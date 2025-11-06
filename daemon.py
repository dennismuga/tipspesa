import time
from utils.paystack import Charge, Transactions

# Example usage
if __name__ == "__main__":
    phone = "+254743626907"
    #phone = "+254105565532"
    amount = 3
    while True:
        charge = Charge().stk_push(phone, amount, provider="mpesa")
        amount -= 1
        reference = charge.get("data").get("reference")
        while True:
            time.sleep(3)
            transaction_details = Transactions().verify(reference=reference)
            if transaction_details and transaction_details.get('status'):
                status = transaction_details.get('data').get('status')
                
                if status == 'ongoing':
                    continue
                else:
                    amount = 3 if amount == 0 else amount
                    break
            else:
                break
            
        time.sleep(45)