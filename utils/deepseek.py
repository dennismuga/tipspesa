import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   

class DeepSeek():
    def __init__(self):  
        self.client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
        
    def chat(self, message):
        completion = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": message}                
            ],
        )

        response = completion.choices[0].message.content
        return response