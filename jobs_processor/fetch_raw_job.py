# fetch_raw_job.py
# ============
# Script chỉ fetch raw job titles từ Lightcast Titles API
# Lưu thành raw_jobs.json (dễ debug nếu cần)
# ============

import requests
import json

# === THAY ĐỔI Ở ĐÂY: Dán client_id và client_secret MỚI của bạn (sau khi đăng ký) ===
# Đăng ký miễn phí tại: https://lightcast.io/open-skills/access
client_id = "5f379hywuvh7fvan"
client_secret = "hfCkXQEy"
scope = "emsi_open"  # hoặc "lightcast_open_free" nếu hướng dẫn yêu cầu

auth_endpoint = "https://auth.emsicloud.com/connect/token"
payload = f"client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials&scope={scope}"
headers = {'content-type': 'application/x-www-form-urlencoded'}

response = requests.post(auth_endpoint, data=payload, headers=headers)
if response.status_code != 200:
    raise Exception(f"Lỗi authentication: {response.status_code} - {response.text}")

access_token = response.json()['access_token']

# Fetch job titles
titles_endpoint = "https://emsiservices.com/titles/versions/latest/titles"
headers = {'authorization': f"Bearer {access_token}"}

response = requests.get(titles_endpoint, headers=headers)
if response.status_code != 200:
    raise Exception(f"Lỗi fetch titles: {response.status_code} - {response.text}")

data = response.json()['data']

# Lưu raw data
raw_output = './skillNer/data/raw_jobs.json'
with open(raw_output, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Đã lưu raw data vào: {raw_output}")