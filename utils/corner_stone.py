import concurrent.futures

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD


class CornerStone():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()
    
    def get_upcoming_match_ids(self):    
        total = 1001
        limit = 1000
        page = 1
        matches_ids = set()
        while limit*page < total:
            total, page, events = self.betika.get_events(limit, page)
            
            for event in events:
                parent_match_id = event.get('parent_match_id')
                matches_ids.add(parent_match_id)
        
        return matches_ids
    
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
                if sub_type_id == 166:   
                    odds = d.get('odds')
                    for odd in odds:
                        odd_value = float(odd.get('odd_value'))           
                        bet_pick = odd.get('odd_key')      
                        special_bet_value = odd.get('special_bet_value')      
                        outcome_id = odd.get('outcome_id')
                        if odd_value>=1.29 and odd_value <= 1.44 and 'over' in bet_pick:                                                
                            match = {
                                'match_id': match_id,
                                'start_time': start_time,
                                'home_team': home_team,
                                'away_team': away_team,
                                'prediction': bet_pick,
                                'odd': odd_value,
                                'overall_prob': 88,
                                'parent_match_id': parent_match_id,
                                'sub_type_id': sub_type_id,
                                'bet_pick': bet_pick,
                                'special_bet_value': special_bet_value,
                                'outcome_id': outcome_id
                            }
        if match:
            print(match)
            self.db.insert_match(match)

    def __call__(self):
        # Use ThreadPoolExecutor to spawn a thread for each match
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.predict_match, parent_match_id) for parent_match_id in self.get_upcoming_match_ids()]

            # Wait for all threads to finish
            concurrent.futures.wait(threads)

if __name__ == '__main__':
    CornerStone()()