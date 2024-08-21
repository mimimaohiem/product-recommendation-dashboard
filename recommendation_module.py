import pandas as pd

def prepare_recommendation(customer_interactions_df, product_details_df, purchase_history_df, threshold=0.3, n_recommendation=20):
    # Extend information for purchasing history data with customer_interactions data and product_details data
    dataset = pd.merge(purchase_history_df, customer_interactions_df, on='customer_id', how='left')
    dataset = pd.merge(dataset, product_details_df, on='product_id', how='left')
    # Select feature that is important to the pipeline used
    dataset = dataset[['customer_id', 'product_id', 'product_ratings']]

    # Create pivot table to get a summary of product ratings by each user
    ratings_matrix_fillna = pd.pivot_table(dataset, index='customer_id', columns='product_id', values='product_ratings')

    # Normalize the value of the ratings - mean-centered overlapping-item - better result - sum all without NaN - Subtract the initial value with it
    ratings_matrix_fillna_norm = ratings_matrix_fillna.subtract(ratings_matrix_fillna.mean(axis=1), axis=0)

    # Transpose the matrix to switch the rows and columns to create correlation data between users
    customer_similarity_matrix = ratings_matrix_fillna_norm.T.corr()

    # List all unique customer_id
    customer_list = list(set(customer_interactions_df['customer_id']))
    # Variable to store recommendation index for every user
    customers_recommendation_lists = {}
    for customer_id in customer_list:
        # Drop row with initial customer_id - customer_id that will be created the recommendation
        customer_similarity_matrix_comparison = customer_similarity_matrix.copy()
        customer_similarity_matrix_comparison.drop(index=customer_id, inplace=True)
        
        # Find similar users - having highly correlated/similar purchasing history vector above threshold
        similar_customer = customer_similarity_matrix_comparison[customer_similarity_matrix_comparison[customer_id] > threshold][customer_id]

        # Get purchasing history for the initial customer_id
        customer_id_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index == customer_id].dropna(axis=1, how='all')
        # Get purchasing history for similar customers, drop products/columns where no user has purchased
        similar_customer_purchased = ratings_matrix_fillna_norm[ratings_matrix_fillna_norm.index.isin(similar_customer.index)].dropna(axis=1, how='all')
        # Drop products that have already been purchased by the initial customer
        similar_customer_purchased.drop(customer_id_purchased.columns, axis=1, inplace=True, errors='ignore')

        # Get product_id and sort by the mean of similarity score from each user, don't include NaN values
        recommendation_list = [(product, similar_customer_purchased[product].dropna(axis=0).mean()) for product in similar_customer_purchased]
        recommendation_list = sorted(recommendation_list, key=lambda x: x[1], reverse=True)

        # Prepare the purchasing history for the initial customer_id
        history = []
        for product in list(customer_id_purchased.columns):
            details = product_details_df[product_details_df['product_id'] == product]
            product_details = {
                'product_id': int(details.values[0][0]),  # Convert to int
                'product_category': details.values[0][1],
                'product_price': float(details.values[0][2]),  # Convert to float
                'product_rating': float(details.values[0][3]),  # Convert to float
            }
            history.append(product_details)

        # Prepare the recommendation data for the initial customer_id
        recommendation = []
        for product in recommendation_list[:n_recommendation]:
            details = product_details_df[product_details_df['product_id'] == product[0]]

            # Get the list of similar customers and their similarity scores for this product
            similar_customers_for_product = [
                {"customer_id": int(similar_customer_id), "similarity_score": round(float(similarity_score), 2)}
                for similar_customer_id, similarity_score in similar_customer.items()
                if product[0] in ratings_matrix_fillna.loc[similar_customer_id].dropna().index
            ]

            product_details = {
                'product_id': int(details.values[0][0]),  # Convert to int
                'product_category': details.values[0][1],
                'product_price': float(details.values[0][2]),  # Convert to float
                'product_rating': float(details.values[0][3]),  # Convert to float
                'score': round(product[1], 2),  # Add the score here
                'similar_customers': similar_customers_for_product
            }
            recommendation.append(product_details)

        # Store the recommendation data for each customer to the dictionary/database - recommendation index
        recommendation_for_a_customer = {
            'customer_id': int(customer_id),  # Convert to int
            'history': history,
            'recommendation': recommendation
        }

        customers_recommendation_lists[customer_id] = recommendation_for_a_customer

    return customers_recommendation_lists
