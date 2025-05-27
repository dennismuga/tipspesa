
import concurrent.futures
import json

from utils.corners import Corners
from utils.corners_beta import CornersBeta
from utils.gemini import Gemini
from utils.helper import Helper
from utils.multi_goal import MultiGoal
from utils.multi_goal_over_under import MultiGoalOverUnder
from utils.postgres_crud import PostgresCRUD

class Autobet:
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
    
    def bet(self, profile):
        phone = profile[0]
        password = profile[1]
        profile_id = profile[2]
        matches = self.db.fetch_unplaced_matches(profile_id)
        helper = Helper(phone, password)
        helper.auto_bet(profile_id, matches, 5)
        helper.auto_bet(profile_id, matches, 10)
        helper.auto_bet(profile_id, matches, 15)
        helper.auto_bet(profile_id, matches, 20)
                    
    def __call__(self):
        # Use ThreadPoolExecutor to spawn a thread for each profile
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.bet, profile) for profile in self.db.get_active_profiles()]

            # Wait for all threads to finish
            concurrent.futures.wait(threads)
                
if __name__ == "__main__":
    Autobet()()
