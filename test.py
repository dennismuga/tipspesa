
import uuid
from utils.jenga import Jenga

# Example usage
if __name__ == "__main__":
    try:
        # Initialize Jenga instance
        jenga = Jenga()

        # Test STK Push
        response = jenga.generate_payment_link(
            order_ref="ORDER12345",
            amount=10,
            phone_number="0759697757",
            customer_name="John Doe",
            customer_email="john@example.com",
            description="Test payment for demo"
        )
        print("STK Push Response:", response)
    except Exception as e:
        print(f"Error: {str(e)}")