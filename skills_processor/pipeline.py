# pipeline_runner.py
# ============
# Class chạy toàn bộ pipeline skill: Fetch → Process → Token Dist → Relax DB
# Từ raw API → skills_processed.json → token_dist_skill.json → skill_db_relax_20.json
# Đã hỗ trợ cấu hình endpoint tùy chỉnh cho Emsi API
# Print theo biến để dễ bảo trì
# ============

import json
from pathlib import Path
from typing import Dict, Optional

# Import các class từ các file tương ứng
from skills_processor.fetch_raw_data import EmsiSkillsFetcher
from skills_processor.processed import SkillsProcessor
from skills_processor.create_token_dist import TokenDistGenerator
from skills_processor.create_surf_db import SkillRelaxDBGenerator


class PipelineRunner:
    """
    Class chạy toàn bộ pipeline xử lý skill từ raw đến relax DB.
    
    Các bước:
    1. Fetch raw từ Emsi API (nếu cần) - hỗ trợ endpoint tùy chỉnh
    2. Process raw → skills_processed.json
    3. Tạo token_dist_skill.json
    4. Tạo skill_db_relax_20.json
    """

    def __init__(
        self,
        client_id: str = "5f379hywuvh7fvan",
        client_secret: str = "hfCkXQEy",
        auth_endpoint: str = "https://auth.emsicloud.com/connect/token",
        skills_endpoint: str = "https://emsiservices.com/skills/versions/latest/skills",
        raw_file: str = "./skillNer/data/raw_skillss.json",
        processed_file: str = "./skillNer/data/skills_processed.json",
        token_dist_file: str = "./skillNer/data/token_dist_skill.json",
        relax_db_file: str = "./skillNer/data/skill_db_relax_20.json"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_endpoint = auth_endpoint
        self.skills_endpoint = skills_endpoint
        
        self.raw_path = Path(raw_file).resolve()
        self.processed_path = Path(processed_file).resolve()
        self.token_dist_path = Path(token_dist_file).resolve()
        self.relax_db_path = Path(relax_db_file).resolve()

        # Kiểm tra thư mục data tồn tại
        data_dir = self.raw_path.parent
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            print(f"Đã tạo thư mục data: {data_dir}")

    def _fetch_raw(self, force: bool = False) -> bool:
        """Bước 1: Fetch raw từ Emsi API nếu cần (dùng endpoint tùy chỉnh)"""
        print(f"\n Bước 1: Fetch raw từ API (endpoint: {self.skills_endpoint})")

        if not force and self.raw_path.exists():
            print(f"   → Sử dụng raw data cũ: {self.raw_path}")
            return True

        fetcher = EmsiSkillsFetcher(
            client_id=self.client_id,
            client_secret=self.client_secret,
            auth_endpoint=self.auth_endpoint,
            skills_endpoint=self.skills_endpoint
        )
        try:
            raw_data = fetcher.fetch_skills_list()
            fetcher.save_to_json(raw_data, str(self.raw_path))
            print(f"   → Đã fetch và lưu raw data: {self.raw_path}")
            return True
        except Exception as e:
            print(f"   → Lỗi fetch raw: {str(e)}")
            if self.raw_path.exists():
                print("   → Tiếp tục dùng raw cũ.")
                return True
            else:
                print("   → Không có raw cũ và fetch thất bại. Dừng pipeline.")
                return False

    def _process_raw(self) -> Optional[Dict]:
        """Bước 2: Process raw → processed"""
        print(f"\n Bước 2: Process raw → {self.processed_path.name}")
        processor = SkillsProcessor(
            raw_file=str(self.raw_path),
            output_file=str(self.processed_path)
        )
        try:
            processed_data = processor.process()
            processor.save(processed_data)
            print(f"   → Đã tạo processed file: {self.processed_path} ({len(processed_data)} skills)")
            return processed_data
        except Exception as e:
            print(f"   → Lỗi process: {str(e)}")
            return None

    def _generate_token_dist(self) -> bool:
        """Bước 3: Tạo token_dist_skill.json"""
        print(f"\n Bước 3: Tạo {self.token_dist_path.name}")
        token_gen = TokenDistGenerator(input_dir=str(self.processed_path.parent))
        try:
            token_dist = token_gen.generate_from_file(processed_filename=self.processed_path.name)
            token_gen.save(token_dist, str(self.token_dist_path))
            print(f"   → Đã tạo token dist: {self.token_dist_path}")
            return True
        except Exception as e:
            print(f"   → Lỗi token dist: {str(e)}")
            return False

    def _generate_relax_db(self) -> bool:
        """Bước 4: Tạo skill_db_relax_20.json"""
        print(f"\n Bước 4: Tạo {self.relax_db_path.name}")
        relax_gen = SkillRelaxDBGenerator(
            processed_path=str(self.processed_path),
            token_dist_path=str(self.token_dist_path),
            output_path=str(self.relax_db_path)
        )
        try:
            relaxed_db = relax_gen.generate()
            relax_gen.print_summary(relaxed_db)
            relax_gen.save(relaxed_db)
            print(f"   → Đã tạo relax DB: {self.relax_db_path}")
            return True
        except Exception as e:
            print(f"   → Lỗi relax DB: {str(e)}")
            return False

    def run(self, force_fetch: bool = False):
        """
        Chạy toàn bộ pipeline.
        
        Parameters:
        - force_fetch: Luôn fetch raw mới từ API (bỏ qua raw cũ)
        """
        print("=== PIPELINE  HOÀN CHỈNH - BẮT ĐẦU ===")
        print(f"Force fetch raw: {force_fetch}")
        print(f"Auth endpoint: {self.auth_endpoint}")
        print(f"data endpoint: {self.skills_endpoint}")
        print("-" * 80)

        success = True

        # Bước 1
        if not self._fetch_raw(force=force_fetch):
            success = False

        if success:
            # Bước 2
            processed = self._process_raw()
            success = processed is not None

        if success:
            # Bước 3
            success = self._generate_token_dist()

        if success:
            # Bước 4
            success = self._generate_relax_db()

        if success:
            print("\n=== PIPELINE HOÀN THÀNH - TOÀN BỘ DỮ LIỆU ĐÃ SẴN SÀNG ===")
            print(f"  Raw:          {self.raw_path}")
            print(f"  Processed:    {self.processed_path}")
            print(f"  Token Dist:   {self.token_dist_path}")
            print(f"  Relax DB:     {self.relax_db_path}")
            print("Bạn có thể dùng skill_db_relax_20.json trong SkillExtractor ngay bây giờ!")
        else:
            print("\n=== PIPELINE DỪNG DO LỖI ===")
            print("Kiểm tra lỗi ở bước trên và thử lại.")

