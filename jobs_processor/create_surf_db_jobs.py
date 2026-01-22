# create_surf_db_jobs.py (final version - cleaned & fixed)
# ============
# Tạo job_db_relax_20.json từ jobs_processed.json + token_dist_job.json
# Tương tự skill_db_relax_20.json nhưng dành cho job titles
# ============

import re
import collections
import json
from pathlib import Path

# Paths
PROCESSED_PATH = './skillNer/data/jobs_processed.json'
DIST_PATH      = './skillNer/data/token_dist_job.json'
OUTPUT_PATH    = './skillNer/data/job_db_relax_20.json'

RELAX_PARAM = 0.2  # ngưỡng cho token đầu (thường noisy với job → có thể comment)

def load_json(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Không tìm thấy: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

job_DB = load_json(PROCESSED_PATH)
dist   = load_json(DIST_PATH)

new_job_db = {}

for key, job in job_DB.items():
    high_forms = {}
    low_forms  = []
    match_on_tokens = False

    job_len     = job.get('job_len', 1)
    job_name    = job.get('job_name', '')
    job_type    = job.get('job_type', '')
    clean_name  = job.get('job_cleaned', '')
    lemmed      = job.get('job_lemmed', '')
    stemmed     = job.get('job_stemmed', '')
    abbrev      = job.get('abbreviation', '')
    match_stem  = job.get('match_on_stemmed', False)

    if abbrev:
        high_forms['abv'] = abbrev

    if job_len == 1:
        high_forms['full'] = clean_name
        if match_stem:
            low_forms.append(stemmed)

    elif job_len == 2:
        high_forms['full'] = lemmed
        stemmed_tokens = stemmed.split()
        if stemmed_tokens:
            low_forms.append(stemmed)
            low_forms.append(' '.join(stemmed_tokens[::-1]))

            last  = stemmed_tokens[-1]
            first = stemmed_tokens[0]

            if dist.get(last, 0) == 1:
                low_forms.append(last)

            # Token đầu thường noisy trong job titles → comment nếu muốn
            if dist.get(first, 0) / dist.get(last, 1) < RELAX_PARAM:
                low_forms.append(first)

    elif job_len > 2:
        high_forms['full'] = lemmed
        match_on_tokens = True

    new_job_db[key] = {
        'job_name': job_name,
        'job_type': job_type,
        'job_len': job_len,
        'high_surfce_forms': high_forms,   # giữ typo như SkillNer gốc
        'low_surface_forms': low_forms,
        'match_on_tokens': match_on_tokens
    }

# === Lọc unique token cho bigram ===
unique_tokens_bigram = []
for entry in new_job_db.values():
    if entry['job_len'] == 2:
        uniques = [f for f in entry['low_surface_forms'] if ' ' not in f]
        unique_tokens_bigram.extend(uniques)

token_counter = collections.Counter(unique_tokens_bigram)

for entry in new_job_db.values():
    if entry['job_len'] == 2:
        filtered = []
        for form in entry['low_surface_forms']:
            if ' ' in form or token_counter[form] == 1:
                filtered.append(form)
        entry['low_surface_forms'] = filtered

# === Extract viết tắt cho n-gram job (>2) ===
rx = r"\b[A-Z](?:[.&]?[A-Z])+\b"  # CEO, CTO, CFO, VP, ...

def remove_parentheses(text: str) -> str:
    return re.sub(r"[\(\[].*?[\)\]]", "", text).strip()

all_abbrevs = []
for job in job_DB.values():
    if job.get('job_len', 0) > 1:
        clean_no_par = remove_parentheses(job['job_name'])
        abvs = re.findall(rx, clean_no_par)
        all_abbrevs.extend(abvs)

abv_counter = collections.Counter(all_abbrevs)

for entry in new_job_db.values():
    if entry['job_len'] > 2:
        clean_no_par = remove_parentheses(entry['job_name'])
        candidates = re.findall(rx, clean_no_par)
        for cand in candidates:
            if abv_counter[cand] == 1 and cand not in entry['low_surface_forms']:
                entry['low_surface_forms'].append(cand)

# === Save ===
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(new_job_db, f, ensure_ascii=False, indent=4)

# Debug info
total = len(new_job_db)
with_abv = sum(1 for e in new_job_db.values() if e['high_surfce_forms'].get('abv'))
with_low = sum(1 for e in new_job_db.values() if e['low_surface_forms'])
match_tok = sum(1 for e in new_job_db.values() if e['match_on_tokens'])

print("\nHOÀN THÀNH!")
print(f"- Tổng job titles: {total}")
print(f"- Có abbreviation (high): {with_abv}")
print(f"- Có low surface forms: {with_low}")
print(f"- match_on_tokens (len >2): {match_tok}")
print(f"File lưu tại: {OUTPUT_PATH}")