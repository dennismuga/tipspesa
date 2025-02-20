import os, requests
import uuid
from dotenv import load_dotenv

class Pesapal():
    def __init__(self):
        # Pesapal credentials
        load_dotenv()
        self.consumer_key = os.getenv('PESAPAL_CONSUMER_KEY')
        self.consumer_secret = os.getenv('PESAPAL_CONSUMER_SECRET')
        self.base_url = 'https://pay.pesapal.com/v3/api' 
        self.callback_url = 'https://tipspesa.vercel.app/pesapal-callback'  #Redirect back after payment URL
        self.ipn_url = 'https://tipspesa.vercel.app/pesapal-ipn'  # IPN (Instant Payment Notification) URL
        # Headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.authenticate()

    def authenticate(self):
        url = f'{self.base_url}/Auth/RequestToken'

        # Prepare the data to be sent
        data = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret
        }

        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers, json=data)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                token = response_json.get('token')
                self.headers['Authorization'] = f'Bearer {token}'
                return response_json
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)  # Print the full response text for debugging
                return None
            
        except Exception as e:
            print(e)
            return None

    def register_IPN_URL(self):
        url = f'{self.base_url}/URLSetup/RegisterIPN'

        # Prepare the data to be sent
        data = {
            "url": self.ipn_url,
            "ipn_notification_type": "POST"
        }

        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers, json=data)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                return response_json
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)  # Print the full response text for debugging
                return None
            
        except Exception as e:
            print(e)
            return None

    def get_IPN_list(self):
        url = f'{self.base_url}/URLSetup/GetIpnList'

        try:
            # Make a GET request request
            response = requests.get(url, headers=self.headers)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                return response_json
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)  # Print the full response text for debugging
                return None
            
        except Exception as e:
            print(e)
            return None 
    
    def submit_order_request(self, phone, amount):
        url = f'{self.base_url}/Transactions/SubmitOrderRequest'

        # Prepare the data to be sent
        id = str(uuid.uuid4())
        # amount = round(amount/0.97, 2)

        data = {
            "id": id,
            "currency": "KES",
            "amount": amount,
            "description": "Payment For Premium Tips",
            "callback_url": self.callback_url,
            "notification_id": "69d97e59-3b5f-4b9a-a022-dc2211b9c5a7",
            "billing_address": {
                "phone_number": phone
            }
        }
        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers, json=data)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                return response_json
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)  # Print the full response text for debugging
                return None
            
        except Exception as e:
            print(e)
            return None 
    
    def get_transaction_status(self, order_tracking_id):
        url = f'{self.base_url}/Transactions/GetTransactionStatus?orderTrackingId={order_tracking_id}'
        try:
            # Make the POST request
            response = requests.get(url, headers=self.headers)

            # Check if the request was successful
            if response.status_code == 200:
                response_json = response.json()
                print(response_json)
                return response_json
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)  # Print the full response text for debugging
                return None
            
        except Exception as e:
            print(e)
            return None 