
import concurrent.futures
from utils.betika import Betika
from utils.postgres_crud import PostgresCRUD

class Withdraw():
    def __init__(self):
        self.betika = Betika()
        self.db = PostgresCRUD()

    def withdraw(self, profile):
        phone = profile[0]
        password = profile[1]
        self.betika.login(phone, password)
        amount = int(self.betika.balance/3) 
        if amount >= 50 and amount <= 300000:
            self.betika.withdraw(amount)
    
    def __call__(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:        
            threads = [executor.submit(self.withdraw, profile) for profile in self.db.get_active_profiles()]
            concurrent.futures.wait(threads)

if __name__ == "__main__":
    Withdraw()()
