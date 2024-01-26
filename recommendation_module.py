import pandas as pd

def prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3, n_recommendation=20):
  dataset = pd.merge(purchase_history_df, customer_interactions_df, on='customer_id', how='left')
  dataset = pd.merge(dataset, product_details_df, on='product_id', how='left')
  dataset = dataset[['customer_id', 'product_id', 'product_ratings']]

  ratings_matrix_fillna = pd.pivot_table(dataset, index='customer_id', columns='product_id', values='product_ratings')
  ratings_matrix_fillna_norm = ratings_matrix_fillna.subtract(ratings_matrix_fillna.mean(axis=1), axis=0)
  customer_similarity_matrix = ratings_matrix_fillna_norm.T.corr()

  customer_list = list(set(customer_interactions_df['customer_id']))
  customers_recommendation_lists = {}
  for customer_id in customer_list:
    customer_similarity_matrix_comparison = customer_similarity_matrix.copy()
    customer_similarity_matrix_comparison.drop(index=customer_id, inplace=True)

    similar_customer = customer_similarity_matrix_comparison[customer_similarity_matrix_comparison[customer_id]>threshold][customer_id]
    customer_id_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index == customer_id].dropna(axis=1, how='all')
    similar_customer_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index.isin(similar_customer.index)].dropna(axis=1, how='all')
    similar_customer_purchased.drop(customer_id_purchased.columns, axis=1, inplace=True, errors='ignore')

    recommendation_list = [(product, similar_customer_purchased[product].dropna(axis=0).mean()) for product in similar_customer_purchased]
    recommendation_list = sorted(recommendation_list, key=lambda x: x[1], reverse=True)

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

    recommendation_for_a_customer = {
      'customer_id' : customer_id,
      'history' : history,
      'recommendation' : recommendation
    }
    customers_recommendation_lists[customer_id] = recommendation_for_a_customer
  
  return customers_recommendation_lists