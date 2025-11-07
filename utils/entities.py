from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, validator, Field
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

class User(UserMixin, BaseModel):
    id: str
    phone: str
    plan: str = 'Free'
    active: bool = False

    @validator('phone')
    def validate_phone(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v.lower()

class Plan(BaseModel):
    name: str
    amount: float
    color: str
    stars: int
    matches: List['Match']
    history: List[Dict]

class Match(BaseModel):
    match_id: Optional[str] = None
    kickoff: Optional[datetime] = None
    home_team: Optional[str] = Field(..., min_length=1)
    away_team: Optional[str] = Field(..., min_length=1)
    league: Optional[str] = None
    prediction: Optional[str] = None
    odd: float = Field(..., gt=0)
    home_results: Optional[int] = None
    status: Optional[str] = None
    away_results: Optional[int] = None
    overall_prob: int = Field(..., ge=0, le=100)
    sub_type_id: int = 0
    parent_match_id: Optional[str] = None
    bet_pick: Optional[str] = None
    outcome_id: int = 0
    special_bet_value: Optional[str] = None

    @validator('odd')
    def validate_odd(cls, v):
        if v <= 1.0:
            raise ValueError('Odd must be >1.0')
        return v

    def from_dict(self, data: Dict) -> 'Match':
        return Match(**data)


class Odd(BaseModel):
    display: str
    odd_key: str
    odd_def: str
    odd_value: float = Field(..., gt=0)
    special_bet_value: Optional[str] = None
    outcome_id: int
    parsed_special_bet_value: Optional[str] = None

# Other classes unchanged (UpcomingMatch, Jackpot, etc.)
class UpcomingMatch(BaseModel):
    # Fields as before
    pass

class Jackpot(BaseModel):
    id: str
    provider: str
    events: Optional[List] = None

class Event(BaseModel):
    id: str
    start_date: datetime
    home: str
    away: str
    odds: Optional[Dict] = None
    prediction: Optional[str] = None

class Odds(BaseModel):
    home_odds: float
    draw_odds: float
    away_odds: float
    created_at: Optional[datetime] = None