
from utils.betika import Betika

class Withdraw():
    def __init__(self):
        self.betika = Betika()

    def __call__(self):
        balance, bonus = self.betika.get_balance()
        amount = balance/2 
        if amount >= 50:
            self.betika.withdraw(amount)

if __name__ == "__main__":
    Withdraw()()