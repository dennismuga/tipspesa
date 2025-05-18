
import concurrent.futures

from utils.corners import Corners
from utils.helper import Helper
from utils.multi_goal import MultiGoal
from utils.multi_goal_over_under import MultiGoalOverUnder


class Predict:
    """
        main class
    """
    def __init__(self):
        self.multi_goal = MultiGoal()
        self.multi_goal_over_under = MultiGoalOverUnder()
        self.corners = Corners()
        self.helper = Helper()
                  
    def __call__(self):
        upcoming_match_ids = self.helper.get_upcoming_match_ids()
        predicted_matches = []
        # Use ThreadPoolExecutor to spawn a thread for each match
        with concurrent.futures.ThreadPoolExecutor() as executor:
            #threads = [executor.submit(self.multi_goal.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]
            threads = [executor.submit(self.multi_goal_over_under.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]

            # Wait for all threads to finish
            concurrent.futures.wait(threads)
            for thread in threads:
                try:
                    match = thread.result()
                    if match:
                        predicted_matches.append(match)
                except Exception as e:
                    print(f"Error processing match: {e}")

            self.helper.auto_bet(predicted_matches)

if __name__ == "__main__":
    Predict()()