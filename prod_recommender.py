import numpy as np
import torch
from transformers import pipeline
from amazon_scraper import scrape_amazon
import re

device = 0 if torch.cuda.is_available() else -1

sentiment_model = pipeline("sentiment-analysis", model='distilbert-base-uncased-finetuned-sst-2-english', device=device)

def analyze_sentiment_bert(text):
    result = sentiment_model(text)[0]
    label = result["label"].upper()
    score = result["score"] if label == "POSITIVE" else (1 - result["score"])
    return score

def process_products(search_term):

    data = scrape_amazon(search_term)

    for product in data:
        # product["rating_count"] = int(product['ratingcount'].replace(',', '').replace(' ratings', ''))
        rating_text  = product['ratingcount']
        rating_number = int(re.sub(r'[^0-9]', '', rating_text)) 
        product["rating_count"] = rating_number
        ratings = [float(review['rating'].replace(' out of 5 stars', '')) for review in product['topreviews']]
        product["avg_rating"] = sum(ratings) / len(ratings) if ratings else 0

        sentiment_scores = [analyze_sentiment_bert(review["title"]) for review in product["topreviews"]]
        product["sentiment_score"] = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

    sorted_products = sorted(data, key=lambda x: (x['avg_rating'], x['rating_count']), reverse=True)

    max_rating_count = max([product['rating_count'] for product in sorted_products])
    for product in sorted_products:
        norm_rating_count = product["rating_count"] / max_rating_count
        final_score = (product["sentiment_score"] * 0.7) + (norm_rating_count * 0.3)
        product["final_score"] = final_score

    sorted_products = sorted(sorted_products, key=lambda x: x["final_score"], reverse=True)
    best_product = sorted_products[0]

    print("**Best Recommendation:**")
    print(f"{best_product['productname']}")
    print(f"Rating Average: {best_product['avg_rating']}")
    print(f"Rating Count: {best_product['rating_count']}")
    print(f"Sentiment Score: {best_product['sentiment_score']}")
    print(f"Final Score: {best_product['final_score']:.4f}")


if __name__ == "__main__":
    search_query = input("Search Term: ")
    process_products(search_query)