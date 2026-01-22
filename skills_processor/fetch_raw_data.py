# native packs
import requests
import json
from typing import Optional

# installed packs
import pandas as pd


class EmsiSkillsFetcher:
    """
    Class để fetch danh sách skills từ Emsi API (Lightcast Open Skills).
    
    Sử dụng:
    fetcher = EmsiSkillsFetcher(client_id="your_id", client_secret="your_secret")
    skills_data = fetcher.fetch_data_list()
    fetcher.save_to_json(skills_data, "raw_skills.json")
    """
    
    def __init__(
        self,
        client_id: str= "5f379hywuvh7fvan" ,
        client_secret: str= "hfCkXQEy",
        scope: str = "emsi_open",
        auth_endpoint: str = "https://auth.emsicloud.com/connect/token",
        skills_endpoint: str = "https://emsiservices.com/skills/versions/latest/skills"
    ):
        """
        Khởi tạo fetcher với credentials và endpoints.
        
        Parameters:
        - client_id: Client ID từ email invite của Emsi
        - client_secret: Client Secret từ email invite
        - scope: Scope của token (mặc định "emsi_open")
        - auth_endpoint: URL lấy token
        - skills_endpoint: URL lấy danh sách skills
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.auth_endpoint = auth_endpoint
        self.skills_endpoint = skills_endpoint
        
        # Cache access token để không phải lấy lại nhiều lần
        self._access_token: Optional[str] = None

    def _get_access_token(self) -> str:
        """
        Lấy access token từ auth endpoint.
        Cache token để tái sử dụng.
        """
        if self._access_token:
            return self._access_token

        payload = (
            f"client_id={self.client_id}"
            f"&client_secret={self.client_secret}"
            f"&grant_type=client_credentials"
            f"&scope={self.scope}"
        )
        
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(
                self.auth_endpoint,
                data=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()  # Raise nếu status != 200
            token_data = response.json()
            self._access_token = token_data['access_token']
            return self._access_token
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi khi lấy access token: {str(e)}")
        except KeyError:
            raise ValueError("Không tìm thấy 'access_token' trong response từ auth endpoint")

    def fetch_data_list(self) -> list:
        """
        Fetch danh sách tất cả skills từ Emsi API.
        
        Returns:
            list: Danh sách skills (response['data'])
        
        Raises:
            ConnectionError: Lỗi mạng hoặc API
            ValueError: Response không đúng format
        """
        token = self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }

        try:
            response = requests.get(
                self.skills_endpoint,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                raise ValueError("Response không chứa key 'data'")
                
            return data['data']
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Lỗi khi fetch skills: {str(e)}")
        except ValueError as ve:
            raise ValueError(f"Response không đúng format: {str(ve)}")

    def save_to_json(self, data: list, filepath: str = "./skillNer/data/raw_skillss.json"):
        """
        Lưu dữ liệu skills vào file JSON.
        
        Parameters:
        - data: list skills từ fetch_data_list()
        - filepath: Đường dẫn lưu file (mặc định raw_skillss.json)
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Đã lưu raw data vào: {filepath}")
        except IOError as e:
            print(f"Lỗi khi lưu file: {str(e)}")

