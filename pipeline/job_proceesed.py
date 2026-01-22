from skills_processor.pipeline import PipelineRunner
# Ví dụ chạy pipeline
if __name__ == "__main__":
    runner = PipelineRunner(
        client_id="5f379hywuvh7fvan",
        client_secret="hfCkXQEy",
        # Cấu hình endpoint tùy chỉnh (nếu cần)
        auth_endpoint="https://auth.emsicloud.com/connect/token",
        skills_endpoint="https://emsiservices.com/titles/versions/latest/titles",   
        raw_file= "./skillNer/data/raw_jobs.json",
        processed_file =  "./skillNer/data/jobs_processed.json",
        token_dist_file = "./skillNer/data/token_dist_job.json",
        relax_db_file = "./skillNer/data/job_db_relax_20.json"
    )
    
    # Chạy với force_fetch=True để lấy dữ liệu mới nhất từ API
    runner.run(force_fetch=False)