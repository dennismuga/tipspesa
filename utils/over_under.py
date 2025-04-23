
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class OverUnder():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()
        self.helper = Helper()
    
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
                        
                        if '3.5' in odd.get('odd_key') or '3.5' in last_odd.get('odd_key'):
                            continue
                            
                        if cur_odd_value >=1.19 and cur_odd_value <= 1.41 and last_odd_value>=1.41 and cur_odd_value < last_odd_value and (last_index > 5 or odd.get('odd_key') != 'over 1.5'):
                            sub_type_id = int(d.get('sub_type_id'))
                            bet_pick = odd.get('odd_key')    
                            odd_value = cur_odd_value   
                            special_bet_value = odd.get('special_bet_value')      
                            outcome_id = odd.get('outcome_id')
                        
                        elif last_odd_value >=1.19 and last_odd_value <= 1.41 and cur_odd_value>=1.41 and last_odd_value < cur_odd_value:
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