
from datetime import datetime

from utils.betika import Betika
from utils.helper import Helper

class CornersBeta():
    def __init__(self):
        self.betika = Betika()
        self.helper = Helper()      

    def get_odd(self, odds, odd_key):
        for odd in odds:
            if odd.get('odd_key') == odd_key:
                return odd
        return None
    
    
    def predict_match(self, parent_match_id):
        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
        match_details = self.betika.get_data(url)
        if not match_details:
            return None            
        meta = match_details.get('meta')   
        start_time = meta.get('start_time') 
        
        if datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date():
            data = match_details.get('data')
            match = None
            if data:
                over_1_5 = None 
                over_2_5 = None 
                over_6_5 = None
                over_7_5 = None
                over_8_5 = None
                over_9_5 = None
                
                under_9_5 = None
                under_10_5 = None
                under_11_5 = None
                under_12_5 = None
                for subtypes in data:  
                    odds = subtypes.get('odds')
                    if int(subtypes.get('sub_type_id')) == 18:                                      
                        over_1_5 = self.get_odd(odds, 'over 1.5')
                        over_2_5 = self.get_odd(odds, 'over 2.5')
                        
                    if int(subtypes.get('sub_type_id')) == 166:
                        over_6_5 = self.get_odd(odds, 'over 6.5')
                        over_7_5 = self.get_odd(odds, 'over 7.5')
                        over_8_5 = self.get_odd(odds, 'over 8.5')
                        over_9_5 = self.get_odd(odds, 'over 9.5')                        
                        
                        under_9_5 = self.get_odd(odds, 'under 9.5')
                        under_10_5 = self.get_odd(odds, 'under 10.5')
                        under_11_5 = self.get_odd(odds, 'under 11.5')
                        if over_6_5 and under_9_5:
                            if float(over_6_5.get('odd_value')) < float(under_9_5.get('odd_value')):
                                if float(over_6_5.get('odd_value')) < 1.5:
                                    match = {
                                            'parent_match_id': parent_match_id,
                                            'match_id': meta.get('match_id'),
                                            'start_time': start_time,
                                            'home_team': meta.get('home_team'),
                                            'away_team': meta.get('away_team'),
                                            'overall_prob': 0,                            
                                            'sub_type_id': subtypes.get('sub_type_id'),
                                            'prediction': subtypes.get('name'),
                                            'bet_pick': over_6_5.get('odd_key'),
                                            'odd': float(over_6_5.get('odd_value')),
                                            'special_bet_value': over_6_5.get('special_bet_value'),
                                            'outcome_id': over_6_5.get('outcome_id')
                                        }
                                    
                        if over_7_5 and under_10_5:
                            if float(over_7_5.get('odd_value')) < float(under_10_5.get('odd_value')):
                                if float(over_7_5.get('odd_value')) < 1.5:
                                    match = {
                                            'parent_match_id': parent_match_id,
                                            'match_id': meta.get('match_id'),
                                            'start_time': start_time,
                                            'home_team': meta.get('home_team'),
                                            'away_team': meta.get('away_team'),
                                            'overall_prob': 0,                            
                                            'sub_type_id': subtypes.get('sub_type_id'),
                                            'prediction': subtypes.get('name'),
                                            'bet_pick': over_7_5.get('odd_key'),
                                            'odd': float(over_7_5.get('odd_value')),
                                            'special_bet_value': over_7_5.get('special_bet_value'),
                                            'outcome_id': over_7_5.get('outcome_id')
                                        }
                                    
                            elif float(under_10_5.get('odd_value')) < 1.5:
                                match = {
                                            'parent_match_id': parent_match_id,
                                            'match_id': meta.get('match_id'),
                                            'start_time': start_time,
                                            'home_team': meta.get('home_team'),
                                            'away_team': meta.get('away_team'),
                                            'overall_prob': 0,                            
                                            'sub_type_id': subtypes.get('sub_type_id'),
                                            'prediction': subtypes.get('name'),
                                            'bet_pick': under_10_5.get('odd_key'),
                                            'odd': float(under_10_5.get('odd_value')),
                                            'special_bet_value': under_10_5.get('special_bet_value'),
                                            'outcome_id': under_10_5.get('outcome_id')
                                        }
                                    
                        if over_8_5 and under_11_5:
                            if float(over_8_5.get('odd_value')) < float(under_11_5.get('odd_value')):
                                if float(over_8_5.get('odd_value')) < 1.5:
                                    match = {
                                            'parent_match_id': parent_match_id,
                                            'match_id': meta.get('match_id'),
                                            'start_time': start_time,
                                            'home_team': meta.get('home_team'),
                                            'away_team': meta.get('away_team'),
                                            'overall_prob': 0,                            
                                            'sub_type_id': subtypes.get('sub_type_id'),
                                            'prediction': subtypes.get('name'),
                                            'bet_pick': over_8_5.get('odd_key'),
                                            'odd': float(over_8_5.get('odd_value')),
                                            'special_bet_value': over_8_5.get('special_bet_value'),
                                            'outcome_id': over_8_5.get('outcome_id')
                                        }
                            elif float(under_11_5.get('odd_value')) < 1.5:
                                match = {
                                        'parent_match_id': parent_match_id,
                                        'match_id': meta.get('match_id'),
                                        'start_time': start_time,
                                        'home_team': meta.get('home_team'),
                                        'away_team': meta.get('away_team'),
                                        'overall_prob': 0,                            
                                        'sub_type_id': subtypes.get('sub_type_id'),
                                        'prediction': subtypes.get('name'),
                                        'bet_pick': under_11_5.get('odd_key'),
                                        'odd': float(under_11_5.get('odd_value')),
                                        'special_bet_value': under_11_5.get('special_bet_value'),
                                        'outcome_id': under_11_5.get('outcome_id')
                                    }
                                    
                        if over_9_5 and under_12_5:
                            if float(over_9_5.get('odd_value')) < float(under_12_5.get('odd_value')):
                                pass
                            
                            elif float(under_12_5.get('odd_value')) < 1.5:
                                match = {
                                        'parent_match_id': parent_match_id,
                                        'match_id': meta.get('match_id'),
                                        'start_time': start_time,
                                        'home_team': meta.get('home_team'),
                                        'away_team': meta.get('away_team'),
                                        'overall_prob': 0,                            
                                        'sub_type_id': subtypes.get('sub_type_id'),
                                        'prediction': subtypes.get('name'),
                                        'bet_pick': under_12_5.get('odd_key'),
                                        'odd': float(under_12_5.get('odd_value')),
                                        'special_bet_value': under_12_5.get('special_bet_value'),
                                        'outcome_id': under_12_5.get('outcome_id')
                                    }
                            
                        if match:                
                            return match
