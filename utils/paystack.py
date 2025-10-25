
import json, os
from dotenv import load_dotenv
import requests

load_dotenv()   

class Paystack():
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.getenv("PAYSTACK_SECRET_KEY")}'
        }
    
class Transactions(Paystack):    
    def initialize(self, email, amount):
        url = f'{self.base_url}/transaction/initialize'

        # Prepare the data to be sent
        data={ 
            "email": email, 
            "amount": amount*100,
            "currency": "KES"
        }

        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers, json=data)

            response_json = response.json()
            print(response_json)
            return response_json
            
        except Exception as e:
            print(e)
            return None  
        
    def verify(self, reference):
        url = f'{self.base_url}/transaction/verify/{reference}'
        
        try:
            # Make the POST request
            response = requests.get(url, headers=self.headers)

            # Check if the request was successful
            response_json = response.json()
            print(response_json)
            return response_json
            
        except Exception as e:
            print(e)
            return None


