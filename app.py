
import os
from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user
from flask_session import Session
from redis import Redis
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit, pytz

#from broadcast_w import BroadcastW
from utils.helper import Helper
from utils.pesapal import Pesapal
from utils.postgres_crud import PostgresCRUD
#from utils.safaricom.utils import Utils

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # One year in seconds

# Load environment variables from .env file
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(
    host=os.getenv('REDIS_HOSTNAME'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_SSL') in ['True', '1'] else None,
    ssl=False if os.getenv('REDIS_SSL') in ['False', '0'] else True
)

app.config['SESSION_COOKIE_SECURE'] = True  # Set to True if using HTTPS on Vercel
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


db = PostgresCRUD()
helper = Helper()

# Set the timezone to Africa/Nairobi globally
os.environ['TZ'] = 'Africa/Nairobi'

def predict():
    print("Running prediction...")
    # Add your prediction logic here

# Define the timezone
nairobi_tz = pytz.timezone('Africa/Nairobi')

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(predict, trigger=CronTrigger(hour=14, minute=53, timezone=nairobi_tz))
scheduler.start()

# Ensure scheduler shuts down properly on exit
atexit.register(lambda: scheduler.shutdown())

waapi_instance_id = os.getenv('WAAPI_INSTANCE_ID')
waapi_token = os.getenv('WAAPI_TOKEN')


def login():           
    phone = request.form['phone']
    user = db.get_user(phone=phone)
    
    if user:      
        login_user(user)
        if user.active:
            return redirect(url_for('today'))       
    else:
        db.add_user(phone)
        user = db.get_user(phone=phone)
        login_user(user)

    return redirect(url_for('subscribe'))
    
# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return db.get_user(user_id=user_id)

@app.errorhandler(404)
def page_not_found(e):
    # Redirect to a specific endpoint, like 'today', or a custom 404 page
    return redirect(url_for('today'), 302)

@app.route('/home', methods=['GET', 'POST'])
def home(): 
    # if request.method == 'POST': 
    #     login()
    # matches, played, won = helper.fetch_matches('', '=', '')
    return render_template('home.html')

@app.route('/today', methods=['GET', 'POST'])
def today(): 
    if request.method == 'POST': 
        login()
    matches, played, won = helper.fetch_matches('', '=', '')
    return render_template('index.html', header="Today Games Predictions", matches=matches, played=played, won=won)

@app.route('/tomorrow', methods=['GET', 'POST'])
def tomorrow():    
    if request.method == 'POST': 
        login()
    matches, played, won = helper.fetch_matches('+1', '=', '')
    return render_template('index.html', header="Tomorrow Games Predictions", matches = matches, played = played, won = won)

@app.route('/yesterday', methods=['GET', 'POST'])
def yesterday():    
    if request.method == 'POST': 
        login()
    matches, played, won = helper.fetch_matches('-1', '=')
    return render_template('index.html', header="Yesterday's Predictions Results", matches = matches, played = played, won = won)

@app.route('/history', methods=['GET', 'POST'])
def history():    
    if request.method == 'POST': 
        login()
    matches, played, won = helper.fetch_matches('', '<')
    return render_template('index.html', header="Last 100 Predicted Games Results", matches = matches, played = played, won = won )

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():   
    if request.method == 'POST':  
        phone = current_user.phone[-9:]
        amount = int(request.form['amount'])
        order_details = Pesapal().submit_order_request(phone, amount)
        order_tracking_id = order_details.get('order_tracking_id')
        db.insert_transaction(order_tracking_id, current_user.id, amount)
        return render_template('pay.html', order_tracking_id=order_tracking_id)

    return render_template('subscribe.html')

@app.route('/pesapal-callback', methods=['GET', 'POST'])
def pesapal_callback():   
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
        days = 30 if amount == 500 else 7 if amount == 150 else 1 if amount == 30 else int(amount/30)
        db.update_user_expiry(order_tracking_id, days)

    return redirect(url_for('today'))   

@app.route('/terms-and-conditions')
def terms_and_conditions():    
    return render_template('terms-and-conditions.html')

@app.route('/privacy-policy')
def privacy_policy():    
    return render_template('privacy-policy.html')

@app.route(f'/webhooks/whatsapp/<security_token>', methods=['POST'])
def handle_webhook(security_token):
    data = request.get_json()

    if not data or 'instanceId' not in data or 'event' not in data or 'data' not in data:
        print('Invalid request')
        return '', 400

    instance_id = data['instanceId']
    event_name = data['event']
    event_data = data['data']

    # check if the security token and the instanceId match in our records
    if str(instance_id) != waapi_instance_id  or waapi_token != security_token:
        print('Authentication failed')
        return '', 401

    # the request is validated and the requester authenticated
    if event_name == 'message':
        message_data = event_data['message']
        message_type = message_data['type']
        
        if message_type == 'chat':
            message_sender_id = message_data['from']  # unique WhatsApp ID
            message_created_at = datetime.fromtimestamp(message_data['timestamp'])  # timestamp is in seconds
            message_content = message_data['body']

            # this is the phone number of the message sender
            message_sender_phone_number = message_sender_id #.replace('@c.us', '')
            
            # run your business logic: someone has sent you a WhatsApp message
                
            if 'unsubscribe' in message_content.lower():
                db.add_or_remove_subscriber(message_sender_phone_number, 2)                
                #BroadcastW().send_goodbye_message(message_sender_phone_number)        

            elif 'subscribe' in message_content.lower():
                db.add_or_remove_subscriber(message_sender_phone_number, 1)
                #BroadcastW().send_welcome_message(message_sender_phone_number)

        return '', 200
    else:
        print(f"Cannot handle this event: {event_name}")
        return '', 404

@app.route('/games_callback', methods=['POST'])
def delivery_reports():
    response = None #Utils().get_callback()
    
    print(response) 
    
    db.save_safaricom_callback(str(response))
    
    if response["success"]:
        for datum in response["data"]["requestParam"]["data"]:
            if datum["name"] == "Msisdn":
                phone = datum["value"]
                db.update_subscriber_on_send(phone) 
    
    return '', 200

@app.route('/webhooks/sms', methods=['POST'])
def handle_sms_webhook():
    data = request.get_json()
    payload = str(data)

    # the request is validated and the requester authenticated
    if data:         
        db.insert_sms(payload)

        return '', 200
    else:
        print("Cannot handle this request")
        return '', 404
    
if __name__ == '__main__':
    debug_mode = os.getenv('IS_DEBUG', 'False') in ['True', '1', 't']
    app.run(debug=debug_mode)