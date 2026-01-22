# create_skillss_processed.py
# ============
# Script xử lý raw_skillss.json thành skillss_processed.json
# Đúng chuẩn như skills_processed.json trong SkillNER
# Sử dụng chính xác Cleaner từ skillNer
# Chỉ thêm logic extract abbreviation
# ============

import json
import spacy
import re
from nltk.stem import PorterStemmer
from skillNer_custom.cleaner import Cleaner

# Load spaCy model
nlp = spacy.load("en_core_web_lg")

# Cleaner giống hệt cách SkillNER xử lý skill name
skills_cleaner = Cleaner(
    to_lowercase=True,
    include_cleaning_functions=[
        "remove_punctuation",  # loại bỏ dấu câu
        "remove_redundant",      
        "remove_extra_space"
    ]
)


def remove_description(text: str) -> str:
    # Loại bỏ mô tả trong ngoặc đơn hoặc ngoặc vuông
    matched = re.sub(r"\s*\([^)]*\)\s*", "", text)
    return matched

# Stemmer
stemmer = PorterStemmer()
def stem_text(text: str) -> str:
    return " ".join([stemmer.stem(word) for word in text.split()])

# Lemmatizer
def lem_text(text: str) -> str:
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])

# === Hàm mới: Extract abbreviation ===
def extract_abbreviation(raw_name: str) -> str:
    """
    Trích xuất viết tắt từ tên skill, ưu tiên:
    1. Phần trong ngoặc đơn ở cuối (nếu là viết tắt uppercase hoặc ngắn gọn)
    2. Viết tắt uppercase ở cuối tên (ví dụ: AWS, SQL, FxCop)
    """
    raw_name = raw_name.strip()
    
    # Case 1: Tìm trong ngoặc đơn cuối cùng (ví dụ: "FxCop Analyzers (FxCop)")
    match_paren = re.search(r'\(([^)]+)\)\s*', raw_name)
    if match_paren:
        candidate = match_paren.group(1).strip()
        # Nếu candidate là viết tắt (toàn uppercase, hoặc ngắn + không khoảng trắng nhiều)
        if (candidate.isupper() or 
            (len(candidate) <= 8 and ' ' not in candidate) or 
            candidate.upper() == candidate):
            return candidate
    
    # Case 2: Tìm viết tắt uppercase ở cuối tên (ngoài ngoặc)
    # Ví dụ: "... (FxCop Analyzers)" nhưng nếu không có ngoặc thì tìm FxCop
    # match_end = re.search(r'\b([A-Z0-9.-]{2,})\b\s*', raw_name)
    # if match_end:
    #     candidate = match_end.group(1)
    #     # Tránh nhầm với số hoặc từ không phải viết tắt
    #     if candidate.isupper() or '-' in candidate:
    #         return candidate
    
    return ""

# Đọc raw data
raw_file = './skillNer/data/raw_skillss.json'
with open(raw_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Processing
processed_skillss = {}
for item in data:
    skills_id = item['id']
    skills_name_raw = item['name']
    skills_type = item.get('type', {}).get('name', '')
    
    # Clean giống hệt SkillNER
    skills_cleaned = skills_cleaner(remove_description(skills_name_raw))
    if not skills_cleaned.strip():
        continue  # bỏ qua nếu rỗng sau clean
    
    skills_len = len(skills_cleaned.split())
    skills_lemmed = lem_text(skills_cleaned)
    skills_stemmed = stem_text(skills_cleaned)
    
    # Extract abbreviation
    abbrev = extract_abbreviation(skills_name_raw)
    
    processed_skillss[skills_id] = {
        "skill_name": skills_name_raw,
        "skill_type": skills_type,
        "skill_cleaned": skills_cleaned,
        "skill_len": skills_len,
        "skill_lemmed": skills_lemmed,
        "skill_stemmed": skills_stemmed,
        "match_on_stemmed": (skills_len == 1),
        "abbreviation": abbrev
    }

# Lưu file cuối cùng
output_file = './skillNer/data/skills_processed.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(processed_skillss, f, ensure_ascii=False, indent=4)

print(f"\nHOÀN THÀNH! Đã tạo {len(processed_skillss)} skills titles chuẩn SkillNER.")
