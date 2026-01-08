# create_surf_db_jobs.py (final version)

import re
import collections
import json

with open('./skillNer/data/jobs_processed.json', 'r') as f:
    job_DB = json.load(f)

with open('./skillNer/data/token_dist_job.json', 'r') as f:  # tên file đúng
    dist = json.load(f)

RELAX_PARAM = 0.2
new_job_db = {}

for key in job_DB:
    high_surface_form = {}
    low_surface_form = []
    match_on_tokens = False

    job_len = job_DB[key]['job_len']
    job_name = job_DB[key]['job_name']
    job_type = job_DB[key]['job_type']
    clean_name = job_DB[key]['job_cleaned']
    job_lemmed = job_DB[key]['job_lemmed']
    job_stemmed = job_DB[key]['job_stemmed']
    abv = job_DB[key]['abbreviation']
    uni_match_on_stemmed = job_DB[key]['match_on_stemmed']

    if abv != '':
        high_surface_form['abv'] = abv

    # Unigram
    if job_len == 1:
        high_surface_form['full'] = clean_name
        if uni_match_on_stemmed:
            low_surface_form.append(job_stemmed)

    # Bigram
    if job_len == 2:
        high_surface_form['full'] = job_lemmed
        stemmed_tokens = job_stemmed.split(' ')
        inv_stemmed_tokens = stemmed_tokens[::-1]
        low_surface_form.append(job_stemmed)
        low_surface_form.append(' '.join(inv_stemmed_tokens))

        last = stemmed_tokens[-1]
        start = stemmed_tokens[0]

        if dist.get(last, 0) == 1:
            low_surface_form.append(last)
        # Comment dòng dưới nếu thấy noisy quá
        # if dist.get(start, 0) / dist.get(last, 1) < RELAX_PARAM:
        #     low_surface_form.append(start)

    # N-gram >2
    if job_len > 2:
        high_surface_form['full'] = job_lemmed
        match_on_tokens = True

    new_job_db[key] = {
        'job_name': job_name,
        'job_type': job_type,
        'job_len': job_len,
        'high_surface_forms': high_surface_form,  # sửa typo
        'low_surface_forms': low_surface_form,
        'match_on_tokens': match_on_tokens
    }

# Lọc low_surface_forms cho bigram (giữ unique token thật sự unique)
list_unique = []
for key in new_job_db:
    if new_job_db[key]['job_len'] == 2:
        uniques = [l for l in new_job_db[key]['low_surface_forms'] if len(l.split(' ')) == 1]
        list_unique.extend(uniques)

counter_unique = collections.Counter(list_unique)

for key in new_job_db:
    if new_job_db[key]['job_len'] == 2:
        filtered_low = []
        for l in new_job_db[key]['low_surface_forms']:
            if len(l.split(' ')) == 1:
                if counter_unique[l] == 1:
                    filtered_low.append(l)
            else:
                filtered_low.append(l)
        new_job_db[key]['low_surface_forms'] = filtered_low

# Thêm abbreviation từ parentheses (nếu có, ví dụ CEO (Chief Executive Officer))
def remove_btwn_par(str_):
    return re.sub(r"[$$ \[].*?[ $$\]]", "", str_)

def extract_sub_forms(name):
    return re.findall(r"\b[A-Z](?:[.&]?[A-Z])+\b", name)

subs = []
for item in job_DB.values():
    if item['job_len'] > 1:
        clean_name_no_par = remove_btwn_par(item['job_name'])
        abvs = extract_sub_forms(clean_name_no_par)
        subs.extend(abvs)

abv_counter = collections.Counter(subs)

for key in new_job_db:
    if new_job_db[key]['job_len'] > 2:
        clean_name_no_par = remove_btwn_par(new_job_db[key]['job_name'])
        potential_abvs = extract_sub_forms(clean_name_no_par)
        for a in potential_abvs:
            if abv_counter[a] == 1:
                new_job_db[key]['low_surface_forms'].append(a)

# Save final
with open('./skillNer/data/job_db_relax_20.json', 'w', encoding='utf-8') as f:
    json.dump(new_job_db, f, ensure_ascii=False, indent=4)

print("job_db_relax_20.json created successfully!")