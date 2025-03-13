
import concurrent.futures, time

from v2.predict_and_bet import PredictAndBet
from v2.stats import Stats
    
def update_stats():
    while True:
        Stats()()
        time.sleep(120)

def predict_and_bet():
    while True:
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