# skill_processed.py
# ============
# Master pipeline cho skill: Fetch → Process → Token Dist → Relax DB
# Chạy toàn bộ từ raw đến skill_db_relax_20.json
# ============

import json
from pathlib import Path
from typing import Dict

from skills_processor.processed import SkillsProcessor                    # class process raw → processed
from skills_processor.create_token_dist import TokenDistGenerator               # class tạo token dist
from skills_processor.create_surf_db import SkillRelaxDBGenerator      # class tạo relax DB
from skills_processor.fetch_raw_data import EmsiSkillsFetcher                   # class fetch API (đổi tên nếu bạn đặt khác)

# Đường dẫn mặc định (thay đổi nếu cần)
RAW_FILE = "./skillNer/data/raw_skillss.json"
PROCESSED_FILE = "./skillNer/data/skills_processed.json"
TOKEN_DIST_FILE = "./skillNer/data/token_dist_skill.json"
RELAX_DB_FILE = "./skillNer/data/skill_db_relax_20.json"


def run_full_skill_pipeline(
    client_id: str = "5f379hywuvh7fvan",
    client_secret: str = "hfCkXQEy",
    force_fetch: bool = False  # True để luôn fetch mới từ API, False để dùng raw cũ nếu có
):
    """
    Chạy toàn bộ pipeline skill:
    1. Fetch raw từ Emsi API (nếu cần)
    2. Process → skills_processed.json
    3. Tạo token_dist_skill.json
    4. Tạo skill_db_relax_20.json
    
    Parameters:
    - client_id, client_secret: Credentials Emsi API
    - force_fetch: Luôn fetch mới từ API (bỏ qua raw cũ)
    """
    print("=== PIPELINE SKILL HOÀN CHỈNH - BẮT ĐẦU ===")
    print(f"Force fetch raw từ API: {force_fetch}")
    print("-" * 80)

    raw_path = Path(RAW_FILE)

    # Bước 1: Fetch raw data (nếu cần)
    if force_fetch or not raw_path.exists():
        print("\nBước 1: Fetch raw skills từ Emsi API...")
        fetcher = EmsiSkillsFetcher(client_id=client_id, client_secret=client_secret)
        try:
            raw_data = fetcher.fetch_data_list()
            fetcher.save_to_json(raw_data, str(raw_path))
            print(f"Đã fetch và lưu raw data: {raw_path}")
        except Exception as e:
            print(f"Lỗi fetch raw: {str(e)}")
            print("→ Dùng raw cũ nếu có hoặc dừng pipeline.")
            if not raw_path.exists():
                raise RuntimeError("Không có raw data và fetch thất bại.")
    else:
        print(f"\nBước 1: Sử dụng raw data cũ: {raw_path}")

    # Bước 2: Process raw → processed
    print("\nBước 2: Process raw → skills_processed.json...")
    processor = SkillsProcessor(raw_file=RAW_FILE, output_file=PROCESSED_FILE)
    try:
        processed_data: Dict = processor.process()
        processor.save(processed_data)
        print(f"Đã tạo processed file: {PROCESSED_FILE} ({len(processed_data)} skills)")
    except Exception as e:
        print(f"Lỗi process: {str(e)}")
        raise

    # Bước 3: Tạo token dist
    print("\nBước 3: Tạo token_dist_skill.json...")
    token_gen = TokenDistGenerator(input_dir="./skillNer/data")
    try:
        token_dist = token_gen.generate_from_file("skills_processed.json")
        token_gen.save(token_dist, "token_dist_skill.json")
        print(f"Đã tạo token dist: {TOKEN_DIST_FILE}")
    except Exception as e:
        print(f"Lỗi token dist: {str(e)}")
        raise

    # Bước 4: Tạo relax DB
    print("\nBước 4: Tạo skill_db_relax_20.json...")
    relax_gen = SkillRelaxDBGenerator(
        processed_path=PROCESSED_FILE,
        token_dist_path=TOKEN_DIST_FILE,
        output_path=RELAX_DB_FILE
    )
    try:
        relaxed_db = relax_gen.generate()
        relax_gen.print_summary(relaxed_db)
        relax_gen.save(relaxed_db)
        print(f"Đã tạo relax DB: {RELAX_DB_FILE}")
    except Exception as e:
        print(f"Lỗi relax DB: {str(e)}")
        raise

    print("\n=== PIPELINE HOÀN THÀNH - TOÀN BỘ SKILL ĐÃ SẴN SÀNG ===")
    print(f"- Raw: {RAW_FILE}")
    print(f"- Processed: {PROCESSED_FILE}")
    print(f"- Token Dist: {TOKEN_DIST_FILE}")
    print(f"- Relax DB: {RELAX_DB_FILE}")
    print("Bạn có thể dùng skill_db_relax_20.json trong SkillExtractor ngay bây giờ!")


if __name__ == "__main__":
    # Chạy pipeline
    # force_fetch=True nếu muốn lấy dữ liệu mới nhất từ API
    run_full_skill_pipeline(
        client_id="5f379hywuvh7fvan",
        client_secret="hfCkXQEy",
        force_fetch=False  # Đổi thành True nếu muốn fetch mới
    )