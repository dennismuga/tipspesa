from utils.paystack import Transactions
from utils.postgres_crud import PostgresCRUD

db = PostgresCRUD()

# Example usage
if __name__ == "__main__":
    transactions = Transactions()
    transactions.initialize(email="dennismuga@gmail.com", amount=10)
    # reference = 'ulrudvrrbc'
    # transaction_details = Transactions().verify(reference=reference)
    # if transaction_details and transaction_details.get('status'):
    #     status = transaction_details.get('data').get('status')
    #     channel = transaction_details.get('data').get('channel')
    #     domain = transaction_details.get('data').get('domain')
    #     receipt_number = transaction_details.get('data').get('receipt_number')   
    #     amount = transaction_details.get('data').get('amount')      
    #     db.update_transaction(reference, channel, domain, receipt_number, status)
        
    #     if status == 'success':
    #         days = 30 if amount==1000 else 7 if amount==300 else 1
    #         db.update_user_expiry(reference,'Premium', days)  