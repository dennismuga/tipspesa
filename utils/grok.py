import os
from dotenv import load_dotenv
from openai import OpenAI

class Grok():
    def __init__(self):     
        load_dotenv()   
        self.client = OpenAI(
            api_key=os.getenv("GITHUB_TOKEN"),
            base_url="https://models.github.ai/inference",
        )
        self.model = "xai/grok-3"
        self.model="deepseek/DeepSeek-R1-0528"
        
    def get_response(self, query):
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages=[
                    {"role": "user", "content": query}                
                ],
            )
            content = response.choices[0].message.content
            print(content)
            return content
        except Exception as e:
            print(f"Error in Grok.get_response: {e}")
            return None