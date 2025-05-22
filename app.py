
import os
from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_session import Session
from redis import Redis
from dotenv import load_dotenv
from datetime import datetime, timedelta

from utils.entities import MinOdds, MinMatches, Plan
from utils.helper import Helper
from utils.pesapal import Pesapal
from utils.postgres_crud import PostgresCRUD
from v2.predict_and_bet import PredictAndBet
from v2.stats import Stats

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
min_odds = MinOdds()
min_matches = MinMatches()
        
def update_stats():
    try:
        Stats()()
    except Exception as e:
        print(f"Error in background task: {e}")

def predict_and_bet():
    try:
        PredictAndBet()()
    except Exception as e:
        print(f"Error in background task: {e}")
        
def subscribe():     
    phone = request.form['phone']
    amount = request.form['amount']
    user = db.get_user(phone=phone)
        
    if not user:
        db.add_user(phone)
        user = db.get_user(phone=phone)

    if current_user.is_authenticated:
        logout_user()

    login_user(user)

    order_details = Pesapal().submit_order_request(phone[-9:], amount)
    order_tracking_id = order_details.get('order_tracking_id')
    db.insert_transaction(order_tracking_id, current_user.id, amount)
    return render_template('pay.html', order_tracking_id=order_tracking_id)

# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return db.get_user(user_id=user_id)

@app.errorhandler(404)
def page_not_found(e):
    # Redirect to a specific endpoint, like 'plans', or a custom 404 page
    return redirect(url_for('free'), 302)

def filter_matches(day, match_count, end, status=''):
    matches = helper.fetch_matches(day, '=', status, limit=51)
    filtered_matches = []
    total_odds = 1
    
    for match in matches:
        # Check if home_team or away_team is already in filtered_matches
        is_duplicate = any(
            match.home_team == m.home_team and match.away_team == m.away_team 
            for m in filtered_matches
        )
        if not is_duplicate:
            filtered_matches.append(match)
            total_odds *= match.odd
    
    total_matches = len(filtered_matches)  # Count unique matches
    # Ensure start and end are within bounds
    end = min(total_matches, end)
    start = max(0, end - match_count)
    to_return = filtered_matches[start:end]  # Correct slicing
    
    return to_return, total_matches

def get_matches(count, index):
    three_days_ago, total_matches = filter_matches('-3', min_matches.platinum, 51)
    two_days_ago, total_matches = filter_matches('-2', min_matches.platinum, 51)
    yesterday_matches, total_matches = filter_matches('-1', min_matches.platinum, 51)
    today_matches, total_matches = filter_matches('', count, index)
    history = [
        {
            'day': (datetime.now() - timedelta(days=3)).strftime("%A"),
            'matches': sorted(three_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': (datetime.now() - timedelta(days=2)).strftime("%A"),
            'matches': sorted(two_days_ago, key=lambda match: match.kickoff) 
        },
        {
            'day': 'Yesterday',
            'matches': sorted(yesterday_matches, key=lambda match: match.kickoff) 
        }
    ]
    
    return total_matches, today_matches, history
    
    
@app.route('/', methods=['GET'])
def free():
    total_matches, today_matches, history = get_matches(min_matches.free, 4)
    plan = Plan('Free', 0, min_odds.free, 'green', 1, today_matches, history)  
    return render_template('plans.html', plan=plan, total_matches=total_matches, min_matches=min_matches, min_odds=min_odds)

@app.route('/bronze', methods=['GET', 'POST'])
def bronze():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        total_matches, today_matches, history = get_matches(min_matches.bronze, 12)
        plan = Plan('Bronze', 20, min_odds.bronze, 'purple', 2, today_matches, history)
        return render_template('plans.html', plan=plan, total_matches=total_matches, min_matches=min_matches, min_odds=min_odds)

@app.route('/silver', methods=['GET', 'POST'])
def silver():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        total_matches, today_matches, history = get_matches(min_matches.silver, 23)
        plan = Plan('Silver', 30, min_odds.silver, 'blue', 3, today_matches, history)
        return render_template('plans.html', plan=plan, total_matches=total_matches, min_matches=min_matches, min_odds=min_odds)

@app.route('/gold', methods=['GET', 'POST'])
def gold():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        total_matches, today_matches, history = get_matches(min_matches.gold, 37)
        plan = Plan('Gold', 50, min_odds.gold, 'yellow', 4, today_matches, history)
        return render_template('plans.html', plan=plan, total_matches=total_matches, min_matches=min_matches, min_odds=min_odds)
    
@app.route('/platinum', methods=['GET', 'POST'])
def platinum():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        total_matches, today_matches, history = get_matches(min_matches.platinum, 51)
        plan = Plan('Platinum', 70, min_odds.platinum, 'pink', 5, today_matches, history)
        return render_template('plans.html', plan=plan, total_matches=total_matches, min_matches=min_matches, min_odds=min_odds)
             
@app.route('/betika-share-code/<plan_name>', methods=['GET'])
def betika_share_code(plan_name):
    today_matches = []
    if plan_name == 'Free':
        total_matches, today_matches, history = get_matches(min_matches.free, 4)
    if plan_name == 'Bronze':
        total_matches, today_matches, history = get_matches(min_matches.free, 12)
    if plan_name == 'Free':
        total_matches, today_matches, history = get_matches(min_matches.free, 23)
    if plan_name == 'Gold':
        total_matches, today_matches, history = get_matches(min_matches.free, 37)
    if plan_name == 'Platinum':
        total_matches, today_matches, history = get_matches(min_matches.free, 51)
        
    return helper.get_share_code(today_matches)

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')
    
def save_pesapal_response():   
    order_tracking_id = request.args.get('OrderTrackingId')
    transaction = Pesapal().get_transaction_status(order_tracking_id)
    order_tracking_id = transaction.get('order_tracking_id')
    payment_method = transaction.get('payment_method')
    payment_account = transaction.get('payment_account')
    confirmation_code = transaction.get('confirmation_code')
    status = transaction.get('payment_status_description')
    amount = int(transaction.get('amount'))
    db.update_transaction(order_tracking_id, payment_method, payment_account, confirmation_code, status)

    if status == 'Completed':
        plan = 'Bronze Plan' if amount == 20 else 'Silver Plan' if amount == 30 else 'Gold Plan' if amount == 50 else 'Platinum Plan' if amount == 70 else 'Free Tips'
        db.update_user_expiry(order_tracking_id, plan)

@app.route('/pesapal-callback', methods=['GET', 'POST'])
def pesapal_callback():  
    save_pesapal_response()
    return redirect(url_for('free'))

@app.route('/pesapal-ipn', methods=['GET', 'POST'])
def pesapal_ipn():  
    save_pesapal_response()
    return redirect(url_for('free'))
    
@app.route('/terms-and-conditions')
def terms_and_conditions():    
    return render_template('terms-and-conditions.html')

@app.route('/privacy-policy')
def privacy_policy():    
    return render_template('privacy-policy.html')
 
if __name__ == '__main__':
    debug_mode = os.getenv('IS_DEBUG', 'False') in ['True', '1', 't']
    app.run(debug=debug_mode)
