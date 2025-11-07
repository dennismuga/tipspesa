import uuid
from typing import List, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import scoped_session, sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
from dotenv import load_dotenv

from utils.entities import User  # Pydantic for validation

load_dotenv()

class PostgresCRUD:
    def __init__(self, app=None, UserDB=None, MatchDB=None):
        self.db = app.extensions['sqlalchemy']
        self.UserDB = UserDB 
        self.MatchDB = MatchDB
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def fetch_matches(self, day: str, comparator: str = '=', status: str = '', limit: int = 56) -> List[Dict]:
        session = self.db.session
        try:
            query = text("""
                SELECT * FROM matches m
                INNER JOIN source_model sm ON sm.parent_match_id = m.parent_match_id
                WHERE m.kickoff::date {} (CURRENT_TIMESTAMP + INTERVAL '3 hours')::date {} {}
                ORDER BY m.kickoff ASC LIMIT :limit
            """.format(comparator, day, status))
            result = session.execute(query, {'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result]
        finally:
            # No close needed; Flask-SQLAlchemy handles scoped session
            pass


    def get_user(self, user_id: Optional[str] = None, phone: Optional[str] = None) -> Optional[User]:
        session = self.db.session
        try:
            query = session.query(self.UserDB)
            if user_id:
                query = query.filter(self.UserDB.id == user_id)
            if phone:
                query = query.filter(self.UserDB.phone == phone)
            user_db = query.first()
            if user_db:
                active = user_db.expires_at > datetime.now() if user_db.expires_at else False
                return User(
                    id=user_db.id,
                    phone=user_db.phone,
                    plan=user_db.plan,
                    active=active
                )
            return None
        finally:
            pass  # Scoped session auto-cleans


    def add_user(self, phone: str):
        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, phone))
        new_user = self.db.UserDB(
            id=user_id,
            phone=phone,
            plan='Free',
            expires_at=datetime.now()
        )
        session = self.db.session
        try:
            session.add(new_user)
            session.commit()
        except Exception:
            session.rollback()
            raise


    def update_user_expiry(self, order_id: str, plan: str, days: int = 1):
        session = self.db.session
        try:
            session.execute(
                text("""
                    UPDATE subscribers 
                    SET plan = :plan, expires_at = NOW() + INTERVAL '{} days' 
                    WHERE id = (SELECT subscriber_id FROM transactions WHERE id = :order_id)
                """.format(days)),
                {'plan': plan, 'order_id': order_id}
            )
            session.commit()
        except Exception:
            session.rollback()
            raise


    def update_match_results(self, match_id: str, home_goals: int, away_goals: int, status: str):
        session = self.db.session
        try:
            session.execute(
                text("""
                    UPDATE matches 
                    SET home_results = :home_goals, away_results = :away_goals, status = :status 
                    WHERE match_id = :match_id
                """),
                {'home_goals': home_goals, 'away_goals': away_goals, 'status': status, 'match_id': match_id}
            )
            session.commit()
        except Exception:
            session.rollback()
            raise