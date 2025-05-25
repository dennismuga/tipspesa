from dotenv import load_dotenv
import os, requests

load_dotenv()   

class TextCortex():
    def __init__(self):
        self.base_url = "https://api.textcortex.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {os.getenv("TEXTCORTEX_API_KEY")}'
        }
    
    def get_response(self, query):
        url = f"{self.base_url}/codes"
        payload = {
            "max_tokens": 2048,
            "mode": "python",
            "model": os.getenv("TEXTCORTEX_MODEL"),
            "n": 1,
            "temperature": None,
            "text": query
        }
        
        try:
            response = requests.request("POST", url, json=payload, headers=self.headers)
            return response.text
        except Exception as e:
            print(e)
            return None