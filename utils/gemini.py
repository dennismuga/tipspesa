import json, os
from datetime import datetime
from dotenv import load_dotenv
from google import genai

load_dotenv()

class Gemini():
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
    def get_response(self, query):
        return self.client.models.generate_content(
            model= os.getenv('GEMINI_MODEL'), 
            contents=str(query)
        ).text
        
    def prepare_query(self, matches):
        # Convert matches to trimmed format using list comprehension
        trimmed_matches = [
            {
                "match_id": match["parent_match_id"],
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "prediction": {match["prediction"]} + " goals" if match["sub_type_id"] == 18 else " corners" if match["sub_type_id"] == 166 else "",
                "match_date": datetime.strptime(match["start_time"], '%Y-%m-%d %H:%M:%S').date().isoformat() 
            }
            for match in matches
        ]

        # Define the query structure as a dictionary for cleaner JSON handling
        query_dict = {
            "instruction": "Analyze the following matches and return the probability percentage of the outcome as predicted. Respond with ONLY the JSON array, with no additional text, prose, or explanation. The output must strictly adhere to the provided JSON schema for the 'expected_output_schema'.",
            "matches": trimmed_matches,
            "expected_output_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "match_id": {
                            "type": "string",
                            "description": "Unique identifier for the match, as provided in the input."
                        },
                        "prediction": {
                            "type": "string",
                            "enum": ["over 1.5 goals", "under 1.5 goals"],
                            "description": "The predicted outcome for 1.5 goals."
                        },
                        "probability": {
                            "type": "string",
                            "pattern": "^(100|[1-9][0-9]?|[0-9])$",
                            "description": "The probability percentage (0-100) as a string."
                        }
                    },
                    "required": ["match_id", "prediction", "probability"]
                }
            }
        }

        # Convert to JSON string with proper formatting
        query = json.dumps(query_dict, indent=4)
        return query