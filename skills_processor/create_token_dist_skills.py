# create_token_dist_skills.py (sửa đúng thứ tự)

import json
import collections

# Đọc từ skills_processed.json (chứ không phải relax db)
with open('./skillNer/data/skills_processed.json', 'r', encoding='utf-8') as f:
    skills_db = json.load(f)

def get_dist_new(array):
    words = []
    for val in array:
        for v in val.split(' '):
            words.append(v)
    return dict(collections.Counter(words))

# Chỉ lấy skill_cleaned của n-gram skills (len > 1) - đúng như md gốc
n_grams = [
    skills_db[key]['skills_cleaned']
    for key in skills_db
    if skills_db[key]['skills_len'] > 1
]

n_gram_dist = get_dist_new(n_grams)

# Save
with open('./skillNer/data/token_dist_skill.json', 'w', encoding='utf-8') as f:
    json.dump(n_gram_dist, f, ensure_ascii=False, indent=4)

print("Token dist for skills created successfully!")