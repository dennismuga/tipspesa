import concurrent.futures
import time 

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

class CornerStone():
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
        data = match_details.get('data')
        match = None
        if data:
            for d in data:
                sub_type_id = int(d.get('sub_type_id'))
                if sub_type_id in [139, 166]:   
                    odds = d.get('odds') 
                    for odd in odds:
                        odd_value = float(odd.get('odd_value'))           
                        bet_pick = odd.get('odd_key')  

                        if 'under' in bet_pick:
                            under = float(bet_pick.replace('under ', ''))
                            for odd in odds:    
                                if sub_type_id == int(d.get('sub_type_id')) and odd.get('odd_key') == f'over {under-3}' and float(odd.get('odd_value')) < odd_value:  
                                    if float(odd.get('odd_value')) >= 1.25:
                                        for d2 in data:
                                            if int(d2.get('sub_type_id')) in [18]:   
                                                for odd2 in d2.get('odds'):    
                                                    if odd2.get('odd_key') == 'over 1.5':
                                                        sub_type_id = int(d2.get('sub_type_id'))
                                                        bet_pick = odd2.get('odd_key')    
                                                        odd_value = float(odd2.get('odd_value'))    
                                                        special_bet_value = odd2.get('special_bet_value')      
                                                        outcome_id = odd2.get('outcome_id')
                                                        overall_prob = 98 if odd_value < 1.32 else 88
                                                        
                                    elif sub_type_id == 139:
                                        for d2 in data:
                                            if int(d2.get('sub_type_id')) in [166]:   
                                                for odd2 in d2.get('odds'):  
                                                    expected_odd_key = f"{odd.get('odd_key').split(' ')[0]} {float(odd.get('odd_key').split(' ')[1])+5}"
                                                    if odd2.get('odd_key') == expected_odd_key:
                                                        sub_type_id = int(d2.get('sub_type_id'))
                                                        bet_pick = odd2.get('odd_key')    
                                                        odd_value = float(odd2.get('odd_value'))    
                                                        special_bet_value = odd2.get('special_bet_value')      
                                                        outcome_id = odd2.get('outcome_id')
                                                        overall_prob = 98 if odd_value < 1.32 else 88
                                                        
                                    else:  
                                        sub_type_id = int(d.get('sub_type_id'))                                      
                                        bet_pick = odd.get('odd_key')    
                                        odd_value = float(odd.get('odd_value'))    
                                        special_bet_value = odd.get('special_bet_value')      
                                        outcome_id = odd.get('outcome_id')
                                        overall_prob = 98 if odd_value < 1.32 else 88
                                        
                                    if odd_value <= 1.38:
                                        if odd_value < 1.2:
                                            v = float(bet_pick.replace('over ',''))
                                            bet_pick = f'over {v+1}'
                                            special_bet_value = f'total={v+1}'
                                            odd_value += 0.25

                                        match = {
                                            'match_id': match_id,
                                            'start_time': start_time,
                                            'home_team': home_team,
                                            'away_team': away_team,
                                            'prediction': bet_pick,
                                            'odd': odd_value,
                                            'overall_prob': overall_prob,
                                            'parent_match_id': parent_match_id,
                                            'sub_type_id': sub_type_id,
                                            'bet_pick': bet_pick,
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
            min_odd = 10
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
            stake = int((balance/2)/len(composite_betslips)) 
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
    CornerStone()()