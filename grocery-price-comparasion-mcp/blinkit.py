import asyncio
from playwright.async_api import async_playwright

async def scroll_to_bottom(page):
    """Scrolls to the bottom of the page until no more content loads."""
    previous_height = await page.evaluate("document.body.scrollHeight")
    
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)  # Wait for potential lazy-loading

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height

async def scrape_blinkit_prices(url):
    """Scrapes product names and prices from a Blinkit category page."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for production
        page = await browser.new_page()

        await page.goto(url, timeout=90000)
        await scroll_to_bottom(page)

        # Wait for at least one ₹ price element to appear
        await page.wait_for_selector("text=₹", timeout=20000)

        # Select all product blocks that contain ₹
        products = await page.query_selector_all("div:has-text('₹')")

        found = 0
        for block in products:
            raw_text = await block.inner_text()
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

            if len(lines) >= 2:
                name = lines[0]
                price = next((l for l in lines if '₹' in l), 'N/A')
                print(f"{name} — {price}")
                found += 1

        print(f"\n✅ Extracted {found} products successfully.")
        await browser.close()

# Run the scraper
asyncio.run(scrape_blinkit_prices("https://blinkit.com/cn/milk/cid/14/922"))
