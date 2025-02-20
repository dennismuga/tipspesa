
import json, time

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

class AutoBet():
    def __init__(self) -> None:
        self.betika = Betika()     
        self.db = PostgresCRUD()
    
    def compose_bet_slip(self, parent_match_id, sub_type_id, bet_pick, odd_value, outcome_id, special_bet_value):
        return {
            "sub_type_id": str(sub_type_id),
            "bet_pick": bet_pick, #team
            "odd_value": odd_value,
            "outcome_id": str(outcome_id),  
            "sport_id": "14",
            "special_bet_value": special_bet_value,
            "parent_match_id": str(parent_match_id),
            "bet_type": 7
        }
    
    def auto_predict(self):
        # Load JSON data from a file
        with open('predictions.json', 'r') as file:
            data = json.load(file)
            added_parent_match_ids = set()
            for datum in data:
                parent_match_id= datum.get('parent_match_id')
                predictions = datum.get('predictions')
                winner = predictions.get('1X2')
                total_goals = predictions.get('TOTAL GOALS')
                btts = predictions.get('BOTH TEAMS TO SCORE')
                total_corners = predictions.get('TOTAL CORNERS')
                predictions = {**winner, **total_goals, **btts, **total_corners}
                for key in predictions:
                    prediction = int(predictions.get(key).replace('%',''))
                    if (prediction>=80 and key in ['OVER 1.5', 'OVER 7.5']) or (prediction>=75 and key in ['OVER 2.5', 'OVER 8.5', 'YES']) or (prediction>=70 and key in ['OVER 9.5', '1', 'X', '2']) or (prediction>=65 and key in ['OVER 10.5']):  
                        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
                        match_details = self.betika.get_data(url)
                        data = match_details.get('data')
                        if data:
                            for d in data:
                                sub_type_id = d.get('sub_type_id')
                                if sub_type_id in ["1", "18", "29", "166"]:
                                    odds = d.get('odds')
                                    for odd in odds:
                                        odd_value = odd.get('odd_value')
                                        if key == odd.get('display') and parent_match_id not in added_parent_match_ids:
                                            bet_pick = 'GG' if key == 'YES' else odd.get('odd_key')
                                            print(f"{datum.get('home_team')} vs {datum.get('away_team')} = {bet_pick} [x{odd_value}]")                                            
                                            match = {
                                                'match_id': match_details.get('meta').get('match_id'),
                                                'start_time': match_details.get('meta').get('start_time'),
                                                'home_team': datum.get('home_team'),
                                                'away_team': datum.get('away_team'),
                                                'prediction': bet_pick,
                                                'odd': odd_value,
                                                'overall_prob': prediction,
                                                'parent_match_id': parent_match_id,
                                                'sub_type_id': sub_type_id,
                                                'bet_pick': bet_pick,
                                                'special_bet_value': odd.get('special_bet_value'),
                                                'outcome_id': odd.get('outcome_id')
                                            }
                                            self.db.insert_match(match)
    
    def auto_bet(self):
        betslips = []
        min_odd = 10
        total_odd = 1
        composite_betslip = None
        composite_betslips = []
        for prediction in self.db.get_predictions():
            parent_match_id = prediction['parent_match_id']
            sub_type_id = prediction['sub_type_id']
            bet_pick = prediction['bet_pick']
            bet_pick = 'YES' if bet_pick == 'GG' else bet_pick
            special_bet_value = prediction['special_bet_value']
            outcome_id = prediction['outcome_id']
            url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
            match_details = self.betika.get_data(url)
            data = match_details.get('data')
            if data:
                for d in data:
                    if sub_type_id == int(d.get('sub_type_id')):   
                        odds = d.get('odds')
                        for odd in odds:
                            if bet_pick == odd.get('odd_key'): 
                                odd_value = odd.get('odd_value') 
                                betslip = self.compose_bet_slip(parent_match_id, sub_type_id, bet_pick, odd_value, outcome_id, special_bet_value)
                                betslips.append(betslip)
                                total_odd *= float(odd_value)                                            
                                composite_betslip = {
                                    'total_odd': total_odd,
                                    'betslips': betslips
                                }
                                if total_odd > min_odd*1.2:
                                    print(total_odd)
                                    composite_betslips.append(composite_betslip)
                                    betslips = []
                                    total_odd = 1
                                    composite_betslip = None 

        if composite_betslip:
            print(total_odd)
            composite_betslips.append(composite_betslip)
        if len(composite_betslips) > 0:                        
            balance, bonus = self.betika.get_balance()
            placeable = (balance) #*0.75
            min_stake = placeable/min_odd
            equal_stake = placeable/len(composite_betslips)
            max_stake = max(min_stake, equal_stake)
            stake = int( max_stake if max_stake>1 else placeable)
            if stake > 0:
                for cb in composite_betslips:
                    ttl_odd = cb['total_odd']
                    slips = cb['betslips']
                    print(f'TOTAL ODD: {ttl_odd}')
                    self.betika.place_bet(slips, ttl_odd, stake)
                    time.sleep(5)

    def __call__(self):
        # self.auto_predict()
        self.auto_bet()

if __name__ == '__main__':
    AutoBet()()