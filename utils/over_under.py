import concurrent.futures
import time 

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

class OverUnder():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()
    
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
    
    def predict_match(self, parent_match_id):
        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
        match_details = self.betika.get_data(url)
        meta = match_details.get('meta')   
        match_id = meta.get('match_id')     
        home_team = meta.get('home_team')     
        away_team = meta.get('away_team')     
        start_time = meta.get('start_time')   
        bet_pick = None
        overall_prob = 98 
        data = match_details.get('data')
        match = None
        if data:
            for d in data:
                if int(d.get('sub_type_id')) in [18]:   
                    odds = d.get('odds') 
                    last_index = len(odds) - 1
                    i = 0
                    for odd in odds:
                        last_odd = odds[last_index-i]
                        cur_odd_value = float(odd.get('odd_value'))      
                        last_odd_value = float(last_odd.get('odd_value'))  
                        
                        if cur_odd_value >=1.19 and cur_odd_value <= 1.31 and cur_odd_value < last_odd_value and odd.get('odd_key') != 'over 1.5':
                            sub_type_id = int(d.get('sub_type_id'))
                            bet_pick = odd.get('odd_key')    
                            odd_value = cur_odd_value   
                            special_bet_value = odd.get('special_bet_value')      
                            outcome_id = odd.get('outcome_id')
                        
                        elif last_odd_value >=1.19 and last_odd_value <= 1.41 and last_odd_value < cur_odd_value and last_odd.get('odd_key') != 'under 3.5':
                            sub_type_id = int(d.get('sub_type_id'))
                            bet_pick = last_odd.get('odd_key')    
                            odd_value = last_odd_value   
                            special_bet_value = last_odd.get('special_bet_value')      
                            outcome_id = last_odd.get('outcome_id')
                        
                        if i == (last_index-1)/2:
                            break
                        else:
                            i += 1
                        
            if bet_pick:
                match = {
                            'parent_match_id': parent_match_id,
                            'match_id': match_id,
                            'start_time': start_time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'overall_prob': overall_prob,                            
                            'sub_type_id': sub_type_id,
                            'prediction': bet_pick,
                            'bet_pick': bet_pick,
                            'odd': odd_value,
                            'special_bet_value': special_bet_value,
                            'outcome_id': outcome_id
                        }
                print(match)
                self.db.insert_match(match)
        return match 
    
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
                  
    def __call__(self):
        matches = []
        # Use ThreadPoolExecutor to spawn a thread for each match
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.predict_match, parent_match_id) for parent_match_id in self.get_upcoming_match_ids()]

            # Wait for all threads to finish
            concurrent.futures.wait(threads)
            for thread in threads:
                try:
                    match = thread.result()
                    if match:
                        matches.append(match)
                except Exception as e:
                    print(f"Error processing match: {e}")

            self.auto_bet(matches)

if __name__ == '__main__':
    OverUnder()()