
from utils.betika import Betika
from utils.helper import Helper

class CornersBeta():
    def __init__(self):
        self.betika = Betika()
        self.helper = Helper()
    
    def predict_match(self, match):
        if match["bet_pick"] == "over 1.5":
            parent_match_id = match["parent_match_id"]
            url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
            match_details = self.betika.get_data(url)
            data = match_details.get('data')
            if data:
                for d in data:
                    sub_type_id = int(d.get('sub_type_id'))
                    if sub_type_id in [166]:   # 166 = corners
                        odds = d.get('odds') 
                        for odd in odds:    
                            bet_pick = odd.get('odd_key')  
                            sub_type_id = int(odd.get('sub_type_id'))
                            odd_value = float(odd.get('odd_value'))        
                            special_bet_value = odd.get('special_bet_value')      
                            outcome_id = odd.get('outcome_id')
                            
                            if odd_value < 1.5 and 'over' in bet_pick:
                                match["bet_pick"] = bet_pick
                                match["prediction"] = bet_pick
                                match["sub_type_id"] = sub_type_id
                                match["odd"] = odd_value
                                match["special_bet_value"] = special_bet_value
                                match["outcome_id"] = outcome_id
                                print(match)
        
        return match 
           