import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_swiggy_instamart(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, timeout=90000)

        # Scroll to bottom to load all content
        previous_height = await page.evaluate("document.body.scrollHeight")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height

        # ✅ Find all product prices by test-id
        price_elements = await page.query_selector_all('[data-testid="item-offer-price"]')
        name_elements = await page.query_selector_all('div[class*="_1sPB0"]')


        # Initialize lists to store the data
        prices = []
        descriptions = []
        reasons = []
        product_names = []

        # Extract prices
        for elem in price_elements:
            price = await elem.get_attribute("aria-label") or await elem.inner_text()
            price = price.strip()
            if not price.startswith("₹"):
                price = "₹" + price
            prices.append(price.strip())

        # Extract descriptions (if available)   
        for elem in name_elements:
            name = await elem.inner_text()
            product_names.append(name)

        # Combine into JSON structure
        products = []
        max_length = max(len(prices), len(descriptions), len(reasons), len(product_names))

        for i in range(max_length):
            product = {
                "product name": product_names[i] if i < len(product_names) else None,
                "price": prices[i] if i < len(prices) else None,
            }
            products.append(product)

        # Create final JSON structure
        result = {
            "products": products,
            }

        # Convert to JSON and print
        json_result = json.dumps(result, indent=2, ensure_ascii=False)
        print("\n" + "="*50)
        print("SCRAPED DATA AS JSON:")
        print("="*50)
        print(json_result)

        # with open('swiggy_products.json', 'w', encoding='utf-8') as f:
        #     f.write(json_result)
        
        # print(f"\n✅ Data saved to 'swiggy_products.json'")

        await browser.close()
        
        # Return the JSON data
        return result

# Run this with Swiggy Instamart URL
if __name__ == "__main__":
    scraped_data = asyncio.run(scrape_swiggy_instamart("https://www.swiggy.com/instamart/campaign-collection/listing?collectionId=193535&custom_back=true&layoutId=12601"))
    
    for product in scraped_data['products'][:3]:  # Show first 3 products
        print(f"Product Name: {product['product name']} - Price: {product['price']}")