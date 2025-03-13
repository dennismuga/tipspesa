
import concurrent.futures, time
from datetime import datetime, timedelta

from v2.predict_and_bet import PredictAndBet
from v2.stats import Stats

start_time = datetime.now()
end_time = start_time + timedelta(hours=3)
    
def update_stats():
    while datetime.now() < end_time:
        Stats()()
        time.sleep(120)

def predict_and_bet():
    while datetime.now() < end_time:
        PredictAndBet()()
        time.sleep(300)

if __name__ == '__main__':
    # Use ThreadPoolExecutor to spawn a thread for each match
    with concurrent.futures.ThreadPoolExecutor() as executor:
        threads = [
            executor.submit(update_stats),
            executor.submit(predict_and_bet)
        ]

        # Wait for all threads to finish
        concurrent.futures.wait(threads)