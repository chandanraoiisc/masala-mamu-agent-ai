import re
import logging
from typing import List, Optional
from dataclasses import dataclass

# Playwright for web scraping
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not found. Please install it with: pip install playwright && playwright install")
    PLAYWRIGHT_AVAILABLE = False
    # Dummy classes for testing
    class PlaywrightTimeout(Exception): pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProductOffer:
    platform: str
    price: str
    quantity: str = ""
    def get_numeric_price(self) -> float:
        try:
            price_str = re.sub(r'[^\d.]', '', self.price)
            return float(price_str) if price_str else float('inf')
        except:
            return float('inf')

@dataclass
class Product:
    brand: str
    name: str
    offers: List[ProductOffer]
    def get_cheapest_offer(self) -> Optional[ProductOffer]:
        if not self.offers:
            return None
        return min(self.offers, key=lambda x: x.get_numeric_price())
    def get_most_expensive_offer(self) -> Optional[ProductOffer]:
        if not self.offers:
            return None
        return max(self.offers, key=lambda x: x.get_numeric_price())

class PlatformExtractor:
    PLATFORM_PATTERNS = {
        r'instamart|swiggy': 'Swiggy Instamart',
        r'zepto': 'Zepto',
        r'bbnow|bigbasket': 'BigBasket',
        r'blinkit|grofers': 'Blinkit',
        r'flipkart': 'Flipkart',
        r'amazon': 'Amazon',
        r'myntra': 'Myntra',
        r'jiomart|jio': 'JioMart',
        r'dmart|avenue': 'DMart',
        r'paytm': 'Paytm Mall'
    }
    @classmethod
    def extract_platform_name(cls, img_src: Optional[str], alt_text: Optional[str] = None) -> str:
        if not img_src and not alt_text:
            return "Unknown Platform"
        text_to_search = (img_src or "") + " " + (alt_text or "")
        text_to_search = text_to_search.lower()
        for pattern, platform_name in cls.PLATFORM_PATTERNS.items():
            if re.search(pattern, text_to_search):
                return platform_name
        if img_src:
            filename = img_src.split('/')[-1].split('.')[0]
            return filename.replace('_', ' ').title()
        return alt_text.title() if alt_text else "Unknown Platform"

