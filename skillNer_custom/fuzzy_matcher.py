from collections import defaultdict
from rapidfuzz.distance import JaroWinkler


class FuzzyPhraseMatcher:
    """
    Fuzzy phrase-level matcher để bắt TYPO trong CỤM SKILL / JOB TITLE.

    Triết lý thiết kế (học từ SkillNer):
    ----------------------------------
    - Chỉ fuzzy PHRASE (skill_len >= 2)
    - KHÔNG mở rộng nghĩa (token count phải khớp)
    - Fuzzy = sửa typo, KHÔNG phải semantic match
    - Gate sớm + candidate pruning để đảm bảo hiệu năng
    - Mutate trực tiếp text_obj.is_matchable
    """

    def __init__(
        self,
        skills_db: dict,
        min_phrase_sim: float = 0.92,
        min_token_sim: float = 0.80,
        min_head_sim: float = 0.90,
        max_char_diff: int = 5,
    ):
        self.skills_db = skills_db
        self.min_phrase_sim = min_phrase_sim
        self.min_token_sim = min_token_sim
        self.min_head_sim = min_head_sim
        self.max_char_diff = max_char_diff

        # ===== Precompute & index =====

        # skill_id -> tokens
        self.skill_tokens = {}
        # skill_id -> phrase
        self.skill_phrases = {}
        # first_char -> [skill_id]
        self.skill_index = defaultdict(list)

        for skill_id, skill in skills_db.items():
            phrase = skill["high_surfce_forms"]["full"].lower()
            tokens = phrase.split()

            # ❌ chỉ fuzzy multi-token
            if len(tokens) <= 1:
                continue

            self.skill_tokens[skill_id] = tokens
            self.skill_phrases[skill_id] = phrase

            # index theo ký tự đầu của head token
            first_char = tokens[0][0]
            self.skill_index[first_char].append(skill_id)

    # ==============================
    # Utility gates
    # ==============================

    def _span_is_matchable(self, text_obj, start, end):
        """Span chỉ hợp lệ nếu toàn bộ token còn matchable"""
        for i in range(start, end):
            if not text_obj[i].is_matchable:
                return False
        return True

    def _token_level_pass(self, span_tokens, skill_tokens):
        """
        Token-level gate:
        MỖI token trong span phải đủ giống token tương ứng
        """
        for a, b in zip(span_tokens, skill_tokens):
            if JaroWinkler.similarity(a, b) < self.min_token_sim:
                return False
        return True

    # ==============================
    # Main matcher
    # ==============================

    def match(self, text_obj):
        matches = []

        tokens = [str(tok).lower() for tok in text_obj]
        text_len = len(tokens)

        for i in range(text_len):
            if not text_obj[i].is_matchable:
                continue

            head_token = tokens[i]
            if not head_token:
                continue

            # ===== Candidate pruning theo head-token =====
            candidates = self.skill_index.get(head_token[0], [])
            if not candidates:
                continue

            for skill_id in candidates:
                skill_tokens = self.skill_tokens[skill_id]
                skill_len = len(skill_tokens)
                j = i + skill_len

                if j > text_len:
                    continue

                # span phải còn matchable
                if not self._span_is_matchable(text_obj, i, j):
                    continue

                span_tokens = tokens[i:j]
                span_text = " ".join(span_tokens)
                skill_phrase = self.skill_phrases[skill_id]

                # ===== Gate 1: head-token similarity =====
                if JaroWinkler.similarity(
                    span_tokens[0], skill_tokens[0]
                ) < self.min_head_sim:
                    continue

                # ===== Gate 2: độ dài ký tự =====
                if abs(len(span_text) - len(skill_phrase)) > self.max_char_diff:
                    continue

                # ===== Gate 3: phrase-level similarity =====
                phrase_sim = JaroWinkler.similarity(
                    span_text, skill_phrase
                )
                if phrase_sim < self.min_phrase_sim:
                    continue

                # ===== Gate 4: token-level similarity (QUAN TRỌNG) =====
                if not self._token_level_pass(span_tokens, skill_tokens):
                    continue

                # ===== MATCH =====
                matches.append({
                    "skill_id": f"{skill_id}",
                    "doc_node_id": list(range(i, j)),
                    "doc_node_value": span_text,
                    "type": "fuzzy",
                    "score": round(phrase_sim, 3)
                })

                # khóa token như SkillNer
                for k in range(i, j):
                    text_obj[k].is_matchable = False

        return matches
