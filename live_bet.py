# Description: This script is used to predict the outcome of live matches
import asyncio, concurrent.futures, json, os, time, threading
from itertools import combinations
from dotenv import load_dotenv
from redis import Redis
from sklearn.ensemble import RandomForestClassifier
import numpy as np

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

# Load environment variables from .env file
load_dotenv()
class RedisCRUD():
    def __init__(self):
        self.redis = Redis(
            host=os.getenv('REDIS_HOSTNAME'),
            port=os.getenv('REDIS_PORT'),
            password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_SSL') in ['True', '1'] else None,
            ssl=False if os.getenv('REDIS_SSL') in ['False', '0'] else True
        )
        
    def set(self, parent_match_id, data):
        try:
            # Store the JSON data in Redis with a TTL of 90 minutes (5400 seconds)
            self.redis.set(f"{parent_match_id}", data, ex=7200)
            # print(f"Data for match {parent_match_id} stored in Redis.")

        except Exception as e:
            print(f"Error storing data in Redis: {e}")
                
    def get(self, key):
        value = self.redis.get(key)
        return value.decode() if value else None
    
    def delete(self, key):
        self.redis.delete(key)
class Stats():
    def __init__(self):
        self.betika = Betika()
        self.redis = RedisCRUD()
    
    def get_live_match_ids(self):   
        limit = 100
        total = limit + 1
        page = 1
        matches_ids = set()
        while limit*page < total:
            total, page, matches = self.betika.get_matches(limit, page, live=True)
        
        for match in matches:
            parent_match_id = match.get('parent_match_id')
            matches_ids.add(parent_match_id)
        
        return matches_ids
        
    def save_match_details(self, parent_match_id):
        match_details = self.betika.get_match_details(parent_match_id, live=True)
        data = match_details.get('data')
        existing_data = self.redis.get(parent_match_id)
        if existing_data:
            existing_data = json.loads(existing_data)
            for sub_type in existing_data:
                odds = sub_type.get('odds')
                for odd in odds:
                    if odd.get('sport_id') == 14:
                        odd_history = odd.get('odd_history', [])
                        for sub_type_2 in data:
                            if sub_type_2.get('sub_type_id'):
                                for odd_2 in sub_type_2.get('odds'):
                                    if odd.get('outcome_id') == odd_2.get('outcome_id'):
                                        odd_value = odd_2.get('odd_value')
                                        break
                        odd_history.append(odd_value)
                        odd['odd_history'] = odd_history
                    else:
                        odds.pop(odds.index(odd))
                    
                sub_type['odds'] = odds
            data = existing_data
        else:            
            for sub_type in data:
                odds = sub_type.get('odds')
                for odd in odds:
                    if odd.get('sport_id') == 14:
                        odd_value = odd.get('odd_value')
                        odd_history = odd.get('odd_history', [])
                        odd_history.append(odd_value)
                        odd['odd_history'] = odd_history
                    else:
                        odds.pop(odds.index(odd))
                sub_type['odds'] = odds
                
        data = json.dumps(data)
        self.redis.set(parent_match_id, data)  

    def __call__(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            live_match_ids = self.get_live_match_ids()
            threads = [executor.submit(self.save_match_details, parent_match_id) for parent_match_id in live_match_ids]
            
            concurrent.futures.wait(threads)
    
class PredictAndBet:
    def __init__(self):
        self.redis = RedisCRUD()
        self.betika = Betika()

    def analyze_market(self, odds):
        """Analyze odds trend for a market, ignoring sharp drops."""
        if not odds or len(odds) < 10:
            return 0.0, odds, "Insufficient data", 0.0

        # Convert odds to floats (if not already done)
        odds = [float(o) for o in odds]

        # Net change (start to current)
        net_change = odds[0] - odds[-1] #corrected for latest first.
        trend = "-" if net_change < 0 else "+" if net_change > 0 else "="

        # Largest drop from any peak to subsequent trough, ignoring sharp drops
        max_drop = 0
        for i in range(len(odds)):
            for j in range(i + 1, len(odds)):
                drop = odds[i] - odds[j]
                # Ignore sharp drops (e.g., drops larger than 1.0)
                if drop > max_drop and drop <= 1.0: #adjust 1.0 to your needs.
                    max_drop = drop

        return net_change

    def get_top_drops(self, parent_match_id):
        """Analyze odds for a match and print top 3 dropping markets."""
        results = []
        data = self.redis.get(parent_match_id)
        
        if not data:
            #print(f"No data found for match ID: {parent_match_id}")
            return []

        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print(f"Invalid JSON data for match ID: {parent_match_id}")
            return []

        for sub_type in data:
            odds_list = sub_type.get('odds', [])
            for odd in odds_list:
                odd['parent_match_id'] = parent_match_id
                if odd.get('sport_id') != 14 or float(odd.get('odd_value')) > 2.0:
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
                net_change = self.analyze_market(odds)
                new_odd = {                    
                    "sub_type_id": sub_type.get('sub_type_id'),
                    "bet_pick": odd.get('odd_key'), #team
                    "odd_value": odd.get('odd_value'),
                    "outcome_id": odd.get('outcome_id'),
                    "sport_id": odd.get('sport_id'),
                    "special_bet_value": odd.get('special_bet_value'),
                    "parent_match_id": parent_match_id,
                    "bet_type": 8
                }
                results.append((new_odd, net_change))
        
        if not results:
            #print(f"No valid odds data for match ID: {parent_match_id}")
            return []

        # Sort by net change (most negative = most dropping)
        top_3 = sorted(results, key=lambda x: x[1])[:3]
        
        top_drops = [odd for odd, _ in top_3]
        
        return top_drops  # Return for potential further use

    def auto_bet(self, data):
        try:
            composite_betslips = [] 
            betslips = []
            total_odd = 1
            min_odd = 2.0
            for betslip in data:    
                betslips.append(betslip)
                total_odd *= float(betslip.get('odd_value'))                                            
                composite_betslip = {
                    'total_odd': total_odd,
                    'betslips': betslips
                }
                if total_odd >= min_odd:
                    print(total_odd)
                    composite_betslips.append(composite_betslip)
                    betslips = []
                    total_odd = 1
                    composite_betslip = None 

            if len(composite_betslips) > 0:                        
                balance, bonus = self.betika.get_balance()
                stake = 1
                if (balance+bonus) >= stake:
                    for cb in composite_betslips:
                        ttl_odd = cb['total_odd']
                        slips = cb['betslips']
                        print(f'TOTAL ODD: {ttl_odd}')
                        self.betika.place_bet(slips, ttl_odd, stake)
                        time.sleep(2)
        except Exception as e:
            print(f"Error in auto_bet: {e}")
                    
        
    def __call__(self):
        """Run analysis for all live matches concurrently."""
        live_match_ids = Stats().get_live_match_ids()
        if not live_match_ids:
            print("No live matches found.")
            return
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks for each match ID
            futures = [executor.submit(self.get_top_drops, parent_match_id) for parent_match_id in live_match_ids]
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
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [
                executor.submit(Stats()),
                executor.submit(PredictAndBet())
            ]
            
            concurrent.futures.wait(threads)
        
        time.sleep(60)