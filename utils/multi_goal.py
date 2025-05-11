
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class MultiGoal():
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
                if int(d.get('sub_type_id')) == 548:  
                    for odd in d.get('odds'):   
                        is_odd = bool(int(float(odd.get('odd_value').replace('.',''))%2))
                        if float(odd.get('odd_value')) > 1.28 and float(odd.get('odd_value')) < 1.38 and is_odd: # and odd.get('odd_key') not in ['2-4','2-5','2-6']:
                            sub_type_id = d.get('sub_type_id')
                            bet_pick = odd.get('odd_key')
                            odd_value = float(odd.get('odd_value'))   
                            special_bet_value = odd.get('special_bet_value')
                            outcome_id = odd.get('outcome_id')  
      
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
                bet_pick = None
                
        return match 
