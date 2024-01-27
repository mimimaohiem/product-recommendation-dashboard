import pandas as pd

def prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3, n_recommendation=20):
  # Extend information for purchasing history data with customer_interactions data and product_details data
  dataset = pd.merge(purchase_history_df, customer_interactions_df, on='customer_id', how='left')
  dataset = pd.merge(dataset, product_details_df, on='product_id', how='left')
  # Select feature that important to the pipeline used
  dataset = dataset[['customer_id', 'product_id', 'product_ratings']]

  # Craete pivot table to get summary of product rating by each user
  ratings_matrix_fillna = pd.pivot_table(dataset, index='customer_id', columns='product_id', values='product_ratings')
  # Normalize the value of the ratings - mean-centered overlapping-item - better result - sum all without NaN - Substract the initial value with it
  # Do nothing to NaN value - user not rated the product yet or never seen it before
  ratings_matrix_fillna_norm = ratings_matrix_fillna.subtract(ratings_matrix_fillna.mean(axis=1), axis=0)
  # Tranpose the matrix to switch the rows and columns to create correlation data between user - .corr() are comparing columns
  # Get the correaltion for each user to other user based on their purchasing history
  customer_similarity_matrix = ratings_matrix_fillna_norm.T.corr()

  # list all unique customer_id
  customer_list = list(set(customer_interactions_df['customer_id']))
  # Variable to store recommendation index for every user
  customers_recommendation_lists = {}
  for customer_id in customer_list:
    # Drop row with initial customer_id - customer_id that will be created the recommendation
    customer_similarity_matrix_comparison = customer_similarity_matrix.copy()
    customer_similarity_matrix_comparison.drop(index=customer_id, inplace=True)
    # Find the similar to the user - having high correlated/similar purchasing history vector above threshold
    similar_customer = customer_similarity_matrix_comparison[customer_similarity_matrix_comparison[customer_id]>threshold][customer_id]

    # Get purchasing history for initial customer_id
    customer_id_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index == customer_id].dropna(axis=1, how='all')
    # Get purchasing history for similar customer to initial customer_id, drop product/column with all user never purchased
    similar_customer_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index.isin(similar_customer.index)].dropna(axis=1, how='all')
    # Drop product/columns that have been purchased by initial customer
    similar_customer_purchased.drop(customer_id_purchased.columns, axis=1, inplace=True, errors='ignore')

    # Get product_id and sort by the mean of similarity score from each user, dont include the NaN value
    recommendation_list = [(product, similar_customer_purchased[product].dropna(axis=0).mean()) for product in similar_customer_purchased]
    recommendation_list = sorted(recommendation_list, key=lambda x: x[1], reverse=True)

    # Prepare the purchasing history for initial customer_id
    history = []
    for product in list(customer_id_purchased.columns):
      details = product_details_df[product_details_df['product_id'] == product]
      product_details = {
          'product_id' : details.values[0][0],
          'product_category' : details.values[0][1],
          'product_price' : details.values[0][2],
          'product_rating' : details.values[0][3],

      }
      history.append(product_details)
    
    # Prepare the recommendation data for initial customer_id
    recommendation = []
    for product in recommendation_list[:n_recommendation]:
      details = product_details_df[product_details_df['product_id'] == product[0]]
      product_details = {
          'product_id' : details.values[0][0],
          'product_category' : details.values[0][1],
          'product_price' : details.values[0][2],
          'product_rating' : details.values[0][3],
      }
      recommendation.append(product_details)

    # Store to form dictionary
    recommendation_for_a_customer = {
      'customer_id' : customer_id,
      'history' : history,
      'recommendation' : recommendation
    }
    # Store recommendation data for each customer to dictionary/database - recommendation index
    customers_recommendation_lists[customer_id] = recommendation_for_a_customer
  
  return customers_recommendation_lists