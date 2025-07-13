from fastapi import FastAPI
from transformers import pipeline
import aiohttp
import asyncio
import torch
from bs4 import BeautifulSoup
import logging
import pandas as pd
import os

app = FastAPI()
device = 0 if torch.cuda.is_available() else -1
sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    device=device,
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
}


async def fetch_page(session, url):
    async with session.get(url, headers=headers) as response:
        return await response.text()


async def get_asins(search):
    url = f"https://www.amazon.co.uk/s?k={search}"
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, url)
    soup = BeautifulSoup(html, "html.parser")
    asins = [
        div["data-asin"]
        for div in soup.select("div.s-main-slot div[data-asin]")
        if div["data-asin"]
    ]
    return asins


async def get_data(asin):
    url = f"https://www.amazon.co.uk/dp/{asin}"
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, url)

    soup = BeautifulSoup(html, "html.parser")
    productname = soup.select_one("#productTitle")
    rating_element = soup.select_one("#acrCustomerReviewText")
    reviews = soup.select("li[data-hook=review]")

    productname = productname.text.strip() if productname else "Unknown Product"
    ratingcount = rating_element.text.strip() if rating_element else "0"

    topreviews = []
    for rev in reviews:
        title_element = rev.select_one("a[data-hook=review-title] span")
        rating_element = rev.select_one("i[data-hook=review-star-rating] span")
        if title_element and rating_element:
            topreviews.append(
                {
                    "title": title_element.text.strip(),
                    "rating": rating_element.text.strip(),
                }
            )

    return {
        "productname": productname,
        "ratingcount": ratingcount,
        "topreviews": topreviews,
    }


async def analyze_sentiment_bert(text):
    result = sentiment_model(text)[0]
    label = result["label"].upper()
    score = result["score"] if label == "POSITIVE" else (1 - result["score"])
    return score


async def get_best_product(search_term):
    asins = await get_asins(search_term)
    if not asins:
        return None

    tasks = [get_data(asin) for asin in asins]
    products = await asyncio.gather(*tasks)
    products = [p for p in products if p]
    if not products:
        return None

    for product in products:
        product["rating_count"] = int(
            product["ratingcount"]
            .replace(",", "")
            .replace(" ratings", "")
            .replace(" rating", "")
        )
        ratings = [
            float(review["rating"].replace(" out of 5 stars", ""))
            for review in product["topreviews"]
            if "out of 5 stars" in review["rating"]
        ]
        product["avg_rating"] = sum(ratings) / len(ratings) if ratings else 0
        sentiment_scores = await asyncio.gather(
            *(
                analyze_sentiment_bert(review["title"])
                for review in product["topreviews"]
            )
        )
        product["sentiment_score"] = (
            sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        )

    sorted_products = sorted(
        products, key=lambda x: (x["avg_rating"], x["rating_count"]), reverse=True
    )
    max_rating_count = max(
        [product["rating_count"] for product in sorted_products], default=1
    )
    for product in sorted_products:
        norm_rating_count = (
            product["rating_count"] / max_rating_count if max_rating_count else 0
        )
        product["final_score"] = (product["sentiment_score"] * 0.7) + (
            norm_rating_count * 0.3
        )

    sorted_products = sorted(
        sorted_products, key=lambda x: x["final_score"], reverse=True
    )
    save_scraped_data(sorted_products, search_term)
    print("saved")

    return sorted_products[0] if sorted_products else None


@app.get("/")
async def recommend(search_term: str):
    logging.info(f"Received request for: {search_term}")
    best_product = await get_best_product(search_term)
    if not best_product:
        return {"error": "No products found for this search term."}
    return {
        "productname": best_product["productname"],
        "final_score": best_product["final_score"],
        "rating_avg": best_product["avg_rating"],
        "rating_count": best_product["rating_count"],
        "sentiment_score": best_product["sentiment_score"],
    }


def save_scraped_data(products, search_term):
    # Ensure the directory exists
    directory = r"E:/University/MLOpsPath/proj_1/Amazon_scraper"
    os.makedirs(directory, exist_ok=True)

    # Create a DataFrame from the products list
    df = pd.DataFrame(products)
    # Save the data to a JSON file
    df.to_json(f"{directory}/{search_term}.json", orient="records", indent=4)
