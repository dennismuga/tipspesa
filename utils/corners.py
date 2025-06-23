
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class Corners():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()
        self.helper = Helper()
    
    def predict_match(self, match):
        parent_match_id = match["parent_match_id"]
        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
        match_details = self.betika.get_data(url)
        data = match_details.get('data')
        if data:
            for d in data:
                sub_type_id = int(d.get('sub_type_id'))
                if sub_type_id == 166:   
                    odds = d.get('odds') 
                    for odd in odds:
                        odd_value = float(odd.get('odd_value'))           
                        bet_pick = odd.get('odd_key')  

                        if bet_pick == 'under 10.5':  
                            match["prediction"] = bet_pick   
                            match["odd"] = odd_value   
                            match["sub_type_id"] = sub_type_id   
                            match["bet_pick"] = bet_pick   
                            match["special_bet_value"] = odd.get('special_bet_value')    
                            match["outcome_id"] = odd.get('outcome_id')   
                            return match                        
        return None 
           