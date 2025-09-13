
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_session import Session
import pytz
from redis import Redis

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

def filter_matches(day, match_count, end_index, status=''):
    matches = helper.fetch_matches(day, '=', status, limit=51)
    filtered_matches = []
    total_odds = 1
    to_return = []
    
    for match in matches:
        # Check if home_team or away_team is already in filtered_matches
        is_duplicate = any(
            match.home_team == m.home_team and match.away_team == m.away_team 
            for m in filtered_matches
        )
        if not is_duplicate:
            filtered_matches.append(match)
            total_odds *= match.odd
    
    #if len(filtered_matches) > end_index - match_count:   #only get a package if it contains new matches not in other packages
    end_index = min(len(filtered_matches), end_index)
    start = max(0, end_index - match_count)
    to_return = filtered_matches[start:end_index]  # Correct slicing
        
    return to_return

def get_matches(count, end_index):
    total = 30 #min_matches.free+min_matches.bronze+min_matches.silver+min_matches.gold+min_matches.platinum
    four_days_ago = filter_matches('-4', total, total)
    three_days_ago = filter_matches('-3', total, total)
    two_days_ago = filter_matches('-2', total, total)
    yesterday_matches = filter_matches('-1', total, total)
    today_matches = filter_matches('', count, end_index)
    history = [
        {
            'day': (datetime.now() - timedelta(days=4)).strftime("%A"),
            'matches': sorted(four_days_ago, key=lambda match: match.kickoff) 
        },
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
    
    return today_matches, history
    
 
def get_total_matches():
    total = min_matches.free+min_matches.bronze+min_matches.silver+min_matches.gold+min_matches.platinum
    today_matches = filter_matches('', total, total)
    return len(today_matches)    

@app.route('/', methods=['GET'])
def index():
    today_matches, history = get_matches(30, 30)
    plan = Plan('Free', 0, min_odds.free, 'green', 5, today_matches, history)  
    slips = [
        {
            'id': 1,
            'matches': today_matches[0:6] 
        },
        {
            'id': 2,
            'matches': today_matches[6:12] 
        },
        {
            'id': 3,
            'matches': today_matches[12:18] 
        },
        {
            'id': 4,
            'matches': today_matches[18:24] 
        },
        {
            'id': 5,
            'matches': today_matches[24:30] 
        }
    ]
    return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches(), slips=slips) 

@app.route('/free', methods=['GET'])
def free():
    today_matches, history = get_matches(min_matches.free, min_matches.free)
    plan = Plan('Free', 0, min_odds.free, 'green', 1, today_matches, history)  
    return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches())

@app.route('/bronze', methods=['GET', 'POST'])
def bronze():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        today_matches, history = get_matches(min_matches.bronze, min_matches.free+min_matches.bronze)
        today_matches = today_matches if len(today_matches) > min_matches.free else []
        plan = Plan('Bronze', 20, min_odds.bronze, 'purple', 2, today_matches, history)
        current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
        return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches(), current_time=current_time)

@app.route('/silver', methods=['GET', 'POST'])
def silver():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        today_matches, history = get_matches(min_matches.silver, min_matches.free+min_matches.bronze+min_matches.silver)
        today_matches = today_matches if len(today_matches) > min_matches.bronze else []
        plan = Plan('Silver', 30, min_odds.silver, 'blue', 3, today_matches, history)
        current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
        return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches(), current_time=current_time)

@app.route('/gold', methods=['GET', 'POST'])
def gold():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        today_matches, history = get_matches(min_matches.gold, min_matches.free+min_matches.bronze+min_matches.silver+min_matches.gold)
        today_matches = today_matches if len(today_matches) > min_matches.silver else []
        plan = Plan('Gold', 50, min_odds.gold, 'yellow', 4, today_matches, history)
        current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
        return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches(), current_time=current_time)

@app.route('/platinum', methods=['GET', 'POST'])
def platinum():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        today_matches, history = get_matches(min_matches.platinum, min_matches.free+min_matches.bronze+min_matches.silver+min_matches.gold+min_matches.platinum)
        today_matches = today_matches if len(today_matches) > min_matches.gold else []
        plan = Plan('Platinum', 70, min_odds.platinum, 'pink', 5, today_matches, history)
        current_time = datetime.now(pytz.timezone('Africa/Nairobi'))
        return render_template('plans.html', plan=plan, min_matches=min_matches, min_odds=min_odds, total_matches=get_total_matches(), current_time=current_time)

@app.route('/betika-share-code/<plan_name>', methods=['GET'])
def betika_share_code(plan_name):
    today_matches = []
    if plan_name == 'Free':
        today_matches, history = get_matches(min_matches.free, 4)
    if plan_name == 'Bronze':
        today_matches, history = get_matches(min_matches.bronze, 12)
    if plan_name == 'Silver':
        today_matches, history = get_matches(min_matches.silver, 23)
    if plan_name == 'Gold':
        today_matches, history = get_matches(min_matches.gold, 37)
    if plan_name == 'Platinum':
        today_matches, history = get_matches(min_matches.platinum, 50)
        
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
        plan = 'Bronze' if amount in [20, 100, 300] else 'Silver' if amount in [30, 150, 450] else 'Gold' if amount in [50, 250, 750] else 'Platinum' if amount in [70, 350, 250] else 'Free'
        days = 7 if amount in [100, 150, 250, 350] else 30 if amount in [300, 450, 750, 1050] else 1

        db.update_user_expiry(order_tracking_id, plan, days)

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


