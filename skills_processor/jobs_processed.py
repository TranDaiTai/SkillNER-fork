# create_jobs_processed.py
# ============
# Script xử lý raw_jobs.json thành jobs_processed.json
# Đúng chuẩn như skills_processed.json trong SkillNER
# Sử dụng chính xác Cleaner từ skillNer
# ============

import json
import spacy
from nltk.stem import PorterStemmer

from skillNer.cleaner import Cleaner

# Load spaCy model
nlp = spacy.load("en_core_web_lg")

# Cleaner giống hệt cách SkillNER xử lý skill name
job_cleaner = Cleaner(
    to_lowercase=True,
    include_cleaning_functions=[
        "remove_punctuation",
        "remove_redundant",      # loại bỏ "(programming language)", etc.
        "remove_extra_space"
    ]
)

# Stemmer
stemmer = PorterStemmer()
def stem_text(text: str) -> str:
    return " ".join([stemmer.stem(word) for word in text.split()])

# Lemmatizer
def lem_text(text: str) -> str:
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

# Đọc raw data
raw_file = './skillNer/data/raw_jobs.json'
with open(raw_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Processing
processed_jobs = {}
for item in data:
    job_id = item['id']
    job_name_raw = item['name']
    job_type = item.get('category', {}).get('name', '')

    # Clean giống hệt SkillNER
    job_cleaned = job_cleaner(job_name_raw)

    if not job_cleaned.strip():
        continue  # bỏ qua nếu rỗng sau clean

    job_len = len(job_cleaned.split())
    job_lemmed = lem_text(job_cleaned)
    job_stemmed = stem_text(job_cleaned)

    processed_jobs[job_id] = {
        "job_name": job_name_raw,
        "job_type": job_type,
        "job_cleaned": job_cleaned,
        "job_len": job_len,
        "job_lemmed": job_lemmed,
        "job_stemmed": job_stemmed,
        "match_on_stemmed": (job_len == 1),
        "abbreviation": ""
    }

# Lưu file cuối cùng
output_file = './skillNer/data/jobs_processed.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(processed_jobs, f, ensure_ascii=False, indent=4)

print(f"\nHOÀN THÀNH! Đã tạo {len(processed_jobs)} job titles chuẩn SkillNER.")