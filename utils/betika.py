
import json
from dotenv import load_dotenv
import requests

load_dotenv()   

class Betika():
    def __init__(self):
        self.base_url = "https://api.betika.com"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime/7.44.0",
            "Cache-Control": "no-cache",
            "Host": "api.betika.com"
        }
        
        
    def share_bet(self, betslips):
        url = f'{self.base_url}/v2/share/encode'
        payload = {
            "betslip": betslips,
            "product_type": "PREMATCH",
            "profile_id": None,
            "src": "MOBILE_WEB",
            "token": None
        }
        
        try:
            # Sending the POST request
            response = requests.post(url, data=json.dumps(payload), headers=self.headers)
            return response.json().get("code")
            
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
        except Exception as err:
            print(f"Unexpected error: {err}")
            
        return ''
        
