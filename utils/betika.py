
import json, os
from dotenv import load_dotenv
import requests

load_dotenv()   
BETIKA_PROFILE_ID = os.getenv("BETIKA_PROFILE_ID")
BETIKA_TOKEN = os.getenv("BETIKA_TOKEN")

class Betika():
    def __init__(self):
        self.base_url = "https://api.betika.com"
        self.live_url = "https://live.betika.com"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }
        self.src = "MOBILE_WEB"
              
    def get_data(self, url):   
        try:
            response = requests.get(url)            
            return response.json()  # Assuming the response is JSON
        
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
        
    def post_data(self, url, payload):
        try:
            # Sending the POST request
            response = requests.post(url, data=json.dumps(payload), headers=self.headers)
            return response.json()
            
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
                
    def login(self, phone, password):
        url = f'{self.base_url}/v1/login'
        payload = {
            "mobile": phone,
            "password": password,
            "src": self.src
        }
        
        response = self.post_data(url, payload)
        print(response)
    
    def get_balance(self):
        url = f'{self.base_url}/v1/balance'
        payload = {
            "profile_id": str(BETIKA_PROFILE_ID),
            "token": BETIKA_TOKEN,
            "src": self.src
        }

        response = self.post_data(url, payload)
        print(response)

        data = response.get('data')
        return data.get('balance'), data.get('bonus')        
      
    def get_events(self, limit, page, live=False):
        url = f'{self.live_url if live else self.base_url}/v1/uo/matches?sport_id=14&sort_id=2&esports=false&is_srl=false&limit={limit}&page={page}'
        response = self.get_data(url)
        data = response.get('data')
        events = []

        for datum in data:
            home = datum.get('home_team')
            away = datum.get('away_team')
            parent_match_id = datum.get('parent_match_id')

            event = {
                "home_team": home,
                "away_team": away,
                "parent_match_id": parent_match_id
            }
            events.append(event)

        total = int(response.get('meta').get('total'))
        current_page = int(response.get('meta').get('current_page'))
        page = current_page + 1

        return total, page, events
     
    def place_bet(self, betslips, total_odd, stake):
        url = f'{self.base_url}/v2/bet'
        payload = {
            "profile_id": str(BETIKA_PROFILE_ID),
            "stake": str(stake),
            "total_odd": str(total_odd),
            "betslip": betslips,
            "token": BETIKA_TOKEN,
            "src": self.src
        }

        response = self.post_data(url, payload)
        print(response)

    def get_matches(self, limit, page, live=False):
        url = f'{self.live_url if live else self.base_url}/v1/uo/matches?sport_id=14&sort_id=1&esports=false&is_srl=false&limit={limit}&page={page}'
        response = self.get_data(url)
        total = int(response.get('meta').get('total'))
        current_page = int(response.get('meta').get('current_page'))
        page = current_page + 1

        return total, page, response.get('data')
    
    def get_match_details(self, parent_match_id, live=False):
        url = f'{self.live_url if live else self.base_url}/v1/uo/match?parent_match_id={parent_match_id}'
        response = self.get_data(url)
        return response 
    
    def get_match_ids(self, live=False):   
        limit = 100
        total = limit + 1
        page = 1
        matches_ids = set()
        while limit*page < total:
            total, page, matches = self.get_matches(limit, page, live)
        
        for match in matches:
            parent_match_id = match.get('parent_match_id')
            match_time = match.get('match_time')
            matches_ids.add((parent_match_id, match_time))
        
        return matches_ids 

    