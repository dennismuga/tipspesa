
import json, pytz, random, requests, time
from datetime import datetime

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

    def fetch_matches(self, day, comparator='=', status="AND status IS NOT NULL", limit=16):
        matches = []
        for open_match in self.db.fetch_matches(day, comparator, status, limit):
            match = Match()
            match.match_id = open_match[0]
            match.kickoff = open_match[1]
            match.home_team = open_match[2]
            match.away_team = open_match[3]
            match.prediction = open_match[4]    
            match.odd = open_match[5]    
            match.home_results = open_match[6] 
            match.status = open_match[7] 
            match.away_results = open_match[8] 
            match.overall_prob = int(open_match[9])   
            match.sub_type_id = int(open_match[10])  
            match.parent_match_id = open_match[11]
            match.bet_pick = open_match[12]
            match.outcome_id = int(open_match[13])
            match.special_bet_value = open_match[14]
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
            min_odd = 3.0
            for match in sorted(matches, key=lambda x: x['start_time']):   
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
                    if total_odd >= min_odd*1.31: #len(betslips) == min_matches: #total_odd >= min_odd:
                        composite_betslips.append(composite_betslip)
                        betslips = []
                        total_odd = 1
                        composite_betslip = None  
                       
            if len(composite_betslips) > 0:                
                balance, bonus = self.betika.get_balance()
                usable = balance + bonus
                stake = int((usable/len(composite_betslips))/2)
                stake = 1 if (stake == 0 and int(usable)>0) else stake
                if stake > 0:
                    composite_betslips.sort(key=lambda cb: cb['total_odd'], reverse=True)
                    for cb in composite_betslips:
                        ttl_odd = cb['total_odd']
                        slips = cb['betslips']
                        print(slips, ttl_odd, stake)
                        self.betika.place_bet(slips, ttl_odd, stake)
                        time.sleep(2)
                            
        except Exception as e:
            print(f"Error in auto_bet: {e}")
            
    def get_share_code(self, matches):
        link = ''
        # Get current time in Nairobi (EAT, UTC+3)
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        current_time = datetime.now(nairobi_tz)
        try:
            betslips = []
            for match in matches:   
                kickoff_aware = nairobi_tz.localize(match.kickoff)
                if not any(betslip["parent_match_id"] == match.parent_match_id for betslip in betslips) and kickoff_aware > current_time:
                    betslip = {
                        "odd_key": match.bet_pick,
                        "outcome_id": match.outcome_id,
                        "special_bet_value": match.special_bet_value,
                        "parent_match_id": match.parent_match_id,
                        "sub_type_id": match.sub_type_id,
                    }
                    betslips.append(betslip)
                       
            if betslips:
                link = self.betika.share_bet(betslips)

            return link if link else ''              
        except Exception as e:
            print(f"Error in get share code: {e}")
            
            
    def get_code(self):
        # Define the allowed digits
        digits = [1, 2, 5, 6, 8, 9]

        # Generate a 6-digit code
        code = ''.join(str(random.choice(digits)) for _ in range(6))

        print(code)
        return code
    
    
