
from datetime import datetime, time
import json

from utils.betika import Betika
from utils.corners import Corners
from utils.gemini import Gemini
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class PredictAi:
    """
        main class
    """
    def __init__(self):
        self.corners = Corners()
        self.gemini = Gemini()
        self.db = PostgresCRUD()
        self.betika = Betika()
    
    def prepare_query(self, parent_match_id):
        url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
        match_details = self.betika.get_data(url)
        if not match_details:
            return None            
        meta = match_details.get('meta')   
        start_time = meta.get('start_time') 
        
        if (datetime.now().date() == datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").date() and datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").time() > time(12, 0)):
            # Define the query structure as a dictionary for cleaner JSON handling
            query_dict = {
                "instruction": "Analyze the following match and return the probability percentage of the highest most probable outcome from the available markets in data array. Respond with ONLY the JSON object, with no additional text, prose, or explanation. The output must strictly adhere to the provided JSON schema for the 'expected_output_schema'.",
                "match_details": match_details,
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
                            "description": "The probability percentage (0-100) as a integer."
                        },
                        "sub_type_id": {
                            "type": "string",
                            "description": "Unique identifier for the picked market, as provided in the input data[i]['sub_type_id']"
                        },
                        "prediction": {
                            "type": "string",
                            "description": "The subtype name as provided in the input data[i]['name']"
                        },
                        "bet_pick": {
                            "type": "string",
                            "description": "The predicted outcome display value as provided in the input data[i]['odds'][i]['odd_key']"
                        },
                        "odd": {
                            "type": "float",
                            "description": "The predicted outcome odd value as provided in the input data[i]['odds'][i]['odd_value']"
                        },
                        "special_bet_value": {
                            "type": "string",
                            "description": "The predicted outcome special_bet_value value as provided in the input data[i]['odds'][i]['special_bet_value']"
                        },
                        "outcome_id": {
                            "type": "string",
                            "description": "The predicted outcome outcome_id value as provided in the input data[i]['odds'][i]['outcome_id']"
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
                response = self.gemini.get_response(query).replace('```json', '').strip('```')
                print(response)
                filtered_match = json.loads(response)
                filtered_match = None if filtered_match["sub_type_id"] in ["18"] else filtered_match
                predicted_match = filtered_match if filtered_match["odd"] >=1.1 and filtered_match["overall_prob"]>=75 else None
                predicted_match = None if ' or ' in predicted_match["bet_pick"] and ' draw ' not in predicted_match["bet_pick"] else predicted_match
                predicted_match = None if predicted_match["bet_pick"] in ['under 2.5', 'under 3.5', '1x2', 'TOTAL'] else predicted_match
                # predicted_match = filtered_match if ((filtered_match["sub_type_id"] in [24,29,105,548] or (filtered_match["sub_type_id"]==18)) and filtered_match["overall_prob"]>=75 and 'under ' not in filtered_match["bet_pick"] and ' or ' not in filtered_match["bet_pick"] ) else None
                unsure_match = filtered_match if (filtered_match["overall_prob"]>=75 and filtered_match["sub_type_id"] == 10 ) else None
                return self.corners.predict_match(predicted_match) if unsure_match else predicted_match
            else:
                return None
        except Exception as e:
            return None
                 
    def __call__(self):
        upcoming_match_ids = Helper().get_upcoming_match_ids()
        
        for parent_match_id in upcoming_match_ids:
            predicted_match = self.predict_match(parent_match_id)
            if predicted_match:
                print(predicted_match)
                self.db.insert_matches([predicted_match]) 
                
if __name__ == "__main__":
    PredictAi()()
