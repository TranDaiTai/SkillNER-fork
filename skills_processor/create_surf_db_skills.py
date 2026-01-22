# generate_skill_db_relax_20.py
# ============
# Script tạo skill_db_relax_20.json từ skills_processed.json + token_dist.json
# Tạo nhiều surface forms (high/low) để matcher linh hoạt hơn
# Dựa sát logic gốc SkillNer, nhưng sạch sẽ + dễ bảo trì hơn
# ============

import re
import collections
import json
from pathlib import Path

# Paths (chuẩn hóa)
PROCESSED_DB_PATH = './skillNer/data/skills_processed.json'
TOKEN_DIST_PATH   = './skillNer/data/token_dist_skill.json'          # sửa tên file nếu bạn dùng token_dist_skill.json
OUTPUT_PATH       = './skillNer/data/skill_db_relax_20.json'

RELAX_PARAM = 0.2  # ngưỡng để quyết định token đầu có unique không (ít dùng)

# Load data
def load_json(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

SKILL_DB = load_json(PROCESSED_DB_PATH)
TOKEN_DIST = load_json(TOKEN_DIST_PATH)

new_skill_db = {}

for skill_id, skill in SKILL_DB.items():
    high_forms = {}
    low_forms = []
    match_on_tokens = False

    skill_len     = skill.get('skill_len', 1)
    skill_name    = skill.get('skill_name', '')
    skill_type    = skill.get('skill_type', '')
    clean_name    = skill.get('skill_cleaned', '')
    lemmed        = skill.get('skill_lemmed', '')
    stemmed       = skill.get('skill_stemmed', '')
    abbrev        = skill.get('abbreviation', '')
    match_stemmed = skill.get('match_on_stemmed', False)

    # High surface forms (độ tin cậy cao)
    if abbrev:
        high_forms['abv'] = abbrev

    if skill_len == 1:
        high_forms['full'] = clean_name
        if match_stemmed:
            low_forms.append(stemmed)

    elif skill_len == 2:
        high_forms['full'] = lemmed

        # Stemmed + đảo ngược
        stemmed_tokens = stemmed.split()
        low_forms.append(stemmed)
        low_forms.append(' '.join(stemmed_tokens[::-1]))

        # Token cuối nếu unique (chỉ xuất hiện 1 lần trong toàn bộ n-gram)
        if stemmed_tokens:
            last_token = stemmed_tokens[-1]
            if TOKEN_DIST.get(last_token, 0) == 1:
                low_forms.append(last_token)

            # Token đầu nếu rất hiếm so với token cuối (ít dùng, có thể bỏ)
            first_token = stemmed_tokens[0]
            if TOKEN_DIST.get(last_token, 1) > 0 and TOKEN_DIST.get(first_token, 0) / TOKEN_DIST.get(last_token, 1) < RELAX_PARAM:
                low_forms.append(first_token)

    elif skill_len > 2:
        high_forms['full'] = lemmed
        match_on_tokens = True  # cho phép match từng token riêng rồi aggregate

    # Lưu entry
    new_skill_db[skill_id] = {
        'skill_name': skill_name,
        'skill_type': skill_type,
        'skill_len': skill_len,
        'high_surfce_forms': high_forms,
        'low_surface_forms': low_forms,
        'match_on_tokens': match_on_tokens
    }

# === Phần lọc low forms cho bigram: chỉ giữ token unique (xuất hiện 1 lần) ===
bigram_unique_tokens = []
for skill_id, entry in new_skill_db.items():
    if entry['skill_len'] == 2:
        for form in entry['low_surface_forms']:
            if ' ' not in form:  # chỉ token đơn
                bigram_unique_tokens.append(form)

token_counter = collections.Counter(bigram_unique_tokens)

# Lọc lại low forms: loại token không unique
for skill_id, entry in new_skill_db.items():
    if entry['skill_len'] == 2:
        filtered_low = []
        for form in entry['low_surface_forms']:
            if ' ' in form:
                filtered_low.append(form)  # giữ nguyên n-gram
            elif token_counter[form] == 1:
                filtered_low.append(form)  # chỉ giữ nếu unique
        entry['low_surface_forms'] = filtered_low

# === Thêm abbreviation từ regex cho n-gram (>2) ===
rx = r"\b[A-Z](?:[&.]?[A-Z])+\b"  # regex tìm viết tắt như AQM, AWS, SQL, FxCop

def extract_abbreviations(text: str) -> list:
    return re.findall(rx, text)

def remove_parentheses(text: str) -> str:
    return re.sub(r"[\(\[].*?[\)\]]", "", text).strip()

all_abbrevs = []
n_gram_skills = [s for s in SKILL_DB.values() if s['skill_len'] > 1]

for skill in n_gram_skills:
    name_clean = remove_parentheses(skill['skill_name'])
    abbrevs = extract_abbreviations(name_clean)
    all_abbrevs.extend(abbrevs)

abbrev_dist = collections.Counter(all_abbrevs)

# Thêm vào low forms nếu unique
for skill_id, entry in new_skill_db.items():
    if entry['skill_len'] > 2:
        name_clean = remove_parentheses(entry['skill_name'])
        candidates = extract_abbreviations(name_clean)
        for cand in candidates:
            if abbrev_dist[cand] == 1:  # unique trong toàn bộ DB
                if cand not in entry['low_surface_forms']:
                    entry['low_surface_forms'].append(cand)

# === Lưu file ===
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(new_skill_db, f, ensure_ascii=False, indent=4)

# === Debug info ===
total_skills = len(new_skill_db)
with_abbrev = sum(1 for v in new_skill_db.values() if v['high_surfce_forms'].get('abv'))
with_low_forms = sum(1 for v in new_skill_db.values() if v['low_surface_forms'])
match_token = sum(1 for v in new_skill_db.values() if v['match_on_tokens'])

print("\nHOÀN THÀNH!")
print(f"- Tổng skills: {total_skills}")
print(f"- Skills có abbreviation (high): {with_abbrev}")
print(f"- Skills có low surface forms: {with_low_forms}")
print(f"- Skills match_on_tokens (len > 2): {match_token}")
print(f"File đã lưu: {OUTPUT_PATH}")