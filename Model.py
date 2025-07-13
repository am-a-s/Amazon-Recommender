import json
import numpy as np
import torch
from transformers import pipeline
from amazon_scraper import scrape_amazon

sentiment_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

def analyze_sentiment_bert(text):
    result = sentiment_model(text)[0]
    label = result["label"].upper()
    score = result["score"] if label == "POSITIVE" else (1 - result["score"])
    return score


with open(r'E:\University\MLOpsPath\proj_1\Amazon_scraper\electric guitar.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

for product in data:
    product["rating_count"] = int(product['ratingcount'].replace(',', '').replace(' ratings', ''))

    ratings = [float(review['rating'].replace(' out of 5 stars', '')) for review in product['topreviews']]
    product["avg_rating"] = sum(ratings) / len(ratings) if ratings else 0

    sentiment_scores = [analyze_sentiment_bert(review["title"]) for review in product["topreviews"]]
    product["sentiment_score"] = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

def get_top_products(data, top_n=6):
    sorted_products = sorted(data, key=lambda x: (x['avg_rating'], x['rating_count'])[:top_n], reverse=True)
    return sorted_products[:top_n]

top_products = get_top_products(data)

max_rating_count = max([product['rating_count'] for product in top_products])

for product in top_products:
    norm_rating_count = product["rating_count"] / max_rating_count
    final_score = (product["sentiment_score"] * 0.7) + (norm_rating_count * 0.3)
    product["final_score"] = final_score

sorted_products = sorted(top_products, key=lambda x: x["final_score"], reverse=True)
best_product = sorted_products[0]

print("**Best Recommendation:**")
print(f"{best_product['productname']}")
print(f"Rating Average: {best_product['avg_rating']}")
print(f"Rating Count: {best_product['rating_count']}")
print(f"Sentiment Score: {best_product['sentiment_score']}")
print(f"Final Score: {best_product['final_score']:.4f}")

# for product in top_products:
#     print(f"product reviews: {product['productname']}")
#     print(f"rating average: {product['avg_rating']}")
#     print(f"rating count: {product['rating_count']}")
#     print(f"sentiment score: {product['sentiment_score']}")