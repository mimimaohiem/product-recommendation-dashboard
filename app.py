from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from recommendation_module import prepare_recommendation
import pandas as pd

scheduler = APScheduler()
app = Flask(__name__, template_folder='site')
CORS(app)

# Pre-Requisites
dataset_root = 'static/dataset/'  
customer_interactions_df = pd.read_csv(f"{dataset_root}generated_customer_interactions.csv")
customer_interactions_df.columns = ['customer_id', 'customer_page_views', 'customer_time_spent']
product_details_df = pd.read_csv(f"{dataset_root}generated_product_details.csv", sep=";")
product_details_df.columns = ['product_id', 'product_category', 'product_price', 'product_ratings']
purchase_history_df = pd.read_csv(f"{dataset_root}generated_purchase_history.csv", sep=";")

recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)
@scheduler.task('cron', id='update_dict_job', hour='*/12')
def scheduled_job():
    global recommendation_index
    recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommendation/<int:customer_id>', methods=['GET'])
def recommendation(customer_id):
    global recommendation_index
    try:
        response = recommendation_index[customer_id]
    except:
        response = {
            'customer_id' : customer_id,
            'history' : [],
            'recommendation' : []
        }
    return jsonify(response)

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)