
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, phone, plan, active):  
        self.id = id
        self.phone = phone
        self.plan = plan
        self.active = active

class Plan():
    def __init__(self, name, amount, odds, color, stars, matches, history):
        self.name = name 
        self.amount = amount
        self.odds = odds
        self.color = color 
        self.stars = stars
        self.matches = sorted(matches, key=lambda match: match.kickoff) 
        self.history = history
        # self.matches_yesterday = sorted(matches_yesterday, key=lambda match: match.kickoff)

class Match():     
    def __init__(self):
        self.match_id = None
        self.kickoff = None
        self.home_team = None
        self.away_team = None
        self.prediction = None
        self.odd = 0
        self.home_results = None
        self.status = None
        self.away_results = None
        self.overall_prob = 0
        self.sub_type_id = 0
        self.parent_match_id = None
        self.bet_pick = None
        self.outcome_id = 0
        self.special_bet_value = None
        
class BetMarket:
    def __init__(self, data):        
        self.sub_type_id = data.get("sub_type_id")
        self.name = data.get("name")
        self.odds = [Odd(odd) for odd in data.get("odds")]    

class Odd:
    def __init__(self, odd):
        self.display = odd.get("display")
        self.odd_key = odd.get("odd_key")
        self.odd_def = odd.get("odd_def")
        self.odd_value = odd.get("odd_value")
        self.special_bet_value = odd.get("special_bet_value")
        self.outcome_id = odd.get("outcome_id")
        self.parsed_special_bet_value = odd.get("parsed_special_bet_value")
        
class MatchData:
    def __init__(self, data):
        self.id = data.get("id")
        self.host_id = data.get("host_id")
        self.guest_id = data.get("guest_id")
        self.league_id = data.get("league_id")
        self.round = data.get("Round")
        self.host_score = data.get("Host_SC")
        self.guest_score = data.get("Guest_SC")
        self.date = data.get("DATE")
        self.date_bah = data.get("DATE_BAH")
        self.pred_1 = data.get("Pred_1")
        self.pred_x = data.get("Pred_X")
        self.pred_2 = data.get("Pred_2")
        self.host_score_ht = data.get("Host_SC_HT")
        self.guest_score_ht = data.get("Guest_SC_HT")
        self.kelly = data.get("kelly")
        self.comment = data.get("comment")
        self.match_preview = data.get("match_preview")
        self.btr_link = data.get("btr_link")
        self.insight_link = data.get("insight_link")
        self.host_stadium = data.get("host_stadium")
        self.match_stadium = data.get("match_stadium")
        self.host_name = data.get("HOST_NAME")
        self.guest_name = data.get("GUEST_NAME")
        self.host_short = data.get("host_short")
        self.guest_short = data.get("guest_short")
        # Add more attributes as needed

class UpcomingMatch:
    def __init__(self, data):
        self.home_team = data.get("home_team")
        self.game_id = data.get("game_id")
        self.match_id = data.get("match_id")
        self.away_team = data.get("away_team")
        self.start_time = data.get("start_time")
        self.competition_name = data.get("competition_name")
        self.category = data.get("category")
        self.parent_match_id = data.get("parent_match_id")
        self.side_bets = data.get("side_bets")
        self.home_odd = data.get("home_odd")
        self.neutral_odd = data.get("neutral_odd")
        self.away_odd = data.get("away_odd")
        self.competition_id = data.get("competition_id")
        self.sport_id = data.get("sport_id")
        self.sport_name = data.get("sport_name")
        self.is_esport = data.get("is_esport", False)
        self.is_srl = data.get("is_srl", False)
        self.odds = data.get("odds") 
class Jackpot():    
    def __init__(self, id, provider, events=None):
        self.id = id
        self.provider = provider
        self.events = events
class Event():    
    def __init__(self, id, start_date, home, away, odds=None, prediction=None):
        self.id = id
        self.start_date = start_date
        self.home = home
        self.away = away
        self.odds = odds
        self.prediction = prediction
class Odds():    
    def __init__(self,home_odds, draw_odds, away_odds, created_at=None):
        self.home_odds = home_odds
        self.draw_odds = draw_odds
        self.away_odds = away_odds 
        self.created_at = created_at
        
class MinOdds():
    def __init__(self):
        self.free = 2
        self.bronze = 5
        self.silver = 10
        self.gold = 20
        self.platinum = 40


class MinMatches():
    def __init__(self):
        self.free = 4
        self.bronze = 12
        self.silver = 20 
        self.gold = 25
        self.platinum = 30
    
