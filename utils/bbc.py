
import requests

class BBC():
    """
    Class to handle Sofascore API interactions.
    """

    def __init__(self):
        """
        Initialize the LiveScore class.
        """
        self.base_url = "https://web-cdn.api.bbci.co.uk/wc-poll-data/container/sport-data-scores-fixtures?urn=urn%3Abbc%3Asportsdata%3Afootball%3Atournament-collection%3Acollated"
        
    def get_results(self, today, yesterday):
        """
        Fetch events for a given date.
        :param event_date: Date in YYYYMMDD format.
        :return: List of events.
        """
        today_date = today.strftime('%Y-%m-%d')
        event_date = yesterday.strftime('%Y-%m-%d')
        url = f'{self.base_url}&todayDate={today_date}&selectedStartDate={event_date}&selectedEndDate={event_date}'
        try:
            response = requests.get(url).json()
            event_groups = response.get('eventGroups')
            results = []
             
            if not event_groups:
                print("No eventGroups found for the given date.")
                return None
            else:
                for event_group in event_groups:
                    secondary_groups = event_group.get('secondaryGroups')
                    for secondary_group in secondary_groups:                        
                        events = secondary_group.get('events')
                        for event in events:                 
                            homeTeam = event.get('home').get('fullName')
                            awayTeam = event.get('away').get('fullName')
                            homeScore = event.get('home').get('score')
                            awayScore = event.get('away').get('score')
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