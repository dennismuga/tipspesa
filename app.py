
import os
from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_session import Session
from redis import Redis
from dotenv import load_dotenv

from utils.entities import Plan
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
login_manager.login_view = 'home'

db = PostgresCRUD()
helper = Helper()

matches = helper.fetch_matches('', '=', '', limit=16)
lm = len(matches)
matches_yesterday = helper.fetch_matches('-1', '=', '', limit=16)
lmy = len(matches_yesterday)
        
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

# Initialize scheduler
# scheduler = BackgroundScheduler()

# # Schedule the task to run every 120 seconds
# scheduler.add_job(func=update_stats, trigger="interval", seconds=60)
# scheduler.add_job(func=predict_and_bet, trigger="interval", seconds=120)
        
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
    # Redirect to a specific endpoint, like 'home', or a custom 404 page
    return redirect(url_for('home'), 302)

def filter_matches(matches, size):
    filtered_matches = []
    for match in matches:
        # Check if home_team or away_team is already in matches_platinum
        is_duplicate = any(
            match.home_team in m.home_team and match.away_team in m.away_team for m in filtered_matches
        )
        if not is_duplicate:
            filtered_matches.append(match)
    
    filtered_matches = filtered_matches[-4:] if size == 4 and len(filtered_matches) >= 1 else filtered_matches
    filtered_matches = filtered_matches[:size] if len(filtered_matches) >= 1 else filtered_matches
    return filtered_matches

@app.route('/', methods=['GET'])
def free():
    plan = Plan('Free Tips', 0, 3, 'pink', 1, filter_matches(matches, 4), filter_matches(matches_yesterday, 4))
    return render_template('plans.html', plan=plan)

@app.route('/bronze', methods=['GET', 'POST'])
def bronze():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        plan = Plan('Bronze Plan', 20, 5, 'purple', 2, filter_matches(matches, 6), filter_matches(matches_yesterday, 6))
        return render_template('plans.html', plan=plan)

@app.route('/silver', methods=['GET', 'POST'])
def silver():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        plan = Plan('Silver Plan', 30, 10, 'blue', 3, filter_matches(matches, 8), filter_matches(matches_yesterday, 8))
        return render_template('plans.html', plan=plan)

@app.route('/gold', methods=['GET', 'POST'])
def gold():
    if request.method == 'POST': 
        return subscribe()
    
    else:        
        plan = Plan('Gold Plan', 50, 15, 'yellow', 4, filter_matches(matches, 10), filter_matches(matches_yesterday, 10))
        return render_template('plans.html', plan=plan)
                
@app.route('/platinum', methods=['GET', 'POST'])
def platinum():
    if request.method == 'POST': 
        return subscribe()
    
    else:                
        plan = Plan('Platinum Plan', 70, 20, 'green', 5, filter_matches(matches, 12), filter_matches(matches_yesterday, 12))
        return render_template('plans.html', plan=plan)

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
    
    # Start the scheduler
    # scheduler.start()
    
    # Run the Flask app
    app.run(debug=debug_mode)