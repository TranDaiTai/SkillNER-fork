# create_token_dist_jobs.py (sửa đúng thứ tự)

import json
import collections

# Đọc từ jobs_processed.json (chứ không phải relax db)
with open('./skillNer/data/jobs_processed.json', 'r', encoding='utf-8') as f:
    jobs_db = json.load(f)

def get_dist_new(array):
    words = []
    for val in array:
        for v in val.split(' '):
            words.append(v)
    return dict(collections.Counter(words))

# Chỉ lấy job_cleaned của n-gram jobs (len > 1) - đúng như md gốc
n_grams = [
    jobs_db[key]['job_cleaned']
    for key in jobs_db
    if jobs_db[key]['job_len'] > 1
]

n_gram_dist = get_dist_new(n_grams)

# Save
with open('./skillNer/data/token_dist_job.json', 'w', encoding='utf-8') as f:
    json.dump(n_gram_dist, f, ensure_ascii=False, indent=4)

print("Token dist for jobs created successfully!")