import json
import os
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for, current_app
from flask_login import LoginManager, current_user, login_user, logout_user, UserMixin
from flask_session import Session
from flask.sessions import session_json_serializer, SessionInterface
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest

# Custom imports for safe session handling
from redis import Redis

from utils.entities import Match, Plan
from utils.helper import Helper
from utils.paystack import Transactions
from utils.postgres_crud import PostgresCRUD

load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-me')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_COOKIE_NAME'] = 'sessionid'  # Explicit cookie name
app.config['SESSION_REDIS'] = Redis(
    host=os.getenv('REDIS_HOSTNAME'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=True
)
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True if using HTTPS on Vercel
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Auto-expire sessions
app.config['SESSION_SERIALIZER'] = session_json_serializer

Session(app)
db = SQLAlchemy(app)  # Global if needed

# Flask-Caching config for cloud Redis (use individual params, not instance)
# Configure caching with Redis
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOSTNAME')
app.config['CACHE_REDIS_PORT'] = os.getenv('REDIS_PORT')
app.config['CACHE_REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD')
app.config['CACHE_REDIS_SSL'] = True
app.config['CACHE_REDIS_DB'] = 0              # Or your Redis database index
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default TTL
app.config['CACHE_KEY_PREFIX'] = 'tipspesa_cache'  # Namespace keys to avoid conflicts

cache = Cache(app)

# Flask-Limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=f"rediss://default:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOSTNAME')}:{os.getenv('REDIS_PORT')}",
    default_limits=["200 per day", "50 per hour"]
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

# Models
class UserDB(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True)
    phone = db.Column(db.String(255), unique=True)
    plan = db.Column(db.String(50), default='Free')
    expires_at = db.Column(db.DateTime)

class MatchDB(db.Model):
    __tablename__ = 'matches'
    match_id = db.Column(db.String(36), primary_key=True)
    kickoff = db.Column(db.DateTime, index=True)
    home_team = db.Column(db.String(255))
    away_team = db.Column(db.String(255))
    prediction = db.Column(db.String(50))
    odd = db.Column(db.Float)
    status = db.Column(db.String(50))
    home_results = db.Column(db.Integer)
    away_results = db.Column(db.Integer)
    overall_prob = db.Column(db.Integer)
    # Indexes
    __table_args__ = (db.Index('idx_kickoff', 'kickoff'),)

with app.app_context():
    db.create_all()  # Init tables

# CRUD now uses SQLAlchemy (update postgres_crud.py accordingly)
crud = PostgresCRUD(app, UserDB, MatchDB)  # Inject app for db
helper = Helper(crud)
paystack_transaction = Transactions()

@login_manager.user_loader
def load_user(user_id):
    return crud.get_user(user_id=user_id)

def free_pass():
    free_user = crud.get_user(phone='admin@tipspesa.com')
    if free_user and not current_user.is_authenticated:
        login_user(free_user)
    elif current_user.is_authenticated and current_user.id != free_user.id:
        logout_user()
        login_user(free_user)

@cache.memoize(timeout=300)
def get_matches(count: int = 50, end_index: int = 50) -> tuple[List[Match], List[Dict]]:
    # Fetch data with proper params
    five_days_ago = crud.fetch_matches('-5', '=', '', limit=count)
    four_days_ago = crud.fetch_matches('-4', '=', '', limit=count)
    three_days_ago = crud.fetch_matches('-3', '=', '', limit=count)
    two_days_ago = crud.fetch_matches('-2', '=', '', limit=count)
    yesterday_matches = crud.fetch_matches('-1', '=', '', limit=count)
    today_matches = crud.fetch_matches('', '>=', 'AND status IS NULL', limit=count)  # Fixed: '' for today

    user_tz = helper.get_user_tz()
    datetime_now = datetime.now(user_tz)

    # Complete history
    history = [
        {
            'day': (datetime_now - timedelta(days=5)).strftime("%A"),
            'matches': five_days_ago 
        },
        {
            'day': (datetime_now - timedelta(days=4)).strftime("%A"),
            'matches': four_days_ago
        },
        {
            'day': (datetime_now - timedelta(days=3)).strftime("%A"),
            'matches': three_days_ago
        },
        {
            'day': (datetime_now - timedelta(days=2)).strftime("%A"),
            'matches': two_days_ago
        },
        {
            'day': 'Yesterday',
            'matches': yesterday_matches
        }
    ]

    return today_matches, history

def create_slips(today_matches: List[Match], slip_size: int = 8) -> List[Dict]:
    slips = []
    for i in range(0, len(today_matches), slip_size):
        chunk = today_matches[i:i + slip_size]
        slips.append({
            "id": (i // slip_size) + 1,
            "matches": chunk,
            "betika_share_code": helper.get_share_code(chunk).upper()
        })
    return slips

@app.route('/ads.txt')
def ads_txt():
    return "google.com, pub-1757067070842104, DIRECT, f08c47fec0942fa0"

@app.route('/', methods=['GET', 'POST'])
def index():
    free_pass()
    if request.method == 'POST':
        action = request.form.get('action') or request.json.get('action')
        if action == 'login':
            return subscribe()
        elif action == 'update_results':
            try:
                match_id = request.form['match_id']
                home_goals = int(request.form['home_team_goals'])
                away_goals = int(request.form['away_team_goals'])
                status = request.form.get('status', '').strip()
                crud.update_match_results(match_id, home_goals, away_goals, status)
                return jsonify({'success': True})
            except (ValueError, KeyError) as e:
                current_app.logger.error(f'Update error: {e}')
                return jsonify({'error': 'Invalid input'}), 400
        elif action == 'donate':
            data = request.get_json() or {}
            amount = int(data.get('amount', 1))
            if not 1 <= amount <= 10:
                return jsonify({'error': 'Invalid amount'}), 400
            order_details = paystack_transaction.initialize(email="donate@tipspesa.com", amount=amount * 100)
            if order_details and order_details.get('status'):
                return jsonify({'success': True, 'authorization_url': order_details['data']['authorization_url']})
            return jsonify({'success': False}), 400
        return jsonify({'success': False}), 400

    today_matches, history = get_matches()
    slips = create_slips(today_matches)
    current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
    yesterday = (current_time - timedelta(days=1)).strftime("%A")
    today = current_time.strftime("%A")
    tomorrow = (current_time + timedelta(days=1)).strftime("%A")
    return render_template('plans.html', slips=slips, current_time=current_time,
                           yesterday=yesterday, today=today, tomorrow=tomorrow, history=history)

def subscribe():
    phone = request.form.get('phone', '').strip().lower()
    amount = int(request.form.get('amount', 0))
    if not phone or '@' not in phone:
        return redirect(url_for('index', error='Invalid email'))
    user = crud.get_user(phone=phone)
    if not user:
        crud.add_user(phone)
        user = crud.get_user(phone=phone)
    if current_user.is_authenticated:
        logout_user()
    login_user(user)
    order_details = paystack_transaction.initialize(email=phone, amount=amount)
    if order_details and order_details.get('status'):
        ref = order_details['data']['reference']
        crud.insert_transaction(ref, user.id, amount)
        return redirect(order_details['data']['authorization_url'])
    return redirect(url_for('index', error='Payment failed'))

@app.route('/paystack-callback', methods=['GET', 'POST'])
def paystack_callback():
    reference = request.args.get('reference')
    if not reference:
        return redirect(url_for('index', error='Invalid callback'))
    details = paystack_transaction.verify(reference)
    if details and details.get('status'):
        data = details['data']
        if data['status'] == 'success':
            amount = data['amount'] / 100
            days = 30 if amount == 500 else 7 if amount == 150 else 1
            crud.update_user_expiry(reference, 'Premium', days)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms-and-conditions.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/app-ads.txt')
def serve_app_ads_txt():
    return app.send_static_file('app-ads.txt')

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(e):
    current_app.logger.error(f'Server error: {e}')
    return render_template('500.html'), 500

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug = os.getenv('IS_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=debug, host='0.0.0.0')