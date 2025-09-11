
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
            market = datum.get('name')
            markets.append(market)
        start_time = meta.get('start_time') 
        
        if datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date():
            # Define the query structure as a dictionary for cleaner JSON handling
            query_dict = {
                "instruction": f"Analyze the following match using ALL available data from the internet including tweets, bookmarkers data, team histories, team forms, etc and return the probability percentage of the highest most probable outcome using these markets {markets}. Respond with ONLY the JSON object, with no additional text, prose, or explanation. The output must strictly adhere to the provided JSON schema for the 'expected_output_schema'.",
                "match_details": meta,
                "expected_output_schema": {
                    "type": "object",
                    "properties": {
                        "parent_match_id": {
                            "type": "string",
                            "description": "Unique identifier for the match, as provided in the input meta['parent_match_id']"
                        },
                        "match_id": {
                            "type": "string",
                            "description": "Also Unique identifier for the match, as provided in the input meta['match_id']"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Match Start Time, as provided in the input meta['start_time']"
                        },
                        "home_team": {
                            "type": "string",
                            "description": "Home Team, as provided in the input meta['home_team']"
                        },
                        "away_team": {
                            "type": "string",
                            "description": "Away Team, as provided in the input meta['away_team']"
                        },
                        "overall_prob": {
                            "type": "integer",
                            "pattern": "^(100|[1-9][0-9]?|[0-9])$",
                            "description": "The probability percentage (0-100) as an integer."
                        },
                        "prediction": {
                            "type": "string",
                            "description": "The subtype name as provided in the input data[i]['name']"
                        },
                        "bet_pick": {
                            "type": "string",
                            "description": "The predicted outcome display value as provided in the input data[i]['odds'][i]['odd_key']"
                        }
                    }
                }
            }
            
            # Convert to JSON string with proper formatting
            query = json.dumps(query_dict, indent=4)
            return query
    
    def clean_match(self, match):
        if match:
            if int(match["sub_type_id"]) == 68: #1ST HALF - TOTAL
                match["prediction"] = "TOTAL"
                match["sub_type_id"] = "18" 
                match["bet_pick"] = "over 2.5"
                match["special_bet_value"] = "total=2.5"                  
                match["odd"] = 1 + (float(match["odd"]) - 1) * 3           
        
        return match

    def predict_match(self, parent_match_id):   
        try:     
            query = self.prepare_query(parent_match_id)
            if query:
                response = self.grok.get_response(query).replace('```json', '').strip('```')
                filtered_match = json.loads(response)
                predicted_match = filtered_match if filtered_match["odd"] >= 1.10 and filtered_match["overall_prob"] >= 80 else None

                #if int(predicted_match["sub_type_id"]) in [1, 14, 45, 105] or
                if int(predicted_match["sub_type_id"]) in [45, 105] or int(predicted_match["outcome_id"]) in [10, 11, 13] or "&" in predicted_match["bet_pick"]:
                    predicted_match = None
                
                return self.clean_match(predicted_match)
            else:
                return None
        except Exception as e:
            return None
                 
    def __call__(self):
        upcoming_match_ids = [56720817]
        
        for parent_match_id in upcoming_match_ids:
            predicted_match = self.predict_match(parent_match_id)
            if predicted_match:
                print(predicted_match)
                # self.db.insert_matches([predicted_match]) 
                time.sleep(6)
                
if __name__ == "__main__":
    Predict()()
    
