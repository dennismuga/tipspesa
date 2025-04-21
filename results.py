
from datetime import datetime, timedelta

from utils.bbc import BBC
from utils.helper import Helper
from utils.livescore import LiveScore
from utils.postgres_crud import PostgresCRUD

class Results:
    """
        main class
    """
    def __init__(self):
        self.livescore = LiveScore()
        self.bbc = BBC()
        self.helper = Helper()
        self.db = PostgresCRUD()
    
    def check_match_results(self, home_team, away_team, result):
        # Split match team names into words
        home_words = home_team.lower().split()
        away_words = away_team.lower().split()
        
        # Check if any word from match.home_team is in result['home_team']
        home_match = any(len(word) > 3 and word in result['home_team'].lower() for word in home_words)
    
        # Check if any word (len > 3) from match.away_team is in result['away_team']
        away_match = any(len(word) > 3 and word in result['away_team'].lower() for word in away_words)
        
        # Return True only if both conditions are met
        return home_match and away_match
    
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
        # Get yesterday's date & Format as YYYYMMDD
        today = datetime.now()
        yesterday = today - timedelta(days=1)        

        yesterday_matches = self.helper.fetch_matches('-1', '=', '', limit=100)        
        # Combine results
        results = self.livescore.get_results(yesterday)
        results += self.bbc.get_results(today, yesterday)

        # Remove duplicates
        unique_results = {tuple(sorted(d.items())) for d in results}
        results = [dict(t) for t in unique_results]
        
        for match in yesterday_matches:
            for result in results:
                if self.check_match_results(match.home_team, match.away_team, result):
                    status = self.get_status(int(result['home_score']), int(result['away_score']), match.bet_pick)
                    print(result, status)
                    self.db.update_match_results(match.match_id, result['home_score'], result['away_score'], status)

if __name__ == "__main__":
    Results()()