
import json, requests, time

from utils.betika import Betika
from utils.entities import Match
from utils.postgres_crud import PostgresCRUD

class Helper():   
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()

    def fetch_data(self, url, timeout=10):
        """
        Fetch data from the given URL.

        Args:
            url (str): The URL to fetch data from.
            timeout (int, optional): The timeout for the HTTP request.

        Returns:
            dict or None: The JSON data if successful, otherwise None.
        """
        headers = {
            'User-Agent': 'PostmanRuntime/7.36.3',
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            json_data = response.json()
            if json_data:
                return json_data
            print("Invalid JSON data format")
        else:
            print(f"{response}")

        return None
    
    def post_data(self, url, body, timeout=10):
        """
        Fetch data from the given URL with POST method.

        Args:
            url (str): The URL to fetch data from.
            body (dict): The body of the POST request.
            timeout (int, optional): The timeout for the HTTP request.

        Returns:
            dict or None: The JSON data if successful, otherwise None.
        """

        body_dict = json.loads(body)

        response = requests.post(url, json=body_dict, timeout=timeout)
        return response.json()

    def fetch_matches(self, day, comparator='=', status="AND status IS NOT NULL", limit=12):
        matches = []
        for open_match in self.db.fetch_matches(day, comparator, status, limit):
            match = Match()
            match.kickoff = open_match[1]
            match.home_team = open_match[2]
            match.away_team = open_match[3]
            match.prediction = open_match[4]    
            match.odd = open_match[5]    
            match.home_results = open_match[6] 
            match.status = open_match[7] 
            match.away_results = open_match[8] 
            match.overall_prob = int(open_match[9])   
            match.subtype_id = int(open_match[10])    
            matches.append(match)
                
        return matches
    
    def get_upcoming_match_ids(self):    
        total = 1001
        limit = 1000
        page = 1
        matches_ids = set()
        while limit*page < total:
            total, page, events = self.betika.get_events(limit, page)
            
            for event in events:
                parent_match_id = event.get('parent_match_id')
                matches_ids.add(parent_match_id)
        
        return matches_ids
     
    def auto_bet(self, matches):
        try:
            betslips = []
            composite_betslip = None
            composite_betslips = [] 
            total_odd = 1
            min_odd = 6
            for match in matches:   
                if not any(betslip["parent_match_id"] == match.get("parent_match_id") for betslip in betslips):
                    betslip = {
                        "sub_type_id": match.get("sub_type_id"),
                        "bet_pick": match.get("bet_pick"),
                        "odd_value": match.get("odd"),
                        "outcome_id": match.get("outcome_id"),
                        "sport_id": 14,
                        "special_bet_value": match.get("special_bet_value"),
                        "parent_match_id": match.get("parent_match_id"),
                        "bet_type": 7
                    }
                    betslips.append(betslip)
                    total_odd *= float(betslip.get('odd_value'))                                              
                    composite_betslip = {
                        'total_odd': total_odd,
                        'betslips': betslips
                    }
                    if total_odd >= min_odd:
                        composite_betslips.append(composite_betslip)
                        betslips = []
                        total_odd = 1
                        composite_betslip = None  
                       
            if composite_betslip:
                if len(composite_betslips) ==0 :
                    composite_betslips.append(composite_betslip)
                else:
                    composite_betslips[0]['betslips'].extend(composite_betslip['betslips'])
                    composite_betslips[0]['total_odd'] *= composite_betslip['total_odd'] 
            if len(composite_betslips) > 0:
                balance, bonus = self.betika.get_balance()
                usable = balance + bonus
                stake = int((usable/2)/len(composite_betslips)) 
                stake = int(usable) if stake == 0 else stake
                if stake > 0:
                    for cb in composite_betslips:
                        ttl_odd = cb['total_odd']
                        slips = cb['betslips']
                        print(slips, ttl_odd, stake)
                        self.betika.place_bet(slips, ttl_odd, stake)
                        time.sleep(2)
                        
        except Exception as e:
            print(f"Error in auto_bet: {e}")
    