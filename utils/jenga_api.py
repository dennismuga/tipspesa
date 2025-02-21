import os
from dotenv import load_dotenv
import requests

class JengaAPI:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.merchant_code = os.getenv('JENGA_MERCHANT_CODE')
        self.password = os.getenv('JENGA_PASSWORD')
        self.consumer_secret = os.getenv('JENGA_CONSUMER_SECRET')
        self.api_key = os.getenv('JENGA_API_KEY')
        self.base_url = 'https://sandbox.jengahq.io'  # Sandbox URL; use 'https://api.jengahq.io' for production
        self.token = None  # Store access token after authentication

        # Validate credentials
        if not all([self.merchant_code, self.password]):
            raise ValueError("Missing Jenga credentials in environment variables.")

    def get_access_token(self):
        """Authenticate with JengaHQ API and retrieve access token."""
        url = f"{self.base_url}/identity-test/v3/token"
        payload=f'username={self.merchant_code}&password={self.password}'
        headers = {}
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            print(response_json)
            self.token = response_json["access_token"]
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    def initiate_stk_push(self, order_ref, amount, phone_number, customer_name, customer_email, description="Test Payment"):
        """Initiate M-Pesa STK Push payment."""
        if not self.token:
            self.get_access_token()  # Authenticate if token is not set

        url = f"{self.base_url}/api-checkout/mpesa-stk-push/v3.0/init"
        
        # Payload for STK Push
        payload = {
            "order": {
                "orderReference": order_ref,
                "orderAmount": amount,
                "orderCurrency": "KES",
                "source": "APICHECKOUT",
                "countryCode": "KE",
                "description": description
            },
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "phoneNumber": phone_number,
                "identityNumber": "0000000",
                "firstAddress": "",
            },
            "payment": {
                "paymentReference": f"PAY-{order_ref}",  # Unique payment reference
                "paymentCurrency": "KES",
                "channel": "MOBILE",
                "service": "MPESA",
                "provider": "JENGA",
                "callbackUrl": "https://your-callback-url.com",
                "details": {
                    "msisdn": phone_number,
                    "paymentAmount": amount
                }
            }
        }

        # Generate signature
        signature = self.generate_signature(
            payload["order"]["orderReference"],
            payload["payment"]["paymentCurrency"],
            payload["payment"]["details"]["msisdn"],
            payload["payment"]["details"]["paymentAmount"]
        )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Signature": signature
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"STK Push failed: {response.status_code} - {response.text}")
