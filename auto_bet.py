
import concurrent.futures

from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class Autobet:
    """
        main class
    """
    def __init__(self):
        self.db = PostgresCRUD()
    
    def bet(self, profile):
        phone = profile[0]
        password = profile[1]
        profile_id = profile[2]
        matches = self.db.fetch_unplaced_matches(profile_id)
        helper = Helper(phone, password)
        #helper.auto_bet(profile_id, matches, 1)
        # helper.auto_bet(profile_id, matches, 2)
        #helper.auto_bet(profile_id, matches, 3)
        #helper.auto_bet(profile_id, matches, 4)
        helper.auto_bet(profile_id, matches, 5)
                    
    def __call__(self):
        # Use ThreadPoolExecutor to spawn a thread for each profile
        with concurrent.futures.ThreadPoolExecutor() as executor:
            threads = [executor.submit(self.bet, profile) for profile in self.db.get_active_profiles()]

            # Wait for all threads to finish
            concurrent.futures.wait(threads)
                
if __name__ == "__main__":
    Autobet()()






