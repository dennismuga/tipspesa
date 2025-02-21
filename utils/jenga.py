import os
from dotenv import load_dotenv
import requests
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64

class Jenga:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.merchant_code = os.getenv('JENGA_MERCHANT_CODE')
        self.consumer_secret = os.getenv('JENGA_CONSUMER_SECRET')
        self.api_key = os.getenv('JENGA_API_KEY')
        self.base_url = 'https://uat.finserve.africa'  # Sandbox URL; use 'https://api.jengahq.io' for production
        self.token = None  # Store access token after authentication

        # Validate credentials
        if not all([self.merchant_code, self.consumer_secret, self.api_key]):
            raise ValueError("Missing Jenga credentials in environment variables.")

    def get_access_token(self):
        """Authenticate with JengaHQ API and retrieve access token."""
        url = f"{self.base_url}/authentication/api/v3/authenticate/merchant"
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "merchantCode": self.merchant_code,
            "consumerSecret": self.consumer_secret
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            self.token = response.json()["accessToken"]
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    def generate_signature(self, order_reference, payment_currency, msisdn, payment_amount):
        """Generate cryptographic signature for the STK Push request."""
        signature_string = f"{order_reference}{payment_currency}{msisdn}{payment_amount}"
        try:
            key = RSA.importKey(open("privatekey.pem").read())  # Load your private key
            h = SHA256.new(signature_string.encode('utf-8'))
            signer = PKCS1_v1_5.new(key)
            signature = base64.b64encode(signer.sign(h)).decode('utf-8')
            return signature
        except FileNotFoundError:
            raise Exception("Private key file 'privatekey.pem' not found.")
        except Exception as e:
            raise Exception(f"Signature generation failed: {str(e)}")

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
