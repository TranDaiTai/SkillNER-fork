# skills_processor.py 
# ============
# Class xử lý raw_skillss.json thành skills_processed.json
# Đúng chuẩn như skills_processed.json trong SkillNER
# Sử dụng Cleaner từ skillNer_custom, thêm extract abbreviation
# ============

import json
import spacy
import re
from typing import Dict, Optional
from pathlib import Path
from nltk.stem import PorterStemmer
from skillNer_custom.cleaner import Cleaner


class SkillsProcessor:
    """
    Class xử lý dữ liệu raw skills (raw_skillss.json) thành định dạng processed
    (skills_processed.json) theo chuẩn SkillNER.
    
    Bao gồm: cleaning, stemming, lemmatization, extract abbreviation.
    
    Ví dụ sử dụng:
    processor = SkillsProcessor()
    processed = processor.process()
    processor.save(processed, "skills_processed.json")
    """

    def __init__(
        self,
        raw_file: str = "./skillNer/data/raw_skillss.json",
        output_file: str = "./skillNer/data/skills_processed.json",
        spacy_model: str = "en_core_web_lg"
    ):
        """
        Khởi tạo processor.
        
        Parameters:
        - raw_file: Đường dẫn file raw_skillss.json
        - output_file: Đường dẫn lưu file output
        - spacy_model: Model spaCy để lemmatize (mặc định en_core_web_lg)
        """
        self.raw_path = Path(raw_file).resolve()
        self.output_path = Path(output_file).resolve()
        
        if not self.raw_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file raw: {self.raw_path}")

        # Load spaCy
        print("Đang load spaCy model...")
        self.nlp = spacy.load(spacy_model)

        # Cleaner chuẩn SkillNER
        self.skills_cleaner = Cleaner(
            to_lowercase=True,
            include_cleaning_functions=[
                "remove_punctuation",
                "remove_redundant",
                "remove_extra_space"
            ]
        )

        # Stemmer
        self.stemmer = PorterStemmer()

    def remove_description(self, text: str) -> str:
        """Loại bỏ mô tả trong ngoặc đơn hoặc ngoặc vuông"""
        return re.sub(r"\s*\([^)]*\)\s*", "", text).strip()

    def stem_text(self, text: str) -> str:
        """Stem text bằng PorterStemmer"""
        return " ".join([self.stemmer.stem(word) for word in text.split()])

    def lem_text(self, text: str) -> str:
        """Lemmatize text bằng spaCy"""
        doc = self.nlp(text)
        return " ".join([token.lemma_ for token in doc])

    def extract_abbreviation(self, raw_name: str) -> str:
        """
        Trích xuất viết tắt từ tên skill, ưu tiên:
        1. Phần trong ngoặc đơn ở cuối (nếu là viết tắt uppercase hoặc ngắn gọn)
        2. Viết tắt uppercase ở cuối tên
        """
        raw_name = raw_name.strip()
        
        # Case 1: Tìm trong ngoặc đơn cuối cùng
        match_paren = re.search(r'\(([^)]+)\)\s*$', raw_name)
        if match_paren:
            candidate = match_paren.group(1).strip()
            if (candidate.isupper() or 
                (len(candidate) <= 8 and ' ' not in candidate) or 
                candidate.upper() == candidate):
                return candidate
        
        # Case 2: Tìm viết tắt uppercase ở cuối tên (ngoài ngoặc)
        # match_end = re.search(r'\b([A-Z0-9.-]{2,})\b\s*$', raw_name)
        # if match_end:
        #     candidate = match_end.group(1)
        #     if candidate.isupper() or '-' in candidate:
        #         return candidate
        
        return ""

    def process(self) -> Dict[str, Dict]:
        """
        Xử lý toàn bộ raw data thành processed dict.
        
        Returns:
            Dict: {skill_id: {skill_name, skill_type, ...}}
        """
        print("Đang đọc raw data...")
        with open(self.raw_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed_skills = {}
        skipped_count = 0

        print("Đang xử lý từng skill...")
        for item in data:
            skill_id = item['id']
            skill_name_raw = item['name']
            skill_type = item.get('type', {}).get('name', '')

            # Loại bỏ description trước khi clean
            cleaned_input = self.remove_description(skill_name_raw)
            
            # Clean giống SkillNER
            skill_cleaned = self.skills_cleaner(cleaned_input)
            if not skill_cleaned.strip():
                skipped_count += 1
                continue  # bỏ qua nếu rỗng sau clean

            skill_len = len(skill_cleaned.split())
            skill_lemmed = self.lem_text(skill_cleaned)
            skill_stemmed = self.stem_text(skill_cleaned)
            abbrev = self.extract_abbreviation(skill_name_raw)

            processed_skills[skill_id] = {
                "skill_name": skill_name_raw,
                "skill_type": skill_type,
                "skill_cleaned": skill_cleaned,
                "skill_len": skill_len,
                "skill_lemmed": skill_lemmed,
                "skill_stemmed": skill_stemmed,
                "match_on_stemmed": (skill_len == 1),
                "abbreviation": abbrev
            }

        print(f"Đã bỏ qua {skipped_count} skill rỗng sau clean.")
        return processed_skills

    def save(self, processed_data: Dict, output_path: Optional[str] = None):
        """
        Lưu processed skills vào file JSON.
        
        Parameters:
        - processed_data: dict đã xử lý
        - output_path: Đường dẫn lưu (mặc định dùng trong __init__)
        """
        if output_path:
            save_path = Path(output_path).resolve()
        else:
            save_path = self.output_path

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=4)
            print(f"File lưu tại: {save_path}")
        except IOError as e:
            print(f"Lỗi khi lưu file: {str(e)}")

