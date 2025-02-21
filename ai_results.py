
import json

from utils.gemini import Gemini
from utils.postgres_crud import PostgresCRUD

if __name__ == '__main__':
    try:
        events = PostgresCRUD().fetch_matches('-1', '=', '') 
        question = f"Use Google Search and get match result for these games: "
        for event in events:
            kickoff = event[1]
            home = event[2]
            away = event[3]
            prediction = event[4]
            question = f"""
                {question} {home} vs {away} played on {kickoff} EAT.
            """
            
        print(f'{question} Just scrap match  result e.g 1-2')
        
            # response = Gemini().get_response(question)
            # print(response)
            # prediction = event['prediction']
            # request_json = {
            #     "instructions": f"Format this string to json {response}. match_id={event['match_id']} Also give me the status of my earlier prediction = {prediction} whether WON/LOST depending on the actual outcome of the match",
            #     "format": {
            #         "type": "json",
            #         "structure": {
            #             "match_id": "string",
            #             "home_results": "integer",
            #             "away_results": "integer",
            #             "status": "string"
            #         }
            #     }
            # }
            # question = json.dumps(request_json)
            # print(question)
            # response = Gemini().get_response(question)
            # cleaned_response = response.replace('```json', '').replace('```', '').strip()
            # datum = json.loads(cleaned_response)  
            # print(datum)
            #PostgresCRUD().update_match_results(datum.get('match_id'), datum.get('home_results'), datum.get('away_results'), datum.get('status'))
                
        print(f"Done Fetching Results...")    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except FileNotFoundError as e:
        print(f"Error accessing file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")