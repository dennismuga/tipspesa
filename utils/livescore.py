
import requests

class LiveScore():
    """
    Class to handle Sofascore API interactions.
    """

    def __init__(self):
        """
        Initialize the LiveScore class.
        """
        self.base_url = "https://prod-cdn-mev-api.livescore.com/v1/api/app/date/soccer"
        
    def get_results(self, event_date):
        """
        Fetch events for a given date.
        :param event_date: Date in YYYYMMDD format.
        :return: List of events.
        """
        
        url = f'{self.base_url}/{event_date}/3?locale=en&MD=1'
        try:
            response = requests.get(url).json()
            stages = response.get('Stages')
            results = []
             
            if not stages:
                print("No Stages found for the given date.")
                return None
            else:
                for stage in stages:
                    events = stage.get('Events')
                    for event in events:                    
                        homeTeam = event.get('T1')[0].get('Nm')
                        awayTeam = event.get('T2')[0].get('Nm')
                        homeScore = event.get('Tr1')
                        awayScore = event.get('Tr2')
                        results.append({
                            "home_team": homeTeam,
                            "away_team": awayTeam,
                            "home_score": homeScore,
                            "away_score": awayScore
                        })
                
            return results
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
        except Exception as err:
            print(f"Unexpected error: {err}")