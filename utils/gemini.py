import os, requests
from dotenv import load_dotenv
from google import genai

class Gemini():
    def __init__(self):        
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
    def get_response(self, query):
        while True:
            try:
                response = self.client.models.generate_content(
                    model= "gemini-2.5-flash", # os.getenv('GEMINI_MODEL'), 
                    contents=str(query)
                )
                return response.text
            
            except Exception as e:
                print(f"Error in Gemini.get_response: {e}")
                self.client = genai.Client('AIzaSyDdp3DT8Q8xBc39dsuIrxQMs7vrcMa17Fs') # Fallback API key
    
    def call_gemini_api(self, query):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": os.getenv('GEMINI_API_KEY')
            }
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": query
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=data)
            text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return text
        
        except Exception as e:
            print(f"Error in predict_match: {e}")

            return None
