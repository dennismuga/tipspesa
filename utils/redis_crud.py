# Load environment variables from .env file
import os
from dotenv import load_dotenv
from redis import Redis


load_dotenv()
class RedisCRUD():
    def __init__(self):
        self.redis = Redis(
            host=os.getenv('REDIS_HOSTNAME'),
            port=os.getenv('REDIS_PORT'),
            password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_SSL') in ['True', '1'] else None,
            ssl=False if os.getenv('REDIS_SSL') in ['False', '0'] else True
        )
        
    def set(self, parent_match_id, data):
        try:
            # Store the JSON data in Redis with a TTL of 90 minutes (5400 seconds)
            self.redis.set(f"{parent_match_id}", data, ex=7200)
            # print(f"Data for match {parent_match_id} stored in Redis.")

        except Exception as e:
            print(f"Error storing data in Redis: {e}")
                
    def get(self, key):
        value = self.redis.get(key)
        return value.decode() if value else None
    
    def delete(self, key):
        self.redis.delete(key)