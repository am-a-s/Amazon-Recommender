from requests_html import HTMLSession
import pandas as pd

# headers for handel errors
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/'
}

def get_asins(search):
    url = f'https://www.amazon.co.uk/s?k={search}'
    r = s.get(url, headers=headers)
    # print(r.html.find('div.s-main-slot.s-result-list div[data-asin]'))
    asins = r.html.find('div.s-main-slot.s-result-list div[data-asin]')
    return [asin.attrs['data-asin'] for asin in asins if asin.attrs['data-asin'] != '']

# print(get_asins('nmve'))

def get_data(asin):
    url = f'https://www.amazon.co.uk/dp/{asin}'
    r = s.get(url, headers=headers)
    productname = r.html.find('#productTitle', first=True).full_text.strip()
    rating_element = r.html.find('#acrCustomerReviewText', first=True)
    reviews = r.html.find('li[data-hook=review]')

    ratingcount = "0"
    if rating_element:
        ratingcount = rating_element.full_text.strip()

    topreviews = []
    for rev in reviews:
        title_elements = rev.find('a[data-hook=review-title] span', first=False)
        if title_elements:  # Ensure there is at least one element
            review_title = title_elements[-1].text
            rating_element = rev.find('i[data-hook=review-star-rating] span', first=True)
            if rating_element:
                rating = rating_element.full_text
                ratings = {
                    'title': review_title,
                    'rating': rating,
                }
                topreviews.append(ratings)

    product = {
        'productname': productname,
        'ratingcount': ratingcount,
        'topreviews': topreviews
    }

    return product

def scrape_amazon(search):
    # search = input('Enter search term: ')
    asins = get_asins(search)
    print(f'Found {len(asins)} asins')
    results = [get_data(asin) for asin in asins]
    # df = pd.DataFrame(results)
    # df.to_json(search + ".json", orient="records", indent=4)
    return results

s = HTMLSession()