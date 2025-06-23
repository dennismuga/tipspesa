from datetime import datetime, time

from utils.betika import Betika
from utils.helper import Helper

class MultiGoalOverUnder():
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
        
        if (datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date() and datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").time() > time(12, 0)):
            data = match_details.get('data')
            match = None
            if data:
                over_1_5 = None 
                over_2_5 = None 
                under_3_5 = None
                under_4_5 = None
                goals_1_3 = None
                goals_2_6 = None
                goals_3_6 = None
                for subtypes in data:  
                    odds = subtypes.get('odds')
                    if int(subtypes.get('sub_type_id')) == 18:                                      
                        over_1_5 = self.get_odd(odds, 'over 1.5')
                        over_2_5 = self.get_odd(odds, 'over 2.5')
                        under_3_5 = self.get_odd(odds, 'under 3.5')
                        under_4_5 = self.get_odd(odds, 'under 4.5')
                        
                    if int(subtypes.get('sub_type_id')) == 548:
                        goals_1_3 = self.get_odd(odds, '1-3')
                        goals_2_6 = self.get_odd(odds, '2-6')
                        goals_3_6 = self.get_odd(odds, '3-6')
                        if goals_1_3 and goals_2_6:
                            if over_1_5 and under_3_5:
                                if float(goals_1_3.get('odd_value')) < float(goals_2_6.get('odd_value')):
                                    # if float(under_3_5.get('odd_value')) >= 1.2 and float(under_3_5.get('odd_value')) < float(over_1_5.get('odd_value')):
                                    #     match = {
                                    #           'parent_match_id': parent_match_id,
                                    #           'match_id': meta.get('match_id'),
                                    #           'start_time': start_time,
                                    #           'home_team': meta.get('home_team'),
                                    #           'away_team': meta.get('away_team'),
                                    #           'overall_prob': 98,                            
                                    #           'sub_type_id': "18",
                                    #           'prediction': under_3_5.get('odd_key'),
                                    #           'bet_pick': under_3_5.get('odd_key'),
                                    #           'odd': float(under_3_5.get('odd_value')),
                                    #           'special_bet_value': under_3_5.get('special_bet_value'),
                                    #           'outcome_id': under_3_5.get('outcome_id')
                                    #       }
                                    pass
                                else:
                                    if float(over_1_5.get('odd_value')) >= 1.25 and float(over_1_5.get('odd_value')) <= 1.29 and float(over_1_5.get('odd_value')) < float(under_3_5.get('odd_value')):
                                        match = {
                                                'parent_match_id': parent_match_id,
                                                'match_id': meta.get('match_id'),
                                                'start_time': start_time,
                                                'home_team': meta.get('home_team'),
                                                'away_team': meta.get('away_team'),
                                                'overall_prob': 98,                            
                                                'sub_type_id': "18",
                                                'prediction': 'TOTAL',
                                                'bet_pick': over_1_5.get('odd_key'),
                                                'odd': float(over_1_5.get('odd_value')),
                                                'special_bet_value': over_1_5.get('special_bet_value'),
                                                'outcome_id': over_1_5.get('outcome_id')
                                            }
                                        
                            if over_2_5 and under_4_5:    
                                if float(goals_1_3.get('odd_value')) < float(goals_3_6.get('odd_value')):
                                    if float(under_4_5.get('odd_value')) >= 1.2 and float(under_4_5.get('odd_value')) < float(over_2_5.get('odd_value')):
                                        match = {
                                                'parent_match_id': parent_match_id,
                                                'match_id': meta.get('match_id'),
                                                'start_time': start_time,
                                                'home_team': meta.get('home_team'),
                                                'away_team': meta.get('away_team'),
                                                'overall_prob': 98,                            
                                                'sub_type_id': "18",
                                                'prediction': 'TOTAL',
                                                'bet_pick': under_4_5.get('odd_key'),
                                                'odd': float(under_4_5.get('odd_value')),
                                                'special_bet_value': under_4_5.get('special_bet_value'),
                                                'outcome_id': under_4_5.get('outcome_id')
                                            }
                                # else:
                                #     if float(over_2_5.get('odd_value')) >= 1.25 and float(over_2_5.get('odd_value')) <= 1.49 and float(over_2_5.get('odd_value')) < float(under_4_5.get('odd_value')):
                                #         match = {
                                #                 'parent_match_id': parent_match_id,
                                #                 'match_id': meta.get('match_id'),
                                #                 'start_time': start_time,
                                #                 'home_team': meta.get('home_team'),
                                #                 'away_team': meta.get('away_team'),
                                #                 'overall_prob': 98,                            
                                #                 'sub_type_id': "18",
                                #                 'prediction': over_2_5.get('odd_key'),
                                #                 'bet_pick': over_2_5.get('odd_key'),
                                #                 'odd': float(over_2_5.get('odd_value')),
                                #                 'special_bet_value': over_2_5.get('special_bet_value'),
                                #                 'outcome_id': over_2_5.get('outcome_id')
                                #             }
                            
                            if match:                
                                return match
                                
                        
                        

                                
                        
                        
