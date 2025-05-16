from datetime import datetime

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
        start_time = meta.get('start_time') 
        
        if datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date():
            data = match_details.get('data')
            match = None
            if data:
                for d in data:                
                    if int(d.get('sub_type_id')) == 548:  
                        for odd in d.get('odds'):   
                            is_odd = bool(int(float(odd.get('odd_value').replace('.',''))%2))
                            if float(odd.get('odd_value')) > 1.28 and float(odd.get('odd_value')) < 1.38 and is_odd and odd.get('odd_key') not in ['1-3', '3-6']:
                                match = {
                                            'parent_match_id': parent_match_id,
                                            'match_id': meta.get('match_id'),
                                            'start_time': start_time,
                                            'home_team': meta.get('home_team'),
                                            'away_team': meta.get('away_team'),
                                            'overall_prob': 98,                            
                                            'sub_type_id': d.get('sub_type_id'),
                                            'prediction': odd.get('odd_key'),
                                            'bet_pick': odd.get('odd_key'),
                                            'odd': float(odd.get('odd_value')),
                                            'special_bet_value': odd.get('special_bet_value'),
                                            'outcome_id': odd.get('outcome_id')
                                        }
                if match:
                    print(match)
                    self.db.insert_match(match)                    
                    return match 
