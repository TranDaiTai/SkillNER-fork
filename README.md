<p align="center"><img width="50%" src="https://user-images.githubusercontent.com/56308112/128958594-79813e72-b688-4a9a-9267-324f098d4b0c.png" /></p>

[**Live demo**](https://share.streamlit.io/anasaito/skillner_demo/index.py) | [**Documentation**](https://badr-moufad.github.io/SkillNER/get_started.html) | [**Website**](https://skillner.vercel.app/)

----------------------


[![Downloads](https://static.pepy.tech/personalized-badge/skillner?period=month&units=international_system&left_color=blue&right_color=green&left_text=Downloads%20/%20months)](https://pepy.tech/project/skillner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Just looking to test out SkillNer? Check out our [demo](https://anasaito-skillner-demo-index-4fiwi3.streamlit.app/)**.

SkillNer is an NLP module to automatically Extract skills and certifications from unstructured job postings, texts, and applicant's resumes.

Skillner uses [EMSI](https://skills.emsidata.com/) databse (an open source skill database) as a knowldge base linker to prevent skill duplications.



<p align="center"><img width="50%" src="https://user-images.githubusercontent.com/56308112/138768792-a25d25e7-1e43-4a44-aa46-8de9895ffe88.png" /></p>


## Installation

It is easy to get started with **SkillNer** and take advantage of its features.

1. First, install **SkillNer** through the ``pip``

```bash
pip install skillNer
```

2. Next, run the following command to install ``spacy en_core_web_lg ``
which is one of the main plugins of SkillNer. Thanks to its modular nature, you can 
customize SkillNer behavior just by adjusting  | plugin | unplugin modules. Don't worry about these details, we will discuss them in detail in the **upcoming Tutorial section**.

```bash
python -m spacy download en_core_web_lg
```

**Note:** The later installation will take a few seconds before it gets done since ``spacy en_core_web_lg `` is a bit too large (800 MB). Yet, you need to wait only one time.


## Example of usage

With these initial steps being accomplished, let’s dive a bit deeper into skillNer through a worked example.

Let’s say you want to extract skills from the following job posting:

    “You are a Python developer with a solid experience in web development and can manage projects. 
    You quickly adapt to new environments and speak fluently English and French”

### Annotating skills

We start first by importing modules, particularly spacy and SkillExtractor. Note that if you are using skillNer for the first time, it might take a while to download SKILL_DB.

**SKILL_DB** is SkillNer default skills database. It was built upon [EMSI skills database ](https://skills.emsidata.com/).



```python
# imports
import spacy
from spacy.matcher import PhraseMatcher

# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor

# init params of skill extractor
nlp = spacy.load("en_core_web_lg")
# init skill extractor
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

# extract skills from job_description
job_description = """
You are a Python developer with a solid experience in web development
and can manage projects. You quickly adapt to new environments
and speak fluently English and French
"""

annotations = skill_extractor.annotate(job_description)

```



### Exploit annotations

Voilà! Now you can inspect results by rendering the text with the annotated skills.
You can achieve that through the ``.describe`` method. Note that the output of this method is 
literally an HTML document that gets rendered in your notebook.


<p align="center">
    <img src="./screenshots/output-describe.gif" alt="example output skillNer"/>
</p>


Besides, you can use the raw result of the annotations. 
Below is the value of the ``annotations`` variable from the code above.


```python
# output
{
    'text': 'you are a python developer with a solid experience in web development and can manage projects you quickly adapt to new environments and speak fluently english and french',
    'results': {
        'full_matches': [
            {
                'skill_id': 'KS122Z36QK3N5097B5JH', 
                'doc_node_value': 'web development', 
                'score': 1, 'doc_node_id': [10, 11]
            }
        ], '
        ngram_scored': [
            {
                'skill_id': 'KS125LS6N7WP4S6SFTCK', 
                'doc_node_id': [3], 
                'doc_node_value': 'python', 
                'type': 'fullUni', 
                'score': 1, 
                'len': 1
            }, 
        # the other annotated skills
        # ...
        ]
    }
}
```

# Contribute

SkillNer is the first **Open Source** skill extractor. 
Hence it is a tool dedicated to the community and thereby relies on its contribution to evolve.

We did our best to adapt SkillNer for usage and fixed many of its bugs. Therefore, we believe its key features 
make it ready for a diversity of use cases. However, it still has not reached 100% stability. SkillNer needs the assistance of the community to be adapted further
and broaden its usage. 


You can contribute to SkillNer either by

1. Reporting issues. Indeed, you may encounter one while you are using SkillNer. So do not hesitate to mention them in the [issue section of our GitHub repository](https://github.com/AnasAito/SkillNER/issues). Also, you can use the issue as a way to suggest new features to be added.

2. Pushing code to our repository through pull requests. In case you fixed an issue or wanted to extend SkillNer features.


3. A third (friendly and not technical) option to contribute to SkillNer will be soon released. *So, stay tuned...*



Finally, make sure to read carefully [our guidelines](https://badr-moufad.github.io/SkillNER/contribute.html) before contributing. It will specify standards to follow so that we can understand what you want to say.


Besides, it will help you setup SkillNer on your local machine, in case you are willing to push code.


## Useful links

- [Visit our website](https://skillner.vercel.app/) to learn about SkillNer features, how it works, and particularly explore our roadmap
- Get started with SkillNer and get to know its API by visiting the [Documentation](https://badr-moufad.github.io/SkillNER/get_started.html)
- [Test our Demo](https://share.streamlit.io/anasaito/skillner_demo/index.py) to see some of SkillNer capabilities



## Fuzzy Matching (Typo-Tolerant Extraction)

Trong phiên bản mở rộng này, SkillNer bổ sung mô-đun `FuzzyPhraseMatcher` nhằm xử lý các trường hợp sai chính tả, thiếu/k dư ký tự, hoặc cách viết không chuẩn thường gặp trong CV và JD.

### Vấn đề

Các matcher hiện có (`full`, `abv`, `low`, `token`, `uni`) hoạt động rất tốt khi dữ liệu đúng chính tả. Tuy nhiên, chúng dễ bỏ sót các cụm nhiều token (multi-token phrases) khi xuất hiện typo, ví dụ:

- `pithon developer`
- `ful stack`
- `. net ful stack developer`

### Mục tiêu

- Phát hiện cụm skill / job title đa token có lỗi chính tả nhẹ.
- Chỉ sửa typo (non‑semantic), không mở rộng nghĩa.
- Không làm gián đoạn hoặc phá vỡ pipeline matcher hiện tại.

### Nguyên lý hoạt động

`FuzzyPhraseMatcher` hoạt động ở phrase-level với các nguyên tắc sau:

- So sánh span token trong văn bản với full surface form trong surface DB.
- Chỉ áp dụng cho multi-token entries (token_len >= 2) để tránh false positive.
- Sử dụng Jaro–Winkler similarity để đo độ tương đồng giữa span và surface form.
- Áp dụng thêm token-level gate nhằm đảm bảo mỗi token trong span đủ giống token tương ứng trong skill/job gốc.

### Hành vi khi fuzzy match thành công

Khi một fuzzy match hợp lệ được phát hiện:

- Toàn bộ token trong span được gán `token.is_matchable = False` để ngăn các matcher yếu hơn (low, token, uni) khớp lại và “ăn mất” cụm đã match.
- Trả về annotation có cấu trúc tương tự `full_match`:

```
{
    "skill_id": "<skill_id>",
    "doc_node_value": "<span text>",
    "doc_node_id": [<token indices>],
    "type": "fuzzy",
    "score": <jaro_winkler_similarity>
}
```

Trong đó `score` biểu thị mức độ tương đồng fuzzy giữa span và surface form gốc.

### Lợi ích

- Bắt được skill / job title có typo hoặc cách viết không chuẩn trong CV/JD.
- Giảm đáng kể false negative ở cấp phrase.
- Giữ nguyên thứ tự matcher hiện tại và tránh xung đột span bằng cơ chế khoá token (`is_matchable`).
- Không ảnh hưởng đến các matcher chính xác cao như `full` hoặc `abv`.

### Gợi ý triển khai trong pipeline

- Thêm `FuzzyPhraseMatcher` như một bước bổ sung.
- Thứ tự khuyến nghị: `full` → `abv` → `fuzzy` → `low` → `token` → `uni`.
- Cho phép cấu hình ngưỡng Jaro–Winkler (ví dụ: `0.88`–`0.92`) tuỳ domain.
- Chỉ áp dụng fuzzy cho surface forms có token length ≥ 2.



## 🔄 Pipeline Xử Lý Skills (Phiên Bản Mới)

Pipeline mới được thiết kế lại theo hướng end-to-end, rõ ràng và dễ bảo trì, cho phép chạy toàn bộ hoặc từng bước riêng lẻ, đồng thời hỗ trợ cấu hình endpoint EMSI linh hoạt.

Tổng quan luồng xử lý

EMSI API
     ↓
`raw_skillss.json`
     ↓
`skills_processed.json`
     ↓
`token_dist_skill.json`
     ↓
`skill_db_relax_20.json`

Pipeline này được điều phối tập trung bởi class `PipelineRunner`.

🧩 Cấu trúc pipeline & các module chính

1️⃣ `pipeline_runner.py` – Orchestrator

Vai trò:

 - Chạy toàn bộ pipeline theo thứ tự chuẩn: Fetch raw skills từ Emsi API → Process raw → Tạo token distribution → Sinh relax skill DB.

Ưu điểm chính:

 - Có thể `force_fetch` hoặc tái sử dụng raw cũ.
 - In log theo từng bước để dễ debug.
 - Cho phép cấu hình: `auth_endpoint`, `skills_endpoint`, đường dẫn output.

Sử dụng:

```python
from pipeline_runner import PipelineRunner

runner = PipelineRunner(
        client_id="YOUR_ID",
        client_secret="YOUR_SECRET"
)

runner.run(force_fetch=False)
```

2️⃣ `fetch_raw_data.py` – Fetch dữ liệu từ Emsi API

`EmsiSkillsFetcher`

Chức năng:

 - Lấy access token từ Emsi.
 - Fetch toàn bộ danh sách skills (Lightcast / EMSI).
 - Cache token để tránh gọi lại nhiều lần.
 - Lưu raw data ra JSON (`data/raw_skillss.json`).

Đặc điểm kỹ thuật:

 - Timeout & error handling rõ ràng.
 - Validate response (kiểm tra key `data`).
 - Endpoint có thể cấu hình mà không sửa code pipeline.

3️⃣ `processed.py` – Chuẩn hoá skill theo chuẩn SkillNER

`SkillsProcessor`

Chức năng:

 - Làm sạch tên skill (Cleaner chuẩn SkillNER).
 - Loại bỏ mô tả trong ngoặc.
 - Lemmatize (spaCy) và stem (PorterStemmer).
 - Trích xuất abbreviation (AWS, SQL, NLP…).

Output: `data/skills_processed.json`

Mỗi skill bao gồm:

```json
{
    "skill_name": "...",
    "skill_type": "...",
    "skill_cleaned": "...",
    "skill_len": 2,
    "skill_lemmed": "...",
    "skill_stemmed": "...",
    "match_on_stemmed": false,
    "abbreviation": "AWS"
}
```

👉 Định dạng tương thích trực tiếp với SkillNER gốc.

4️⃣ `create_token_dist.py` – Token Distribution

`TokenDistGenerator`

Chức năng:

 - Tính tần suất token.
 - Chỉ dùng n-gram (skill_len > 1) để tránh nhiễu.
 - Phục vụ cho logic relax DB (unique token, rare token).

Output: `data/token_dist_skill.json`

Ví dụ:

```json
{
    "data": 2134,
    "learning": 1876,
    "cloud": 912
}
```

5️⃣ `create_surf_db.py` – Sinh Relax Skill DB

`SkillRelaxDBGenerator`

Chức năng chính:

 - Sinh high surface forms: full, abbreviation.
 - Sinh low surface forms: stemmed, đảo token (bigram), token hiếm, abbreviation regex.

Logic theo độ dài skill:

 - Skill length 1: match full + stem
 - Skill length 2: full (lemma) + stem + đảo token
 - Skill length >2: full (lemma) + match_on_tokens

Output cuối cùng: `data/skill_db_relax_20.json`

👉 Đây là file được dùng trực tiếp bởi `SkillExtractor`.

▶️ Chạy pipeline

Chạy toàn bộ pipeline:

```python
runner = PipelineRunner()
runner.run()
```

Luôn fetch raw mới từ API:

```python
runner.run(force_fetch=True)
```

📦 Output sau khi pipeline hoàn tất
```
data/
 ├─ raw_skillss.json
 ├─ skills_processed.json
 ├─ token_dist_skill.json
 └─ skill_db_relax_20.json
```

Bạn có thể dùng trực tiếp `skill_db_relax_20.json` trong:

`SkillExtractor(nlp, SKILL_DB, PhraseMatcher)`

