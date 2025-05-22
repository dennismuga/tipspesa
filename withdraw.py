
from utils.betika import Betika

class Withdraw():
    def __init__(self):
        self.betika = Betika()

    def __call__(self):
        balance, bonus = self.betika.get_balance()
        amount = int(balance/2) 
        if amount >= 50 and amount <= 300000:
            #self.betika.withdraw(amount)
            pass

if __name__ == "__main__":
    Withdraw()()
