
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

class Results:
    """
        main class
    """
    def __init__(self):
        self.betika = Betika()
        self.helper = Helper()
        self.db = PostgresCRUD()
        
    def get_status(self, home_score, away_score, bet_pick):
        if bet_pick == 'over 1.5' and home_score + away_score < 2:
            return 'LOST'
        if bet_pick == 'over 2.5' and home_score + away_score < 3:
            return 'LOST'
        if bet_pick == 'over 3.5' and home_score + away_score < 4:
            return 'LOST'
        if bet_pick == 'under 3.5' and home_score + away_score > 3:
            return 'LOST'
        if bet_pick == 'under 4.5' and home_score + away_score > 4:
            return 'LOST'
        if bet_pick == 'under 5.5' and home_score + away_score > 5:
            return 'LOST'
        else:
            return 'WON'
         
    def __call__(self):
        matches = self.helper.fetch_matches('', '=', '', limit=100)  
             
        for match in matches:
            match_details = self.betika.get_match_details(match.parent_match_id, live=True)
            meta = match_details["meta"]
            current_score = meta["current_score"] if "current_score" in meta else None
            if current_score:
                scores = current_score.split(':')
                status = self.get_status(int(scores[0]), int(scores[1]), match.bet_pick)
                print(scores, status)
                self.db.update_match_results(match.match_id, scores[0], scores[1], status)

if __name__ == "__main__":
    Results()()