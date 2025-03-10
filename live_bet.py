# Description: This script is used to predict the outcome of live matches
import concurrent.futures, time, uuid
from apscheduler.schedulers.background import BackgroundScheduler
from itertools import combinations
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np

from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

class Stats():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()
    
    def get_live_match_ids(self):   
        limit = 10 
        total = limit + 1
        page = 1
        matches_ids = set()
        #while limit*page < total:
        total, page, events = self.betika.get_events(limit, page, live=True)
        
        for event in events:
            parent_match_id = event.get('parent_match_id')
            matches_ids.add(parent_match_id)
        
        return matches_ids
        
    def save_match_odds(self, parent_match_id):
        match_details = self.betika.get_match_details(parent_match_id, live=True)
        for sub_type in match_details:
            sub_type_id = sub_type['sub_type_id']
            if sub_type['market_active'] == 1:
                for odd in sub_type['odds']:        
                    self.db.insert_odds(
                        str(uuid.uuid4()), 
                        parent_match_id,
                        sub_type_id, 
                        odd['display'], 
                        odd['odd_value'], 
                        odd['outcome_id'], 
                        odd['sport_id'], 
                        odd['special_bet_value'], 
                        bet_type=8
                    )
            else:
                self.db.delete_inactive_odds(parent_match_id, sub_type_id)

    def __call__(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            live_match_ids = self.get_live_match_ids()
            threads = [executor.submit(self.save_match_odds, parent_match_id) 
                       for parent_match_id in live_match_ids]
            threads.append(executor.submit(self.db.delete_expired_odds, live_match_ids))
            
            results = concurrent.futures.wait(threads)

class PredictAndBet():
    def __init__(self):
        self.db = PostgresCRUD()
        self.betika = Betika()
        self.model = RandomForestClassifier()
        
    def extract_features(self, match_id, market, stats):
        odds = self.db.get_odds_history(match_id, market)
        if len(odds) < 2:
            return [0, 0, 0, stats.get("shots_on_target", 0)]
        total_drop = ((odds[0] - odds[-1]) / odds[0]) * 100 if odds[0] > 0 else 0
        rate = total_drop / (len(odds) - 1)
        accel = np.mean(np.diff([((odds[i] - odds[i+1]) / odds[i] if odds[i] != 0 else 0) * 100 for i in range(len(odds)-1)])) if len(odds) > 2 else 0        
        
        return [total_drop, rate, accel, stats.get("shots_on_target", 0)]

    def build_multibet_candidates(self):        
        # Fetch all active odds
        active_odds = self.db.get_active_odds()
        live_matches = {}
        for row in active_odds:
            match_id = row[1]
            market = row[3]
            
            # Initialize match entry if it doesn’t exist
            if match_id not in live_matches:
                live_matches[match_id] = {
                    "odds": {},
                    "stats": self.betika.get_match_stats(match_id, live=True)
                }
                
            # Store full odds row under bet_pick (market)
            live_matches[match_id]["odds"][market] = {
                "parent_match_id": row[1],
                "sub_type_id": row[2],
                "bet_pick": row[3],
                "odd_value": row[4],
                "outcome_id": row[5],
                "sport_id": row[6],
                "special_bet_value": row[7],  # Handle null as empty string
                "bet_type": row[8]
            }

        # Build candidates with full odds data
        candidates = []
        for match_id, data in live_matches.items():
            for market, odds_data in data["odds"].items():
                features = self.extract_features(match_id, market, data["stats"])
                prob = 0.7 if features[0] > 20 else 0.5  # Fallback rule
                if prob > 0.7:
                    candidates.append({
                        "match_id": match_id,
                        "market": market,
                        "odds_data": odds_data,
                        "prob": prob
                    })
                    
        valid_multibets = []
        for r in range(1, min(6, len(candidates) + 1)):
            for combo in combinations(candidates, r):
                total_odds = 1.0
                for leg in combo:
                    total_odds *= float(leg["odds_data"]["odd_value"])
                if total_odds >= 3.0:
                    valid_multibets.append({
                        "legs": combo,
                        "total_odds": total_odds
                    })
        return valid_multibets

    # def place_multibet(self, multibet):
    #     legs = [
    #         {
    #             "parent_match_id": leg["odds_data"]["parent_match_id"],
    #             "sub_type_id": leg["odds_data"]["sub_type_id"],
    #             "bet_pick": leg["odds_data"]["bet_pick"],
    #             "odd_value": leg["odds_data"]["odd_value"],
    #             "outcome_id": leg["odds_data"]["outcome_id"],
    #             "sport_id": leg["odds_data"]["sport_id"],
    #             "special_bet_value": leg["odds_data"]["special_bet_value"],
    #             "bet_type": leg["odds_data"]["bet_type"]
    #         }
    #         for leg in multibet["legs"]
    #     ]
    #     your_autobet_class.place_bet(legs, amount=10)
    #     for leg in multibet["legs"]:
    #         self.db.insert_bet(
    #             leg["odds_data"]["parent_match_id"],
    #             leg["odds_data"]["bet_pick"],
    #             leg["odds_data"]["odd_value"],
    #             10 / len(multibet["legs"])
    #         )

    def __call__(self):
        multibets = self.build_multibet_candidates()
        if multibets:
            best_multibet = max(multibets, key=lambda x: x["total_odds"])
            print(best_multibet)
            #self.place_multibet(best_multibet)
            
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    #scheduler.add_job(Stats()(), 'interval', minutes=2) # Stats update job
    scheduler.add_job(PredictAndBet()(), "interval", minutes=2)  # Predict and bet job
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()