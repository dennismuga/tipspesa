
from flask import Flask, render_template
from utils.pesapal import Pesapal

app = Flask(__name__)

@app.route('/')
def index():
    phone = '254759697757'
    amount = 20
    order_details = Pesapal().submit_order_request(phone, amount)
    order_tracking_id = order_details.get('order_tracking_id')
    return render_template('pesapal.html', order_tracking_id=order_tracking_id)

if __name__ == '__main__':
    app.run(debug=True)