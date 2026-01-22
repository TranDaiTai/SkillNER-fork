# create_token_dist.py 
# ============
# Class để tính token distribution từ skills_processed.json
# Chỉ lấy token từ skill_cleaned của các skill có len > 1 (n-gram)
# ============

import json
import collections
from pathlib import Path
from typing import Dict, Optional

class TokenDistGenerator:
    """
    Class để tính token distribution (tần suất token) từ file skills_processed.json.
    
    Chỉ đếm token từ skill_cleaned của các skill có skill_len > 1 (n-gram).
    
    Ví dụ sử dụng:
    generator = TokenDistGenerator()
    dist = generator.generate_from_file("skills_processed.json")
    generator.save(dist, "token_dist_skill.json")
    """

    def __init__(self, input_dir: str = "./skillNer/data"):
        """
        Khởi tạo với thư mục input mặc định.
        
        Parameters:
        - input_dir: Thư mục chứa file skills_processed.json (mặc định "./skillNer/data")
        """
        self.input_dir = Path(input_dir).resolve()
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Thư mục không tồn tại: {self.input_dir}")

    def _load_processed_db(self, filename: str = "skills_processed.json") -> Dict:
        """Load file JSON processed (skills_processed.json)"""
        file_path = self.input_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_from_file(
        self,
        processed_filename: str = "skills_processed.json"
    ) -> Dict[str, int]:
        """
        Tính token distribution từ file processed.
        
        Returns:
            Dict[str, int]: {token: count}
        """
        skills_db = self._load_processed_db(processed_filename)
        
        # Lấy danh sách skill_cleaned của n-gram (len > 1)
        n_grams = [
            skills_db[key]['skill_cleaned']
            for key in skills_db
            if skills_db[key].get('skill_len', 0) > 1
        ]
        
        
        # Tính distribution
        all_tokens = []
        for cleaned in n_grams:
            all_tokens.extend(cleaned.split())
        
        token_dist = dict(collections.Counter(all_tokens))
        
        return token_dist

    def save(
        self,
        dist: Dict[str, int],
        output_filename: str = "token_dist_skill.json"
    ):
        """
        Lưu token distribution vào file JSON.
        
        Parameters:
        - dist: dict token distribution
        - output_filename: Tên file output (mặc định token_dist_skill.json)
        """
        output_path = self.input_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dist, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Lỗi khi lưu file: {str(e)}")