class QuickCompareScraper:
    BASE_URL = "https://quickcompare.in"
    LOCATION_COORDS = {"latitude": 13.02120018, "longitude": 77.57039642}
    def __init__(self, headless: bool = True, timeout: int = 60000):
        self.headless = headless
        self.timeout = timeout
        self.platform_extractor = PlatformExtractor()
    async def scrape_products(self, query: str, max_cards: int = 5) -> List[Product]:
        logger.info(f"Starting scrape for query: '{query}' with max_cards: {max_cards}")
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, returning dummy data")
            return "Error: Playwright is not installed. Please install it to use this tool."
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                geolocation=self.LOCATION_COORDS,
                permissions=["geolocation"],
                locale="en-IN",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            try:
                return await self._scrape_with_page(page, query, max_cards)
            finally:
                await browser.close()
    async def _scrape_with_page(self, page, query: str, max_cards: int) -> List[Product]:
        try:
            logger.info("Navigating to QuickCompare...")
            await page.goto(self.BASE_URL, timeout=self.timeout)
            await page.wait_for_timeout(2000)
        except PlaywrightTimeout:
            logger.warning("Page load timeout, attempting to continue")
        except Exception as e:
            logger.error(f"Failed to navigate to QuickCompare: {e}")
            return []
        await self._verify_location(page)
        try:
            await self._perform_search(page, query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        await self._scroll_for_more_results(page)
        return await self._extract_products(page, max_cards)
    async def _verify_location(self, page):
        try:
            await page.wait_for_selector("div.truncate", timeout=10000)
            location = await page.inner_text("div.truncate")
            logger.info(f"Location detected: {location.strip()}")
        except PlaywrightTimeout:
            logger.warning("Could not verify location detection")
    async def _perform_search(self, page, query: str):
        logger.info(f"Searching for: {query}")
        search_selectors = [
            'input[placeholder*="compare prices"]',
            'input[type="text"]',
            'input[placeholder*="search"]'
        ]
        search_input = None
        for selector in search_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                search_input = selector
                break
            except PlaywrightTimeout:
                continue
        if not search_input:
            raise Exception("Could not find search input field")
        await page.fill(search_input, query)
        await page.keyboard.press("Enter")
        await page.wait_for_selector('div.flex.flex-col.gap-2.rounded-md.bg-white', timeout=15000)
        await page.wait_for_timeout(2000)
    async def _scroll_for_more_results(self, page, max_attempts: int = 5):
        logger.info("Scrolling to load more results...")
        prev_height = -1
        for attempt in range(max_attempts):
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == prev_height:
                logger.info("Reached end of scrollable content")
                break
            prev_height = current_height
            await page.mouse.wheel(0, current_height)
            await page.wait_for_timeout(1500)
    async def _extract_products(self, page, max_cards: int) -> List[Product]:
        product_locator = page.locator('div.flex.flex-col.gap-2.rounded-md.bg-white')
        total_cards = await product_locator.count()
        logger.info(f"Found {total_cards} product cards, processing up to {min(total_cards, max_cards)}")
        products = []
        for i in range(min(total_cards, max_cards)):
            try:
                product = await self._extract_single_product(product_locator.nth(i))
                if product:
                    products.append(product)
            except Exception as e:
                logger.error(f"Error extracting product {i}: {e}")
                continue
        logger.info(f"Successfully extracted {len(products)} products")
        return products
    async def _extract_single_product(self, card_locator) -> Optional[Product]:
        try:
            brand_element = card_locator.locator('.line-clamp-1')
            brand = await brand_element.inner_text() if await brand_element.count() > 0 else ""
            name_element = card_locator.locator('.line-clamp-2')
            name = await name_element.inner_text() if await name_element.count() > 0 else ""
            offers = await self._extract_offers(card_locator)
            if brand and name and offers:
                return Product(brand=brand.strip(), name=name.strip(), offers=offers)
            logger.warning(f"Incomplete product data: brand='{brand}', name='{name}', offers={len(offers)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting single product: {e}")
            return None
    async def _extract_offers(self, card_locator) -> List[ProductOffer]:
        offers = []
        price_locators = card_locator.locator('span.text-m.font-bold')
        num_prices = await price_locators.count()
        for i in range(num_prices):
            try:
                price_element = price_locators.nth(i)
                price = await price_element.inner_text()
                platform = await self._extract_platform_for_price(price_element)
                if platform and price.strip():
                    offers.append(ProductOffer(platform=platform.strip(), price=price.strip()))
            except Exception as e:
                logger.error(f"Error extracting offer {i}: {e}")
                continue
        return offers
    async def _extract_platform_for_price(self, price_element) -> str:
        try:
            container_locator = price_element.locator(
                'xpath=ancestor::div[contains(@class, "flex") and contains(@class, "w-full") and contains(@class, "items-center")]'
            ).first
            if await container_locator.count() > 0:
                img_locator = container_locator.locator('img')
                if await img_locator.count() > 0:
                    img_src = await img_locator.get_attribute('src')
                    alt_text = await img_locator.get_attribute('alt')
                    return self.platform_extractor.extract_platform_name(img_src, alt_text)
            return "Unknown Platform"
        except Exception as e:
            logger.error(f"Error extracting platform: {e}")
            return "Unknown Platform"

from langchain_core.tools import tool



@tool
async def quickcompare_scraper(query: str, max_cards: int = 5) -> str:
    """
    Uses QuickCompare (quickcompare.in) to search for products and compare prices across various online platforms.
    Provide a concise and specific search query for the product you are looking for (e.g., "milk", "curd", "washing machine LG 7kg").
    The tool returns a formatted string summary of the search results, including product brand, name, and available offers from different platforms with their prices.
    If no relevant results are found, it will indicate that.

    Args:
        query (str): The product you want to search for.
        max_cards (int): The maximum number of distinct product cards to process and return. Defaults to 5 to avoid overly long responses.

    Returns:
        str: A formatted string with product and price comparison results.
    """
    logger.info(f"QuickCompare tool called with query: '{query}', max_cards: {max_cards}")
    scraper = QuickCompareScraper()
    products = await scraper.scrape_products(query, max_cards)
    if not products:
        return f"No comparison results found on QuickCompare for '{query}'. Please try a different or more specific query."
    formatted_output = f"QuickCompare Results for '{query}' (showing top {len(products)} results):\n\n"
    for product in products:
        formatted_output += f"Brand: {product.brand}\n"
        formatted_output += f"Product: {product.name}\n"
        formatted_output += "Offers:\n"
        if product.offers:
            for offer in product.offers:
                # Extract quantity from product name if available
                quantity = ""
                if "pieces" in product.name.lower():
                    quantity = product.name.split("pieces")[0].strip().split()[-1]
                elif "kg" in product.name.lower():
                    quantity = product.name.split("kg")[0].strip().split()[-1] + "kg"
                elif "g" in product.name.lower():
                    quantity = product.name.split("g")[0].strip().split()[-1] + "g"
                elif "l" in product.name.lower():
                    quantity = product.name.split("l")[0].strip().split()[-1] + "L"
                
                if quantity:
                    formatted_output += f"  - {offer.platform}: {offer.price} ({quantity})\n"
                else:
                    formatted_output += f"  - {offer.platform}: {offer.price}\n"
        else:
            formatted_output += "  No offers found for this product.\n"
        formatted_output += "---\n"
    logger.info(f"Generated formatted output for {len(products)} products")
    return formatted_output.strip()