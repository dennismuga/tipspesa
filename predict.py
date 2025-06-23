
import concurrent.futures
import json

from utils.corners import Corners
from utils.corners_beta import CornersBeta
from utils.gemini import Gemini
from utils.helper import Helper
from utils.multi_goal import MultiGoal
from utils.multi_goal_over_under import MultiGoalOverUnder
from utils.postgres_crud import PostgresCRUD

class Predict:
    """
        main class
    """
    def __init__(self):
        self.multi_goal = MultiGoal()
        self.multi_goal_over_under = MultiGoalOverUnder()
        self.corners = Corners()
        self.gemini = Gemini()
        self.db = PostgresCRUD()
        self.corners_beta = CornersBeta()
                        
    def __call__(self):
        upcoming_match_ids = Helper().get_upcoming_match_ids()
        predicted_matches = []
        # Use ThreadPoolExecutor to spawn a thread for each match
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.multi_goal_over_under.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]
            threads_2 = [executor.submit(self.corners_beta.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]

            # Wait for all threads to finish
            concurrent.futures.wait(threads + threads_2)  # Wait for both threads and threads_2

            # Process threads (multi_goal_over_under predictions)
            for thread in threads:
                try:
                    match = thread.result()
                    if match:
                        predicted_matches.append(match)
                except Exception as e:
                    print(f"Error processing match from multi_goal_over_under: {e}")

            # Process threads_2 (corners_beta predictions)
            for thread in threads_2:
                try:
                    match = thread.result()
                    if match:
                        # Check if parent_match_id already exists in predicted_matches
                        if not any(m["parent_match_id"] == match["parent_match_id"] for m in predicted_matches):
                            predicted_matches.append(match)
                except Exception as e:
                    print(f"Error processing match from corners_beta: {e}")

            if len(predicted_matches) > 0:
                query = self.gemini.prepare_query(predicted_matches)
                response = self.gemini.get_response(query).replace('```json', '').strip('```')
                filtered_matches = json.loads(response)
                beta_matches = [
                    { **match, "overall_prob": int(f_m["probability"]) }
                    for match in predicted_matches
                    for f_m in filtered_matches
                    if match["parent_match_id"] == f_m["match_id"] and int(f_m["probability"]) >= 75
                ]
                print(beta_matches)
                self.db.insert_matches(beta_matches)           
                
if __name__ == "__main__":
    Predict()()
