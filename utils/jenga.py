import os
from dotenv import load_dotenv
import requests

class Jenga:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.base_url = os.getenv('JENGA_BASE_URL', 'https://uat.finserve.africa')
        self.merchant_code = os.getenv('JENGA_MERCHANT_CODE')
        self.consumer_secret = os.getenv('JENGA_CONSUMER_SECRET')
        self.api_key = os.getenv('JENGA_API_KEY')
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
