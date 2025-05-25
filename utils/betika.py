
import cloudscraper, json, os
from dotenv import load_dotenv
import requests

load_dotenv()   

class Betika():
    def __init__(self):
        self.base_url = "https://api.betika.com"
        self.live_url = "https://live.betika.com"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime/7.44.0",
            "Cache-Control": "no-cache",
            "Host": "api.betika.com"
        }
        self.src = "MOBILE_WEB"
        self.profile_id = None
        self.balance = 0.0
        self.bonus = 0.0
        self.token = None
              
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
        
        # Create a cloudscraper session
        scraper = cloudscraper.create_scraper()

        try:
            response = scraper.post(url, json=payload, headers=self.headers)
            if "application/json" in response.headers.get("Content-Type", "").lower():
                response_json = response.json()
                if response_json:
                    self.profile_id = response_json.get('data').get('user').get('id')
                    self.balance = float(response_json.get('data').get('user').get('balance'))
                    self.bonus = float(response_json.get('data').get('user').get('bonus'))
                    self.token = response_json.get('token')                
            else:
                print("Response is not JSON. Likely an HTML error page.")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"JSON Parsing Error: {e}")
    
    def get_balance(self):
        url = f'{self.base_url}/v1/balance'
        payload = {
            "profile_id": str(self.profile_id),
            "token": self.token,
            "src": self.src
        }

        response = self.post_data(url, payload)
        print(response)

        data = response.get('data')
        if data:
            return data.get('balance'), data.get('bonus') 
        else:
            return 0, 0
      
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
            "betslip": betslips,
            "profile_id": str(self.profile_id),
            "src": self.src,
            "stake": str(stake),
            "token": self.token,
            "total_odd": str(total_odd),
        }

        response = self.post_data(url, payload)
        print(response)
     
    def share_bet(self, betslips):
        url = f'{self.base_url}/v2/share/encode'
        payload = {
            "betslip": betslips,
            "product_type": "PREMATCH",
            "src": self.src,
            "profile_id": str(self.profile_id),
            "token": self.token
        }
        
        response = self.post_data(url, payload)
        #return response.get("link")
        return response.get("code")

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
    
    def withdraw(self, amount):
        url = f'{self.base_url}/v1/withdraw'
        payload = {
            "amount": amount,
            "app_name": self.src,
            "token": self.token
        }

        response = self.post_data(url, payload)
        print(response)
    

    
