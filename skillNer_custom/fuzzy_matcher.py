import jellyfish

class FuzzyPhraseMatcher:
    '''
    Fuzzy phrase-level matcher dùng để phát hiện CỤM SKILL / JOB TITLE
    bị sai chính tả (typo), ví dụ:
        - "pithon developer"  -> "python developer"
        - "net ful stack developer" -> ".net full stack developer"

    TRIẾT LÝ THIẾT KẾ
    -----------------
    - Chỉ match PHRASE (skill_len > 1), không match token đơn lẻ
    - Chạy SAU full_match / abv_match
    - Khi match thành công:
        + Trả về kết quả fuzzy
        + ĐÁNH DẤU token trong text_obj là không còn matchable
          để các matcher cấp thấp hơn (lowSurf, token, uni)
          KHÔNG được ăn mất phrase-level match

    - Không dùng occupied mask / utils bên ngoài
    - Mutate trực tiếp text_obj (phù hợp với thiết kế SkillNER gốc)
    '''

    def __init__(self, skills_db, min_sim=0.92):
        '''
        Parameters
        ----------
        skills_db : dict
            Skill database, mỗi skill chứa high_surface_forms['full']
        min_sim : float
            Ngưỡng Jaro-Winkler similarity để coi là fuzzy match hợp lệ
            (thường nằm trong khoảng 0.90 – 0.95)
        '''
        self.min_sim = min_sim

        # Map: skill_id -> full skill phrase (lowercase)
        self.skill_phrases = {
            skill_id: skill["high_surfce_forms"]["full"].lower()
            for skill_id, skill in skills_db.items()
        }

    def _span_is_matchable(self, text_obj, start, end):
        '''
        Kiểm tra xem toàn bộ token trong span [start, end)
        có còn matchable hay không.

        Một span chỉ được fuzzy match nếu:
        - TẤT CẢ token trong span đều chưa bị matcher khác chiếm
          (is_matchable == True)

        Điều này đảm bảo:
        - fuzzy không override full / abv match
        - fuzzy không chồng chéo các phrase đã được nhận diện
        '''
        for i in range(start, end):
            if not text_obj[i].is_matchable:
                return False
        return True

    def match(self, text_obj):
        '''
        Thực hiện fuzzy phrase matching trên text_obj.

        Quy trình:
        ----------
        1. Duyệt từng skill phrase trong skill DB
        2. Trượt cửa sổ token với độ dài = skill_len
        3. Chỉ xét span còn matchable
        4. So sánh span_text với skill_phrase bằng Jaro-Winkler
        5. Nếu similarity >= min_sim:
            - Ghi nhận fuzzy match
            - Đánh dấu toàn bộ token trong span là is_matchable = False

        Returns
        -------
        list[dict]
            Danh sách fuzzy phrase matches, mỗi phần tử có dạng:
            {
                'skill_id': '<skill_id>_fuzzy',
                'doc_node_id': [token indices],
                'doc_node_value': 'span text',
                'type': 'fuzzy',
                'score': <similarity score>
            }
        '''
        matches = []
        tokens = [str(tok).lower() for tok in text_obj]
        text_len = len(tokens)

        for skill_id, skill_phrase in self.skill_phrases.items():
            skill_tokens = skill_phrase.split()
            skill_len = len(skill_tokens)

            # Chỉ fuzzy phrase, bỏ uni-gram
            if skill_len <= 1:
                continue

            for i in range(text_len - skill_len + 1):
                j = i + skill_len

                # Skip nếu span đã bị matcher khác chiếm
                if not self._span_is_matchable(text_obj, i, j):
                    continue

                span_text = " ".join(tokens[i:j])

                sim = jellyfish.jaro_winkler_similarity(
                    span_text, skill_phrase
                )

                if sim >= self.min_sim:
                    matches.append({
                        "skill_id": f"{skill_id}_fuzzy",
                        "doc_node_id": list(range(i, j)),
                        "doc_node_value": span_text,
                        "type": "fuzzy",
                        "score": round(sim, 3)
                    })

                    # Đánh dấu token đã được dùng
                    for k in range(i, j):
                        text_obj[k].is_matchable = False

        return matches
