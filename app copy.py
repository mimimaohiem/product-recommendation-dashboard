from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from recommendation_module import prepare_recommendation
import pandas as pd

scheduler = APScheduler()
app = Flask(__name__, template_folder='site')
CORS(app)

# Pre-requisites - data connection/loading
dataset_root = 'static/dataset/'  
# Loading customer interaction data
customer_interactions_df = pd.read_csv(f"{dataset_root}generated_customer_interactions.csv")
customer_interactions_df.columns = ['customer_id', 'customer_page_views', 'customer_time_spent']
# Loading product details data
product_details_df = pd.read_csv(f"{dataset_root}generated_product_details.csv", sep=";")
product_details_df.columns = ['product_id', 'product_category', 'product_price', 'product_ratings']
# Loading purchasing history data
purchase_history_df = pd.read_csv(f"{dataset_root}generated_purchase_history.csv", sep=";")

# Create initial recommendation index for each user
# Faster latency if we provide the recommendation data first - no need to do calculation every request
recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)

# Scheduler - Update recommendation index every N Hour - in this case, there are no data update (static dataset)
# Threshold for the similarity between user purchasing behaviour is setted to 0.3
@scheduler.task('cron', id='update_dict_job', hour='*/12')
def scheduled_job():
    # The result of this recommendation index update will store to global recommendation_index variable
    global recommendation_index
    recommendation_index = prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3)

@app.route('/')
def home():
    # Root route will show the simple dashboard to get the product recommendation of each user based on their purchasing behaviour
    # To get the recommendation data for each user, in index.html will hit to `/recommendation/<int:customer_id>`
    return render_template('index.html')

@app.route('/recommendation/<int:customer_id>', methods=['GET'])
def recommendation(customer_id):
    global recommendation_index
    try:
        # Try to get the recommendation from recommendation index
        response = recommendation_index[customer_id]
    except:
        # If failed or no data found in recommendation index, it will return no data like below
        response = {
            'customer_id' : customer_id,
            'history' : [],
            'recommendation' : []
        }
    return jsonify(response)

if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)