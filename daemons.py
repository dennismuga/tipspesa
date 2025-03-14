
import concurrent.futures, time

from v2.predict_and_bet import PredictAndBet
from v2.stats import Stats

if __name__ == '__main__':
    i = 0
    while True:
        Stats()()
        if i%2 == 0:
           print("predicting... ") 
           PredictAndBet()()
        i += 1
        time.sleep(120)
        print("sleeping... ") 
