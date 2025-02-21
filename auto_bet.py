
import time

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
    
    def auto_bet(self):
        betslips = []
        max_games = 5
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
                                if len(betslips) == max_games:
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
            placeable = balance #*0.75
            stake = int(placeable/len(composite_betslips))
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