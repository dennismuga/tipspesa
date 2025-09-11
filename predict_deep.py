
from datetime import datetime
import json
import time

from utils.betika import Betika
from utils.grok import Grok

class Predict:
    """
        main class
    """
    def __init__(self):
        self.grok = Grok()
        self.betika = Betika()
    
    def prepare_query(self, parent_match_id):
        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
        match_details = self.betika.get_data(url)
        if not match_details:
            return None            
        meta = match_details.get('meta') 
        markets = [] 
        for datum in match_details.get('data', []):
            if int(datum.get('sub_type_id')) in [1, 10, 29, 18]: # 1X2, DOUBLE CHANCE, BOTH TEAMS TO SCORE, TOTAL
                market = {
                    "sub_type_id": datum.get('sub_type_id'),
                    "prediction": datum.get('name'),
                    "odds": [
                        { 
                            "odd_key": odd.get('odd_key'),
                            "odd_value": odd.get('odd_value'),
                            "special_bet_value": odd.get('special_bet_value') ,
                            "outcome_id": odd.get('outcome_id') 
                        } for odd in datum.get('odds', [])]
                }            
            
                markets.append(market)
        start_time = meta.get('start_time') 
        
        if datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date():
            # Define the query structure as a dictionary for cleaner JSON handling
            query_dict = {
                "instruction": "Analyze the following match using ALL available data from the internet including tweets, bookmarkers data, team histories, team forms, etc and return the probability percentage of the highest most probable outcome using the provided markets. Respond with ONLY the JSON object, with no additional text, prose, or explanation. The output must strictly adhere to the provided JSON schema for the 'expected_output_schema'.",
                "match_details": meta,
                "markets": markets,
                "expected_output_schema": {
                    "type": "object",
                    "properties": {
                        "parent_match_id": {
                            "type": "string",
                            "description": "Unique identifier for the match, as provided in the input match_details['parent_match_id']"
                        },
                        "match_id": {
                            "type": "string",
                            "description": "Also Unique identifier for the match, as provided in the input match_details['match_id']"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Match Start Time, as provided in the input match_details['start_time']"
                        },
                        "home_team": {
                            "type": "string",
                            "description": "Home Team, as provided in the input match_details['home_team']"
                        },
                        "away_team": {
                            "type": "string",
                            "description": "Away Team, as provided in the input match_details['away_team']"
                        },
                        "overall_prob": {
                            "type": "integer",
                            "pattern": "^(100|[1-9][0-9]?|[0-9])$",
                            "description": "The probability percentage (0-100) as an integer."
                        },
                        "sub_type_id": {
                            "type": "string",
                            "description": "Unique identifier for the picked market, as provided in the input markets[i]['sub_type_id']"
                        },
                        "prediction": {
                            "type": "string",
                            "description": "The prediction name as provided in the input markets[i]['prediction']"
                        },
                        "bet_pick": {
                            "type": "string",
                            "description": "The predicted outcome display value as provided in the input markets[i]['odd_key']"
                        },
                        "odd": {
                            "type": "float",
                            "description": "The predicted outcome odd value as provided in the input markets[i]['odd_value']"
                        },
                        "special_bet_value": {
                            "type": "string",
                            "description": "The predicted outcome special_bet_value value as provided in the input markets[i]['special_bet_value']"
                        },
                        "outcome_id": {
                            "type": "string",
                            "description": "The predicted outcome outcome_id value as provided in the input markets[i]['outcome_id']"
                        }
                    }
                }
            }
            
            # Convert to JSON string with proper formatting
            query = json.dumps(query_dict, indent=4)
            return query
    
    def predict_match(self, parent_match_id):   
        try:     
            query = self.prepare_query(parent_match_id)
            if query:
                response = self.grok.get_response(query)
                filtered_match = json.loads(response)
                predicted_match = filtered_match if filtered_match["odd"] >= 1.10 and filtered_match["overall_prob"] >= 80 else None
                
                return predicted_match
            else:
                return None
        except Exception as e:
            return None
    
    def get_upcoming_match_ids(self, live=False):    
        total = 1001
        limit = 1000
        page = 1
        matches_ids = set()
        while limit*page < total:
            total, page, events = self.betika.get_events(limit, page, live)
            
            for event in events:
                parent_match_id = event.get('parent_match_id')
                matches_ids.add(parent_match_id)
        
        return matches_ids
              
    def __call__(self):
        upcoming_match_ids = self.get_upcoming_match_ids(live=False)
        
        for parent_match_id in upcoming_match_ids:
            predicted_match = self.predict_match(parent_match_id)
            if predicted_match:
                print(predicted_match)
                # self.db.insert_matches([predicted_match]) 
                time.sleep(6)
                
if __name__ == "__main__":
    Predict()()
    
