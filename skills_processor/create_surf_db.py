# generate_skill_db_relax.py 
# ============
# Class để tạo skill_db_relax_20.json từ skills_processed.json + token_dist_skill.json
# Tạo nhiều surface forms (high/low) để matcher linh hoạt hơn
# Dựa sát logic gốc SkillNer, nhưng sạch sẽ + dễ bảo trì hơn
# ============

import re
import collections
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class SkillRelaxDBGenerator:
    """
    Class để generate skill_db_relax_20.json với nhiều surface forms (high/low).
    
    Tạo high/low surface forms dựa trên độ dài skill, unique token, và viết tắt regex.
    
    Ví dụ sử dụng:
    generator = SkillRelaxDBGenerator()
    new_db = generator.generate()
    generator.save(new_db, "skill_db_relax_20.json")
    """

    def __init__(
        self,
        processed_path: str = "./skillNer/data/skills_processed.json",
        token_dist_path: str = "./skillNer/data/token_dist_skill.json",
        output_path: str = "./skillNer/data/skill_db_relax_20.json",
        relax_param: float = 0.2
    ):
        """
        Khởi tạo generator với các đường dẫn và tham số.
        
        Parameters:
        - processed_path: Đường dẫn đến skills_processed.json
        - token_dist_path: Đường dẫn đến token_dist_skill.json
        - output_path: Đường dẫn lưu file output
        - relax_param: Ngưỡng để quyết định token đầu có unique không (ít dùng)
        """
        self.processed_path = Path(processed_path).resolve()
        self.token_dist_path = Path(token_dist_path).resolve()
        self.output_path = Path(output_path).resolve()
        self.relax_param = relax_param

        # Kiểm tra file tồn tại
        for p in [self.processed_path, self.token_dist_path]:
            if not p.exists():
                raise FileNotFoundError(f"Không tìm thấy file: {p}")

        self.SKILL_DB: Dict = self._load_json(self.processed_path)
        self.TOKEN_DIST: Dict = self._load_json(self.token_dist_path)

    def _load_json(self, path: Path) -> Dict:
        """Load file JSON an toàn"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate(self) -> Dict[str, Any]:
        """
        Chạy toàn bộ quá trình generate relax DB.
        
        Returns:
            Dict: new_skill_db với các surface forms đã augment
        """
        new_skill_db = {}


        for skill_id, skill in self.SKILL_DB.items():
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
                if stemmed_tokens:
                    low_forms.append(stemmed)
                    low_forms.append(' '.join(stemmed_tokens[::-1]))

                    # Token cuối nếu unique
                    last_token = stemmed_tokens[-1]
                    if self.TOKEN_DIST.get(last_token, 0) == 1:
                        low_forms.append(last_token)

                    # Token đầu nếu rất hiếm so với token cuối (ít dùng, có thể bỏ)
                    first_token = stemmed_tokens[0]
                    if (self.TOKEN_DIST.get(last_token, 1) > 0 and 
                        self.TOKEN_DIST.get(first_token, 0) / self.TOKEN_DIST.get(last_token, 1) < self.relax_param):
                        low_forms.append(first_token)

            elif skill_len > 2:
                high_forms['full'] = lemmed
                match_on_tokens = True

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
        print("Đang lọc unique token cho bigram...")
        bigram_unique_tokens = []
        for entry in new_skill_db.values():
            if entry['skill_len'] == 2:
                for form in entry['low_surface_forms']:
                    if ' ' not in form:  # chỉ token đơn
                        bigram_unique_tokens.append(form)

        token_counter = collections.Counter(bigram_unique_tokens)

        # Lọc lại low forms
        for entry in new_skill_db.values():
            if entry['skill_len'] == 2:
                filtered_low = []
                for form in entry['low_surface_forms']:
                    if ' ' in form or token_counter[form] == 1:
                        filtered_low.append(form)
                entry['low_surface_forms'] = filtered_low

        # === Thêm abbreviation từ regex cho n-gram (>2) ===
        print("Đang extract viết tắt từ tên skill cho n-gram...")
        rx = r"\b[A-Z](?:[&.]?[A-Z])+\b"  # regex tìm viết tắt như AQM, AWS, SQL, FxCop

        def extract_abbreviations(text: str) -> List[str]:
            return re.findall(rx, text)

        def remove_parentheses(text: str) -> str:
            return re.sub(r"[\(\[].*?[\)\]]", "", text).strip()

        all_abbrevs = []
        n_gram_skills = [s for s in self.SKILL_DB.values() if s['skill_len'] > 1]

        for skill in n_gram_skills:
            name_clean = remove_parentheses(skill['skill_name'])
            abbrevs = extract_abbreviations(name_clean)
            all_abbrevs.extend(abbrevs)

        abbrev_dist = collections.Counter(all_abbrevs)

        # Thêm vào low forms nếu unique
        for entry in new_skill_db.values():
            if entry['skill_len'] > 2:
                name_clean = remove_parentheses(entry['skill_name'])
                candidates = extract_abbreviations(name_clean)
                for cand in candidates:
                    if abbrev_dist[cand] == 1 and cand not in entry['low_surface_forms']:
                        entry['low_surface_forms'].append(cand)

        return new_skill_db

    def save(self, db: Dict[str, Any], output_path: Optional[str] = None):
        """
        Lưu new_skill_db vào file JSON.
        
        Parameters:
        - db: dict skill DB đã relax
        - output_path: Đường dẫn lưu (mặc định dùng output_path trong __init__)
        """
        if output_path:
            save_path = Path(output_path).resolve()
        else:
            save_path = self.output_path

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
            print(f"File đã lưu: {save_path}")
        except IOError as e:
            print(f"Lỗi khi lưu file: {str(e)}")

    def print_summary(self, db: Dict[str, Any]):
        """In thông tin debug sau khi generate"""
        total_skills = len(db)
        with_abbrev = sum(1 for v in db.values() if v['high_surfce_forms'].get('abv'))
        with_low_forms = sum(1 for v in db.values() if v['low_surface_forms'])
        match_token = sum(1 for v in db.values() if v['match_on_tokens'])

        print("\nHOÀN THÀNH!")
        print(f"- Tổng skills: {total_skills}")
        print(f"- rows  có abbreviation (high): {with_abbrev}")
        print(f"- rows có low surface forms: {with_low_forms}")
        print(f"- rows match_on_tokens (len > 2): {match_token}")
