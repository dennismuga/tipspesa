
import json
from pathlib import Path
from utils.betika import Betika
from utils.gemini import Gemini

import json
from pathlib import Path

from utils.postgres_crud import PostgresCRUD

def compose_question(events):     
    question = {
        "instructions": "Predict the outcome of the following football matches using available web data, including team form and Twitter feeds.For each market, provide a probability percentage. Save the results as a JSON array of objects, where each object represents a match in predictions.json file." ,
        "matches": events,  # Use the 'events' list here
        "format": {
            "type": "json",
            "structure": [
                {
                    "parent_match_id": "string",
                    "home_team": "string",
                    "away_team": "string",
                    "predictions": {
                        "1X2":{
                            "1": "probability",
                            "X": "probability",
                            "2": "probability"
                        },       
                        "TOTAL GOALS":{
                            "OVER 2.5": "probability",
                            "OVER 1.5": "probability"
                        },       
                        "BOTH TEAMS TO SCORE":{
                            "YES": "probability",
                            "NO": "probability"
                        },                        
                        "TOTAL CORNERS":{
                            "OVER 10.5": "probability",
                            "OVER 9.5": "probability",
                            "OVER 8.5": "probability",
                            "OVER 7.5": "probability"
                        }
                    }
                }
            ] 
        },
        "data_sources": [
            "Recent match results for the last 7 games, weighted by recency",
            "League standings",
            "Head-to-head records for the last 5 meetings",
            "Player statistics: goals and assists for key players this season, current injuries/suspensions",
            "Team news from official team websites and reputable sports news sources",
            "Expert predictions from ESPN and Sky Sports",
            "Weather forecast for the match location",
            "Home form for Team A, away form for Team B",
            "Tweets from official team accounts and reputable sports journalists covering the league",
            "Aggregate fan sentiment from Twitter (treat with caution)",
            "Team information from Wikipedia",
            "Player transfer data from Transfermarkt"
        ]
    }

    return question

def generate_questions():
    questions = []        
    total = 1001
    limit = 1000
    page = 1
    
    while limit*page < total:
        total, page, events = Betika().get_events(limit, page)
         
        question = compose_question(events)  
        
        # Write data to file
        with open("questions.json", 'w', encoding='utf-8') as f:
            json.dump(question, f, indent=4, ensure_ascii=False)
        #questions.append(question)
        
    return questions

def save_predictions():
    # Load JSON data from a file
    with open('predictions.json', 'r') as file:
        data = json.load(file)
        added_parent_match_ids = set()
        for datum in data:
            parent_match_id= datum.get('parent_match_id')
            predictions = datum.get('predictions')
            winner = predictions.get('1X2')
            total_goals = predictions.get('TOTAL GOALS')
            btts = predictions.get('BOTH TEAMS TO SCORE')
            total_corners = predictions.get('TOTAL CORNERS')
            predictions = {**winner, **total_goals, **btts, **total_corners}
            for key in predictions:
                prediction = int(predictions.get(key).replace('%',''))
                if (prediction>=85 and key in ['OVER 1.5', 'OVER 7.5']) or (prediction>=80 and key in ['OVER 2.5', 'OVER 8.5', 'YES']) or (prediction>=75 and key in ['OVER 9.5', '1', 'X', '2']) or (prediction>=70 and key in ['OVER 10.5']):  
                    url = f'https://api.betika.com/v1/uo/match?parent_match_id={parent_match_id}'
                    match_details = Betika().get_data(url)
                    data = match_details.get('data')
                    if data:
                        for d in data:
                            sub_type_id = d.get('sub_type_id')
                            if sub_type_id in ["1", "18", "29", "166"]:
                                odds = d.get('odds')
                                for odd in odds:
                                    odd_value = odd.get('odd_value')
                                    if key == odd.get('display') and parent_match_id not in added_parent_match_ids:
                                        bet_pick = 'GG' if key == 'YES' else odd.get('odd_key')
                                        print(f"{datum.get('home_team')} vs {datum.get('away_team')} = {bet_pick} [x{odd_value}]")                                            
                                        match = {
                                            'match_id': match_details.get('meta').get('match_id'),
                                            'start_time': match_details.get('meta').get('start_time'),
                                            'home_team': datum.get('home_team'),
                                            'away_team': datum.get('away_team'),
                                            'prediction': bet_pick,
                                            'odd': odd_value,
                                            'overall_prob': prediction,
                                            'parent_match_id': parent_match_id,
                                            'sub_type_id': sub_type_id,
                                            'bet_pick': bet_pick,
                                            'special_bet_value': odd.get('special_bet_value'),
                                            'outcome_id': odd.get('outcome_id')
                                        }
                                        PostgresCRUD().insert_match(match)
                    
def gemini_predict():
    try:
        file_path = Path('predictions.json')
        # Delete the file if it exists
        # if file_path.exists():
        #     file_path.unlink()

        # Initialize an empty list to store all responses
        all_data = []

        for question in generate_questions():
            response = Gemini().get_response(question)
            # Clean and parse the JSON response
            cleaned_response = response.replace('```json', '').replace('```', '').strip()
            data = json.loads(cleaned_response)
            print(f"Added {len(data)} matches...")
            
            # Append the current data to all_data list
            all_data.extend(data)  # Use extend because data is already a list
            
            # Write updated data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
        print(f"Done Predicting. Total = {len(all_data)} matches...")    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except FileNotFoundError as e:
        print(f"Error accessing file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    #gemini_predict()
    save_predictions()