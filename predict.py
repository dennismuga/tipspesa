
import concurrent.futures

from utils.corners import Corners
from utils.helper import Helper
from utils.over_under import OverUnder


class Predict:
    """
        main class
    """
    def __init__(self):
        self.over_under = OverUnder()
        self.corners = Corners()
        self.helper = Helper()
                  
    def __call__(self):
        upcoming_match_ids = self.helper.get_upcoming_match_ids()
        predicted_matches = []
        # Use ThreadPoolExecutor to spawn a thread for each match
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.over_under.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]
            threads += [executor.submit(self.corners.predict_match, parent_match_id) for parent_match_id in upcoming_match_ids]

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