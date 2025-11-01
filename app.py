
import os
import pytz

from datetime import datetime, timedelta
from typing import List, Dict, Any

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_session import Session
from redis import Redis

from utils.entities import Plan
from utils.helper import Helper
from utils.paystack import Transactions
from utils.postgres_crud import PostgresCRUD

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # One year in seconds
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(
    host=os.getenv('REDIS_HOSTNAME'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_SSL') in ['True', '1'] else None,
    ssl=False if os.getenv('REDIS_SSL') in ['False', '0'] else True
)
app.config['SESSION_COOKIE_SECURE'] = True if os.getenv('REDIS_SSL') in ['True', '1'] else False  # Set to True if using HTTPS on Vercel
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'free'

db = PostgresCRUD()
helper = Helper()
paystack_transaction = Transactions()

def free_pass():
    free_user = db.get_user(phone='admin@tipspesa.com')
    if not current_user:
        login_user(free_user)
    if current_user.is_authenticated and current_user != free_user:
        logout_user()
        login_user(free_user)
        
def subscribe():     
    phone = request.form['phone']
    amount = int(request.form['amount'])
    user = db.get_user(phone=phone)
        
    if not user:
        db.add_user(phone)
        user = db.get_user(phone=phone)

    if current_user.is_authenticated:
        logout_user()

    login_user(user)

    order_details = paystack_transaction.initialize(email=phone, amount=amount)
    if order_details.get('status'):
        authorization_url = order_details.get('data').get('authorization_url')
        reference = order_details.get('data').get('reference')
        db.insert_transaction(reference, current_user.id, amount)
        return redirect(authorization_url)
    else:
        return redirect(url_for('index'))

# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return db.get_user(user_id=user_id)

@app.errorhandler(404)
def page_not_found(e):
    # Redirect to a specific endpoint, like 'plans', or a custom 404 page
    return redirect(url_for('index'))

def filter_matches(day, comparator='=', status='', limit=56):
    matches = helper.fetch_matches(day, comparator, status, limit)
    filtered_matches = []
    total_odds = 1
    to_return = []    
    user_tz = helper.get_user_tz()
    eat_tz = pytz.timezone('Africa/Nairobi')
    
    for match in matches:
        kickoff = eat_tz.localize(match.kickoff)
        match.kickoff = kickoff.astimezone(user_tz)
        if comparator == '>=' and match.kickoff.date() < datetime.now().astimezone(user_tz).date():
            continue
        
        # Check if home_team or away_team is already in filtered_matches
        is_duplicate = any(
            match.home_team == m.home_team and match.away_team == m.away_team 
            for m in filtered_matches
        )
        if not is_duplicate:
            filtered_matches.append(match)
            total_odds *= match.odd
            
    return filtered_matches

def get_matches(count, end_index):
    five_days_ago = filter_matches('-5')
    four_days_ago = filter_matches('-4')
    three_days_ago = filter_matches('-3')
    two_days_ago = filter_matches('-2')
    yesterday_matches = filter_matches('-1')
    today_matches = filter_matches('', '>=')
    user_tz = helper.get_user_tz()
    datetime_now = datetime.now().astimezone(user_tz)
    history = [
        {
            'day': (datetime_now - timedelta(days=5)).strftime("%A"),
            'matches': sorted(five_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': (datetime_now - timedelta(days=4)).strftime("%A"),
            'matches': sorted(four_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': (datetime_now - timedelta(days=3)).strftime("%A"),
            'matches': sorted(three_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': (datetime_now - timedelta(days=2)).strftime("%A"),
            'matches': sorted(two_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': 'Yesterday',
            'matches': sorted(yesterday_matches, key=lambda match: match.kickoff) 
        }
    ]
    
    return today_matches, history  

def create_slips(today_matches: List[Dict[str, Any]], slip_size: int = 8) -> List[Dict[str, Any]]:
    """Create slips from today's matches with specified size."""
    return [
        {
            "id": i + 1, 
            "matches": today_matches[i * slip_size:(i + 1) * slip_size],
            "betika_share_code": helper.get_share_code(today_matches[i * slip_size:(i + 1) * slip_size]).upper()
        } for i in range((len(today_matches) + slip_size - 1) // slip_size)
    ]

@app.route('/', methods=['GET', 'POST'])
def index():   
    if request.method == 'POST':         
        if request.form.get('action') == 'login':
            return subscribe()
        
        elif request.form.get('action') == 'update_results':
            match_id = request.form['match_id']
            home_team_goals = request.form['home_team_goals']
            away_team_goals = request.form['away_team_goals']
            status = request.form['status']
            db.update_match_results(match_id, home_team_goals, away_team_goals, status.strip())
        
        else:
            data = request.get_json()              
            if data.get('action') == 'donate':                               
                amount = int(data.get('amount'))*100
                order_details = paystack_transaction.initialize(email="donate.tipspesa@gmail.com", amount=amount)
                if order_details.get('status'):
                    authorization_url = order_details.get('data').get('authorization_url')
                    return jsonify(
                        {
                            'success': True, 
                            'authorization_url': authorization_url
                        }
                    ), 200  
                        
            return jsonify(
                {
                    'success': False
                }
            ), 504  
            
    today_matches, history = get_matches(50, 50)
    plan = Plan('Free', 0, 'green', 5, today_matches, history)  
    slips = create_slips(today_matches)
    current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
    yesterday = (current_time - timedelta(days=1)).strftime("%A")
    today = (current_time).strftime("%A")
    tomorrow = (current_time + timedelta(days=1)).strftime("%A")
    return render_template('plans.html', plan=plan, slips=slips, current_time=current_time, yesterday=yesterday, today=today, tomorrow=tomorrow) 

@app.route('/paystack-callback', methods=['GET', 'POST'])
def paystack_callback():  
    reference = request.args.get('reference')
    transaction_details = paystack_transaction.verify(reference=reference)
    if transaction_details.get('status'):
        status = transaction_details.get('data').get('status')
        channel = transaction_details.get('data').get('channel')
        bank = transaction_details.get('data').get('authorization').get('bank')
        receipt_number = transaction_details.get('data').get('receipt_number')   
        amount = transaction_details.get('data').get('amount')/100      
        db.update_transaction(reference, channel, bank, receipt_number, status)
        
        if status == 'success':
            days = 30 if amount==500 else 7 if amount==150 else 1
            db.update_user_expiry(reference,'Premium', days)        
        
    return redirect(url_for('index'))

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')
    
@app.route('/terms-and-conditions')
def terms_and_conditions():    
    return render_template('terms-and-conditions.html')

@app.route('/privacy-policy')
def privacy_policy():    
    return render_template('privacy-policy.html')

# The route to serve app-ads.txt from the root URL.
@app.route('/app-ads.txt')
def serve_app_ads_txt():
    """
    Serves the app-ads.txt file from the root URL of the domain.
    """
    # Use app.send_static_file to serve the file directly from the static folder
    return app.send_static_file('app-ads.txt')

if __name__ == '__main__':
    debug_mode = os.getenv('IS_DEBUG', 'False') in ['True', '1', 't']
    app.run(debug=debug_mode)






