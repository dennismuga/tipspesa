import asyncio
import random
import pytz
from datetime import datetime
from functools import lru_cache
from flask import request, session
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import aiohttp
import requests  # For sync fallback

from utils.betika import Betika
from utils.entities import Match

class Helper:
    def __init__(self, crud):
        self.betika = Betika()
        self.crud = crud

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def fetch_data_async(self, url: str, timeout: int = 10) -> Optional[Dict]:
        headers = {'User-Agent': 'TipsPesa/2.0'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
        return None

    def fetch_data(self, url: str, timeout: int = 10) -> Optional[Dict]:
        return asyncio.run(self.fetch_data_async(url, timeout))

    def fetch_matches(self, day: str, comparator: str = '=', status: str = '', limit: int = 16) -> List[Match]:
        raw_matches = self.crud.fetch_matches(day, comparator, status, limit)
        return [Match(**m) for m in raw_matches]  # Pydantic auto-validates

    def get_share_code(self, matches):
        current_time = datetime.now(self.get_user_tz())
        try:
            betslips = []
            for match in matches:   
                kickoff = match.get("kickoff")
                if kickoff is None:
                    continue
                # Assume kickoff is str or naive dt; make aware
                if isinstance(kickoff, str):
                    # Parse assuming UTC or local; adjust format
                    kickoff_dt = datetime.strptime(kickoff, '%Y-%m-%d %H:%M:%S')  # Adjust format
                    kickoff_aware = self.get_user_tz().localize(kickoff_dt)  # Or pytz.UTC.localize if UTC
                elif isinstance(kickoff, datetime) and kickoff.tzinfo is None:
                    kickoff_aware = self.get_user_tz().localize(kickoff)  # Assume naive is local/UTC
                else:
                    kickoff_aware = kickoff  # Already aware

                if not any(betslip["parent_match_id"] == match.get("parent_match_id") for betslip in betslips) and kickoff_aware > current_time:
                    betslip = {
                        "odd_key": match.get("bet_pick"),
                        "outcome_id": match.get("outcome_id"),
                        "special_bet_value": match.get("special_bet_value"),
                        "parent_match_id": match.get("parent_match_id"),
                        "sub_type_id": match.get("sub_type_id"),
                    }
                    betslips.append(betslip)
                    
            if betslips:
                code = self.betika.share_bet(betslips)
                return code if code else ''
                
        except Exception as e:
            print(f"Error in get share code: {e}")
        
        return ''

    @lru_cache(maxsize=1000)
    def get_tz_from_ip(self, ip: str) -> str:
        try:
            resp = requests.get(f'https://ipapi.co/{ip}/json/', timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('timezone', 'Africa/Nairobi')
        except Exception:
            pass
        return 'Africa/Nairobi'

    def get_user_tz(self):
        tz_str = session.get('user_timezone')
        if not tz_str:
            ip = request.remote_addr
            tz_str = self.get_tz_from_ip(ip)
            session['user_timezone'] = tz_str
        return pytz.timezone(tz_str)

    def get_code(self) -> str:
        digits = [1, 2, 5, 6, 8, 9]
        return ''.join(str(random.choice(digits)) for _ in range(6))