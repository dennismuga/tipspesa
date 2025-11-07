import hmac
import json
from typing import Dict, Optional
import os
from dotenv import load_dotenv
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

class Paystack:
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.secret_key}'
        }
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY not set")

class Transactions(Paystack):
    CURRENCY = os.getenv('PAYSTACK_CURRENCY', 'KES')

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def initialize(self, email: str, amount: float) -> Optional[Dict]:
        url = f'{self.base_url}/transaction/initialize'
        data = {
            "email": email,
            "amount": int(amount * 100),
            "currency": self.CURRENCY
        }
        resp = requests.post(url, headers=self.headers, json=data)
        if resp.status_code == 200:
            return resp.json()
        print(f"Init failed: {resp.status_code} - {resp.text}")
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def verify(self, reference: str) -> Optional[Dict]:
        url = f'{self.base_url}/transaction/verify/{reference}'
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        print(f"Verify failed: {resp.status_code}")
        return None

    def verify_webhook(self, payload: str, signature: str) -> bool:
        key = self.secret_key.encode()
        expected = hmac.new(key, payload.encode(), 'sha512').hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        data = json.loads(payload)
        return self.verify(data.get('reference', '')).get('status')

class Charge(Paystack):
    @retry(stop=stop_after_attempt(3))
    def stk_push(self, phone: str, amount: float, provider: str = "mpesa") -> Optional[Dict]:
        url = f'{self.base_url}/charge'
        adj_amount = int(amount * 102.5) + 99  # Fee adjustment
        data = {
            "email": f"{phone}@{ 'safaricom.co.ke' if provider == 'mpesa' else 'airtel.co.ke' }",
            "amount": int(adj_amount * 100),
            "currency": self.CURRENCY,
            "mobile_money": {"phone": phone, "provider": provider}
        }
        resp = requests.post(url, headers=self.headers, json=data)
        if resp.status_code == 200:
            return resp.json()
        return None