from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from recommendation_module import prepare_recommendation
import MySQLdb
import pandas as pd

scheduler = APScheduler()
app = Flask(__name__, template_folder='site')
CORS(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'recommendation'
app.config['MYSQL_PASSWORD'] = '123456a'
app.config['MYSQL_DB'] = 'recommendation_db'

mysql = MySQLdb.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    passwd=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

def load_data_from_db():
    cursor = mysql.cursor()

    # Loading customer interaction data
    cursor.execute("SELECT customer_id, customer_page_views, customer_time_spent FROM customer_interactions")
    customer_interactions = cursor.fetchall()
    customer_interactions_df = pd.DataFrame(customer_interactions, columns=['customer_id', 'customer_page_views', 'customer_time_spent'])

    # Loading product details data
    cursor.execute("SELECT product_id, product_category, product_price, product_ratings FROM product_details")
    product_details = cursor.fetchall()
    product_details_df = pd.DataFrame(product_details, columns=['product_id', 'product_category', 'product_price', 'product_ratings'])

    # Loading purchasing history data
    cursor.execute("SELECT customer_id, product_id, purchase_date FROM purchase_history")
    purchase_history = cursor.fetchall()
    purchase_history_df = pd.DataFrame(purchase_history, columns=['customer_id', 'product_id', 'purchase_date'])

    cursor.close()

    return customer_interactions_df, product_details_df, purchase_history_df

# Load initial data from the database
customer_interactions_df, product_details_df, purchase_history_df = load_data_from_db()

# Create initial recommendation index for each user
recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)

# Scheduler to update recommendation index every N hours
@scheduler.task('cron', id='update_dict_job', hour='*/12')
def scheduled_job():
    global recommendation_index
    customer_interactions_df, product_details_df, purchase_history_df = load_data_from_db()
    recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommendation/<int:customer_id>', methods=['GET'])
def recommendation(customer_id):
    global recommendation_index

    # Get customer information from the users table
    user_info = get_user_info(customer_id)

    if not user_info:
        return jsonify({
            'error': 'User not found'
        }), 404

    # Fetch recommendation data
    try:
        response = recommendation_index[customer_id]
    except KeyError:
        response = {
            'customer_id': customer_id,
            'history': [],
            'recommendation': [],
            'similar_customers': []
        }

    # Combine customer info with recommendation data
    response['user_info'] = user_info

    # Retrieve similar customers' detailed info
    similar_customer_ids = [sc['customer_id'] for r in response['recommendation'] for sc in r.get('similar_customers', [])]
    response['similar_customers'] = get_similar_customers_info(similar_customer_ids)

    return jsonify(response)

def get_user_info(customer_id):
    cursor = mysql.cursor()
    query = "SELECT customer_id, name, email, phone FROM users WHERE customer_id = %s"
    cursor.execute(query, (customer_id,))
    user_info = cursor.fetchone()
    cursor.close()

    if user_info:
        return {
            'customer_id': user_info[0],
            'name': user_info[1],
            'email': user_info[2],
            'phone': user_info[3]
        }
    else:
        return None

def get_similar_customers_info(customer_ids):
    if not customer_ids:
        return []

    cursor = mysql.cursor()
    format_strings = ','.join(['%s'] * len(customer_ids))

    # Query to get customer info and count of purchases from purchase_history
    query = f"""
        SELECT u.customer_id, u.name, COUNT(ph.product_id) as purchased_items
        FROM users u
        LEFT JOIN purchase_history ph ON u.customer_id = ph.customer_id
        WHERE u.customer_id IN ({format_strings})
        GROUP BY u.customer_id, u.name
    """
    cursor.execute(query, tuple(customer_ids))
    similar_customers = cursor.fetchall()
    cursor.close()

    return [
        {
            'customer_id': customer[0],
            'name': customer[1],
            'purchased_items': customer[2]  # The count of purchases
        } for customer in similar_customers
    ]

@app.route('/customer-stats/<int:customer_id>', methods=['GET'])
def customer_stats(customer_id):
    cursor = mysql.cursor()

    # Fetch customer interactions data (page views and time spent)
    cursor.execute("""
        SELECT customer_page_views, customer_time_spent
        FROM customer_interactions
        WHERE customer_id = %s
    """, (customer_id,))
    interactions = cursor.fetchone()

    if not interactions:
        return jsonify({"error": "Customer interactions not found"}), 404

    # Fetch number of products purchased from purchase_history
    cursor.execute("""
        SELECT COUNT(product_id)
        FROM purchase_history
        WHERE customer_id = %s
    """, (customer_id,))
    purchases = cursor.fetchone()

    cursor.close()

    if purchases is None:
        return jsonify({"error": "No purchase history found"}), 404

    # Prepare the response data
    response = {
        "customer_id": customer_id,
        "customer_page_views": interactions[0],
        "customer_time_spent": interactions[1],
        "products_purchased": purchases[0]
    }

    return jsonify(response)

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)
