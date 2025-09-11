import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   

class DeepSeek():
    def __init__(self):  
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
                
    def get_response(self, query):
        while True:
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant"},
                        {"role": "user", "content": "Hello"},
                    ],
                    stream=False
                )

                return response.choices[0].message.content
            
            except Exception as e:
                print(f"Error in DeepSeek.get_response: {e}")
                return None