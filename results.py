import time
import concurrent.futures
import logging
from typing import List, Tuple
from utils.betika import Betika
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD

# Set up logging for GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Results:
    def __init__(self):
        self.betika = Betika()
        self.helper = Helper()
        self.db = PostgresCRUD()

    def get_status(self, home_score: int, away_score: int, bet_pick: str) -> str:
        """Determine the match status based on scores and bet pick."""
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
        if '-' in bet_pick:
            bet_pick = bet_pick.split('-')
            if (home_score+away_score) not in range(int(bet_pick[0]), int(bet_pick[1])+1):
                return 'LOST'
        return 'WON'
    

    def process_match(self, match: object) -> Tuple[str, int, int, str]:
        """
        Process a single match: fetch details, calculate status, and update DB.
        Returns (match_id, home_score, away_score, status) for logging.
        """
        try:
            match_details = self.betika.get_match_details(match.parent_match_id, live=True)
            if not match_details:
                logger.info('No match details for match %s', match.match_id)
                return match.match_id, None, None, 'No match details'

            meta = match_details.get("meta", {})
            match_time = meta.get("match_time") #22:50
            current_score = meta.get("current_score")
            if match_time and current_score:
                mins = int(match_time.split(':')[0])
                scores = current_score.split(':')
                home_score, away_score = int(scores[0]), int(scores[1])           
                status = self.get_status(home_score, away_score, match.bet_pick)
                status = status if mins >= 90 or ('over' in match.bet_pick and status == 'WON') else f"{mins if mins > 0 else 'HT'}'"
                if home_score is not None and away_score is not None:
                    logger.info('%s vs %s [%s] = %d:%d - %s', match.home_team, match.away_team, match.bet_pick, home_score, away_score, status)
                
                self.db.update_match_results(match.match_id, home_score, away_score, status)
                return match.match_id, home_score, away_score, status
            else:
                # logger.info('No current score for match %s vs %s', match.home_team, match.away_team)
                return match.match_id, None, None, None
        except Exception as e:
            logger.error('Error processing match %s: %s', match.match_id, e)
            return match.match_id, None, None, 'Error: %s' % e

    def __call__(self, matches) -> List[Tuple[str, int, int, str]]:
        """
        Fetch matches and process them concurrently.
        Returns list of (match_id, home_score, away_score, status) for each match.
        """

        results = []
        # Use ThreadPoolExecutor for concurrent processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map process_match to each match concurrently
            futures = [executor.submit(self.process_match, match) for match in matches]
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    match_id, home_score, away_score, status = result
                    if home_score is not None and away_score is not None:
                        results.append(result)
                except Exception as e:
                    logger.error('Error in concurrent processing: %s', e)
                    results.append((None, None, None, 'Error: %s' % e))

        return results

def main():
    """Run forever, processing matches every 1 minute."""
    results_processor = Results()
    matches = results_processor.helper.fetch_matches('', '=', '', limit=1000)
    logger.info('Fetched %d matches to process', len(matches))
    while True:
        logger.info('Starting new cycle')
        try:
            results = results_processor(matches)
            logger.info('Cycle completed with %d matches updated', len(results))
        except Exception as e:
            logger.error('Error in cycle: %s', e)
        logger.info('Sleeping for 1 minute')
        logger.info('--------------------------------------------------------------')
        time.sleep(60)

if __name__ == "__main__":
    main()
