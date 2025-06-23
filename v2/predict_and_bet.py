import  concurrent.futures, json
import time
from utils.betika import Betika
from utils.redis_crud import RedisCRUD


class PredictAndBet:
    def __init__(self):
        self.redis = RedisCRUD()
        self.betika = Betika()

    def analyze_market(self, odds):
        """Analyze odds trend for a market, ignoring sharp drops."""
        if not odds or len(odds) < 7:
            return 0.0

        # Convert odds to floats (if not already done)
        odds = [float(o) for o in odds]

        net_change = 0
        for i in range(1, len(odds)):
            net_change += (odds[i - 1] - odds[i])
        
        return net_change

    def get_current_odd(self, parent_match_id, sub_type_id, odd_key):
        match_details = self.betika.get_match_details(parent_match_id, live=True)
        data = match_details.get('data')
        if data:
            for sub_type in data:
                if sub_type.get('sub_type_id') == sub_type_id:
                    odds = sub_type.get('odds')
                    for odd in odds:
                        if odd.get('odd_key') == odd_key:
                            return odd.get('odd_value')
        return None
                
    def get_top_drops(self, parent_match_id, match_time):
        """Analyze odds for a match and print top 3 dropping markets."""
        results = []
        data = self.redis.get(parent_match_id)
        
        if not data:
            #print(f"No data found for match ID: {parent_match_id}")
            return []
        minutes = int(match_time.split(':')[0])
        if minutes < 15 or (minutes >= 45 and minutes < 55) or minutes > 80:
            #print(f"Match ID: {parent_match_id} just started or is ending soon.")
            return []

        try:
            meta = json.loads(data)["meta"]
            subtypes = json.loads(data)["data"]
        except json.JSONDecodeError:
            print(f"Invalid JSON data for match ID: {parent_match_id}")
            return []
        for sub_type in subtypes:
            odds_list = sub_type.get('odds', [])
            for odd in odds_list:
                odd['parent_match_id'] = parent_match_id
                if odd.get('sport_id') != 14:
                    continue
                
                # Extract odds history and market identifier
                odds = odd.get('odd_history', [])
                
                if not odds:
                    continue
                
                # Convert odds from bytes to floats if needed
                try:
                    odds = [float(o.decode('utf-8')) if isinstance(o, bytes) else float(o) for o in odds]
                except (ValueError, AttributeError) as e:
                    print(f"Error converting odds for {odd}: {e}")
                    continue
                
                # Analyze the market
                net_change = self.analyze_market(odds[:-10])
                if net_change > 0.0:
                    continue 
                
                odd_value = self.get_current_odd(parent_match_id, sub_type.get('sub_type_id'), odd.get('odd_key'))
                if odd_value and float(odd_value) <= 1.6:                    
                    betslip = {                    
                        "sub_type_id": sub_type.get('sub_type_id'),
                        "bet_pick": odd.get('odd_key'), #team
                        "odd_value": odd_value,
                        "outcome_id": odd.get('outcome_id'),
                        "sport_id": odd.get('sport_id'),
                        "special_bet_value": odd.get('special_bet_value'),
                        "parent_match_id": parent_match_id,
                        "bet_type": 8
                    }
                
                    results.append((betslip, net_change))
        
        if not results:
            #print(f"No valid odds data for match ID: {parent_match_id}")
            return []

        # Sort by net change (most negative = most dropping)
        top_3 = sorted(results, key=lambda x: x[1])[:3]
        
        top_drops = [betslip for betslip, _ in top_3]
                
        return top_drops  # Return for potential further use
    
    def auto_bet(self, data):
        try:
            composite_betslip = None
            composite_betslips = [] 
            betslips = []
            total_odd = 1
            min_odd = 2.7
            for betslip in data:    
                betslips.append(betslip)
                total_odd *= float(betslip.get('odd_value'))                                            
                composite_betslip = {
                    'total_odd': total_odd,
                    'betslips': betslips
                }
                if total_odd >= min_odd:
                    composite_betslips.append(composite_betslip)
                    betslips = []
                    total_odd = 1
                    composite_betslip = None 

            if len(composite_betslips) > 0:   
                if composite_betslip:
                    composite_betslips[0]['betslips'].extend(composite_betslip['betslips'])
                    composite_betslips[0]['total_odd'] *= composite_betslip['total_odd'] 
                balance, bonus = self.betika.get_balance()
                stake = int(min(5, balance)) 
                if stake > 0:
                    for cb in composite_betslips:
                        ttl_odd = cb['total_odd']
                        slips = cb['betslips']
                        # print(slips, ttl_odd, stake)
                        self.betika.place_bet(slips, ttl_odd, stake)
                        time.sleep(2)
        except Exception as e:
            print(f"Error in auto_bet: {e}")
                    
        
    def __call__(self):
        """Run analysis for all live matches concurrently."""
        live_match_ids = self.betika.get_match_ids(live=True)
        if not live_match_ids:
            print("No live matches found.")
            return
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks for each match ID
            futures = [executor.submit(self.get_top_drops, parent_match_id, match_time) for parent_match_id, match_time in live_match_ids]
            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
            
            # Optionally collect results (if needed)
            zeros = [] 
            ones = [] 
            twos = []
            for future in futures:
                try:
                    top_drops = future.result()  # Raises exception if task 
                    if len(top_drops) > 0:
                        zeros.append(top_drops[0])
                    if len(top_drops) > 1:
                        ones.append(top_drops[1])
                    if len(top_drops) > 2: 
                        twos.append(top_drops[2])                
                except Exception as e:
                    print(f"Error in task: {e}")
                    
            # Auto-bet on the top 3 dropping markets
            self.auto_bet(zeros)
            self.auto_bet(ones)    
            self.auto_bet(twos)      

if __name__ == '__main__':    
    while True:
        PredictAndBet()()
        
        time.sleep(120)