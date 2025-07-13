import asyncio
import aiohttp
from selectolax.parser import   # سریع‌تر از requests_html

async def fetch(session, url):
    async with session.get(url) as response:
        html_content = await response.text()
        return HTML(html_content)  # پارس کردن HTML سریع‌تر از requests_html

async def get_data_async(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results

# تست برای چندین محصول
urls = ["https://www.amazon.com/dp/B09BG8YB58", "https://www.amazon.com/dp/B08G8YYR9T"]
html_results = asyncio.run(get_data_async(urls))

for html in html_results:
    title = html.css_first("#productTitle").text()  # استخراج اطلاعات با selectolax
    print("Title:", title)
