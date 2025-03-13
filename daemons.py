
import concurrent.futures, time

from v2.predict_and_bet import PredictAndBet
from v2.stats import Stats
    
def update_stats():
    i = 0
    while True:
        Stats()()
        if i>0 and i%2 == 0:
           PredictAndBet()()
        i += 1
        time.sleep(120)

if __name__ == '__main__':
    # Use ThreadPoolExecutor to spawn a thread for each match
    with concurrent.futures.ThreadPoolExecutor() as executor:
        threads = [
            executor.submit(update_stats)
            #executor.submit(predict_and_bet)
        ]

        # Wait for all threads to finish
        concurrent.futures.wait(threads)