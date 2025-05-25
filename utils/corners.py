
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class Corners():
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
                            overall_prob = 88
                            special_bet_value = None 
                            outcome_id = None
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
                                                        overall_prob = 98 if odd_value < 1.32 else overall_prob
                                                        
                                    else:  
                                        sub_type_id = int(d.get('sub_type_id'))                                      
                                        bet_pick = odd.get('odd_key')    
                                        odd_value = float(odd.get('odd_value'))    
                                        special_bet_value = odd.get('special_bet_value')      
                                        outcome_id = odd.get('outcome_id')
                                        overall_prob = 98 if odd_value < 1.32 else overall_prob
                                        
                                    if odd_value <= 1.38:
                                        if odd_value < 1.2 and 'over' in bet_pick:
                                            v = float(bet_pick.replace('over ',''))
                                            bet_pick = f'over {v+1}'
                                            special_bet_value = f'total={v+1}'
                                            odd_value += 0.25

                                        if bet_pick == 'over 6.5':
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
                                            #self.db.insert_match(match)
        return match 
           