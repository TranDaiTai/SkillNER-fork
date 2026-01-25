from rapidfuzz.distance import JaroWinkler


class FuzzyPhraseMatcher:
    '''
    Fuzzy phrase-level matcher để bắt typo trong CỤM SKILL / JOB TITLE.

    TRIẾT LÝ
    --------
    - Chỉ fuzzy PHRASE (len > 1)
    - Fuzzy = sửa typo, KHÔNG phải semantic match
    - Không cho mở rộng / nuốt token
    - Có token-level gate để diệt false positive
    - Reject sớm (cheap gate → expensive gate)
    - Mutate trực tiếp text_obj (đúng thiết kế SkillNER)
    '''

    def __init__(
        self,
        skills_db,
        min_phrase_sim=0.92,
        min_token_sim=0.80
    ):
        self.min_phrase_sim = min_phrase_sim
        self.min_token_sim = min_token_sim
        self.skill_db = skills_db

        # 🔥 CACHE SKILL DATA (tối ưu quan trọng)
        self.skill_cache = {
            skill_id: {
                "tokens": skill["high_surfce_forms"]["full"].lower().split(),
                "phrase": skill["high_surfce_forms"]["full"].lower(),
                "len": len(skill["high_surfce_forms"]["full"].split())
            }
            for skill_id, skill in skills_db.items()
        }

    def _span_is_matchable(self, text_obj, start, end):
        '''
        Span chỉ được fuzzy nếu toàn bộ token còn matchable
        '''
        for i in range(start, end):
            if not text_obj[i].is_matchable:
                return False
        return True

    def _token_level_pass(self, span_tokens, skill_tokens):
        '''
        Token-level gate (STRICT):
        MỖI token trong span phải đủ giống token tương ứng trong skill
        '''
        for a, b in zip(span_tokens, skill_tokens):
            if JaroWinkler.similarity(a, b) < self.min_token_sim:
                return False
        return True

    def match(self, text_obj):
        '''
        Quy trình match (theo thứ tự tối ưu):

        1. Span còn matchable?
        2. Length gate (rẻ)
        3. First-token cheap fuzzy gate
        4. Phrase-level fuzzy
        5. Token-level strict gate
        '''
        matches = []
        tokens = [str(tok).lower() for tok in text_obj]
        text_len = len(tokens)

        for skill_id, info in self.skill_cache.items():
            skill_tokens = info["tokens"]
            skill_phrase = info["phrase"]
            skill_len = info["len"]

            # Chỉ fuzzy phrase
            if skill_len <= 1:
                continue

            for i in range(text_len - skill_len + 1):
                j = i + skill_len

                # 1️⃣ Span đã bị matcher khác chiếm
                if not self._span_is_matchable(text_obj, i, j):
                    continue

                span_tokens = tokens[i:j]
                span_text = " ".join(span_tokens)

                # 2️⃣ Length gate (diệt punctuation / semantic drift)
                if abs(len(span_text) - len(skill_phrase)) > 3:
                    continue

                # 3️⃣ Cheap first-token gate
                if JaroWinkler.similarity(
                    span_tokens[0], skill_tokens[0]
                ) < 0.7:
                    continue

                # 4️⃣ Phrase-level fuzzy
                phrase_sim = JaroWinkler.similarity(
                    span_text, skill_phrase
                )
                if phrase_sim < self.min_phrase_sim:
                    continue

                # 5️⃣ Token-level strict gate (quan trọng nhất)
                if not self._token_level_pass(span_tokens, skill_tokens):
                    continue

                # ✅ MATCH
                matches.append({
                    "skill_id": skill_id,
                    "doc_node_id": list(range(i, j)),
                    "doc_node_value": span_text,
                    "type": "fuzzy",
                    "score": round(phrase_sim, 3)
                })

                # Đánh dấu token đã dùng
                for k in range(i, j):
                    text_obj[k].is_matchable = False

        return matches
