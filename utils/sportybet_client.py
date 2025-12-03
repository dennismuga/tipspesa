import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger(__name__)


class SportybetClient:
    BASE_URL = "https://www.sportybet.com/api/ke"

    def __init__(self) -> None:
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self) -> None:
        """Set realistic browser-like headers."""
        self.session.headers.update({
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://www.sportybet.com",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Unified request handler with proper error logging."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)

            if response.status_code == 403:
                logger.error("403 Forbidden - likely blocked by anti-bot protection")
                logger.debug("Response snippet: %s", response.text[:500])
                return None

            response.raise_for_status()
            data = response.json()
            return data.get("response", data)

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s %s: %s", method.upper(), endpoint, e)
        except requests.exceptions.RequestException as e:
            logger.error("Network error for %s %s: %s", method.upper(), endpoint, e)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received: %s", response.text[:500])
        except Exception as e:
            logger.error("Unexpected error during %s %s: %s", method.upper(), endpoint, e)

        return None


    def book_bet(self, matches: List[Dict]) -> Optional[str]:
        """
        Book multiple selections and return share code.
        Each event must have _event_id, _market_id, _outcome_id.
        """
        selections = [
            {
                "eventId": f'sr:match:{match.parent_match_id}',
                "marketId": str(match.sub_type_id),
                "outcomeId": str(match.outcome_id),
                "specifier": str(match.special_bet_value),
            }
            for match in matches
            #if all(k in match for k in ("parent_match_id", "sub_type_id", "outcome_id"))
        ]

        if not selections:
            logger.error("No valid selections to book")
            return None

        payload = {"selections": selections}
        response = self._request("POST", "/orders/share", json=payload)  

        if response and "data" in response:
            return response["data"].get("shareCode")

        logger.error("Failed to book bet, response: %s", response)
        return None