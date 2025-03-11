
import  concurrent.futures, json
import time
from utils.betika import Betika
from utils.redis_crud import RedisCRUD

class Stats():
    def __init__(self):
        self.betika = Betika()
        self.redis = RedisCRUD()
        
    def save_match_details(self, parent_match_id):
        match_details = self.betika.get_match_details(parent_match_id, live=True)
        data = match_details.get('data')
        existing_data = self.redis.get(parent_match_id)
        if existing_data:
            existing_data = json.loads(existing_data)
            for sub_type in existing_data:
                odds = sub_type.get('odds')
                if len(odds) == 0:
                    existing_data.pop(existing_data.index(sub_type))
                for odd in odds:
                    if odd.get('sport_id') == 14:
                        odd_history = odd.get('odd_history', [])
                        for sub_type_2 in data:
                            if sub_type_2.get('sub_type_id'):
                                odds_2 = sub_type_2.get('odds')
                                if len(odds_2) == 0:
                                    existing_data.pop(existing_data.index(sub_type))
                                for odd_2 in odds_2:
                                    if odd.get('outcome_id') == odd_2.get('outcome_id'):
                                        odd_value = odd_2.get('odd_value')
                                        odd['odd_value'] = odd_value
                                        break
                        odd_history.append(odd_value)
                        odd['odd_history'] = odd_history
                    else:
                        odds.pop(odds.index(odd))
                    
                sub_type['odds'] = odds
                
        
            if len(existing_data) == 0:
                self.redis.delete(parent_match_id)
                print(f"Data for match {parent_match_id} deleted from Redis.")
                return
            else:
                data = existing_data
        else:            
            for sub_type in data:
                odds = sub_type.get('odds')
                if len(odds) == 0:
                    data.pop(data.index(sub_type))
                else:
                    for odd in odds:
                        if odd.get('sport_id') == 14:
                            odd_value = odd.get('odd_value')
                            odd_history = odd.get('odd_history', [])
                            odd_history.append(odd_value)
                            odd['odd_history'] = odd_history
                        else:
                            odds.pop(odds.index(odd))
                    sub_type['odds'] = odds
                    
        if len(data) > 0:
            data = json.dumps(data)
            self.redis.set(parent_match_id, data)  
            print(f"Data for match {parent_match_id} stored in Redis.")

    def __call__(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            live_match_ids = self.betika.get_match_ids(live=True)
            threads = [executor.submit(self.save_match_details, parent_match_id) for parent_match_id, match_time in live_match_ids]
            
            concurrent.futures.wait(threads)   

if __name__ == '__main__':    
    while True:
        Stats()()
        
        time.sleep(60)
 