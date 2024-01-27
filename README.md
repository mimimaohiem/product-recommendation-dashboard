# **Case Study: Predictive Analytics for E-commerce**

## **Business Context:**
You are hired as a Data Science and AI for an e-commerce company named "Terra Store." Terra Store is looking to enhance its marketing strategy by predicting customer purchase behavior based on historical data. The company wants to build an AI-powered application that can provide insights into which products a customer is likely to purchase next.

## **Problem Statement:**
Terra Store has provided you with a dataset containing information about customer interactions, purchases, and product details. Your task is to develop a web-based AI application that predicts the next product a customer is likely to buy. The application should be user-friendly, allowing marketing teams to target customers more effectively.

## **Data Description:**
The dataset includes the following information:
- Customer Interactions:
- Customer ID
- Page views
- Time spent on the website

Purchase History:
- Customer ID
- Product ID
- Purchase date
- Product Details:
- Product ID
- Category
- Price
- Ratings

**customer_interactions.csv** includes information about customer interactions on the website, such as the number of page views and time spent.

**purchase_history.csv** contains records of customer purchases, including the product purchased and the date of purchase.

**product_details.csv** provides details about each product, such as its category, price, and ratings.

> Generated data used are created with `notebook/Dataset Generation.ipynb`

## **Model Development Approach**
In the creation of a recommendation system leveraging purchasing history similarity vectors for each customer, the development approach focuses on meticulously analyzing and encoding individual buying patterns, effectively transforming them into comprehensive vectors that encapsulate user preferences and behaviors, thereby enabling the system to generate personalized and relevant product recommendations tailored to each customer's unique shopping history and preferences.

Example Data:
```txt
Product ID | 101| 102| 103| 104| 105|
-------------------------------------
Customer ID--------------------------
A          |   1|    |    |   1|   3|
B          |   1|    |    |    |   4|
C          |    |   3|    |    |    |
D          |   2|   2|    |    |    |
E          |    |   4|   4|    |    |
```

Simple Vector Illustration:
```
A - {1,0,0,1,3}
B - {1,0,0,0,4}
C - {0,3,0,0,0}
D - {2,2,0,0,0}
E - {0,4,4,0,0}
```

In this simple vector illustration, each customer is represented by a unique set of values, denoting their behavior or preferences across different product categories. The vectors A, B, C, D, and E represent Customer IDs, and each element in the vector signifies the level of engagement or interest in a specific product category.

The primary objective is to compare the vectors for each Customer ID to identify the most similar behaviors among them. By computing correlations between the vectors, the system can pinpoint the customer with the highest correlation, indicating a significant similarity in their preferences. Once the most correlated customer is identified, further analysis is conducted to recommend products. However, a crucial condition is imposed: the recommended products must exclude those already purchased by the selected customer ID. This approach ensures that the recommendations are tailored to the individual's preferences while avoiding redundant suggestions of previously acquired items.

# **Evaluation**

The evaluation of the recommendation system involves computing the nDCG@5 metric, where the relevance scores are determined by assigning a score of 1 for each product category that exists in the purchasing history, multiplied by the number of occurrences of the same product category in the purchasing history. For product categories that do not exist in the purchasing history, a score of 0 is assigned. The resulting scores are organized into a list representing the predicted relevance. The nDCG@5 is then calculated by comparing this list with the sorted list of true relevance, sorted in descending order of relevance scores, to assess the system's performance in recommending relevant products.

The NDCG@5 Score is `0.8484064772401175`. Check on `notebook/Case_Study_Predictive_Analytics_for_E_Commerce.ipynb`

# **Live Dashboard**

URL: https://product-recommendation-dashboard.vercel.app/

# **Live Dashboard Architecture Design**

![Architecture](https://raw.githubusercontent.com/hanifabd/product-recommendation-dashboard/master/static/img/architecture-webapp.png)

# Run in Local
1. Create python environment
2. Install `requirements.txt` in that python environment
3. run `python app.py`