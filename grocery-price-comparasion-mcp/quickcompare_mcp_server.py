#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import json
import logging
import sys
import asyncio
import traceback
import re
from typing import List, Optional
from dataclasses import dataclass

# Setup MCP Server
mcp = FastMCP("QuickCompare") #

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Playwright for web scraping
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True #
    logger.info("Playwright is available")
except ImportError:
    logger.warning("Playwright not found. Please install it with: pip install playwright && playwright install")
    PLAYWRIGHT_AVAILABLE = False
    # Dummy classes for testing - KEPT for robustness/development ease even if Playwright is expected
    class PlaywrightTimeout(Exception): pass
    class DummyPlaywright:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def chromium(self): return DummyBrowser()
    class DummyBrowser:
        async def launch(self, headless=True): return DummyContext()
        async def close(self): pass
    class DummyContext:
        async def new_context(self, **kwargs): return self
        async def new_page(self): return DummyPage()
        async def close(self): pass
    class DummyPage:
        async def goto(self, url, timeout=None): logging.info(f"Dummy: Navigating to {url}")
        async def wait_for_selector(self, selector, timeout=None): logging.info(f"Dummy: Waiting for {selector}")
        async def inner_text(self, selector): return "Hyderabad, Telangana"
        async def fill(self, selector, value): logging.info(f"Dummy: Filling {selector} with {value}")
        def keyboard(self): return DummyKeyboard()
        async def wait_for_timeout(self, ms): import asyncio; await asyncio.sleep(ms / 1000)
        async def evaluate(self, script): return 1000
        def mouse(self): return DummyMouse()
        def locator(self, selector): return DummyLocator()
    class DummyKeyboard:
        async def press(self, key): logging.info(f"Dummy: Pressing {key}")
    class DummyMouse:
        async def wheel(self, x, y): logging.info(f"Dummy: Scrolling by {y}")
    class DummyLocator:
        def __init__(self, count=3): self._count = count
        async def count(self): return self._count
        def nth(self, n): return self
        async def inner_text(self): dummy_responses = ["Fresho", "Farm Fresh Eggs 6 pieces", "₹48", "₹52", "₹45"]; return dummy_responses[n % len(dummy_responses)]
        async def get_attribute(self, attr): return "blinkit_logo.png"
    async_playwright = DummyPlaywright

# Data classes #
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

# Platform extractor #
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

# Main scraper class #
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
            # _generate_dummy_data is still called here for the dummy path
            return self._generate_dummy_data(query, max_cards)
        
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
                
                # Try to extract quantity information
                quantity = await self._extract_quantity_for_price(price_element, card_locator)
                
                if platform and price.strip():
                    offers.append(ProductOffer(
                        platform=platform.strip(), 
                        price=price.strip(),
                        quantity=quantity.strip() if quantity else ""
                    ))
            except Exception as e:
                logger.error(f"Error extracting offer {i}: {e}")
                continue
        
        return offers
    
    async def _extract_quantity_for_price(self, price_element, card_locator) -> str:
        """
        Try to extract quantity information from the product card.
        This method uses multiple strategies to find quantity information.
        """
        try:
            logger.debug("Starting quantity extraction")
            
            # Strategy 1: Check all text content in the entire product card
            card_text = await card_locator.inner_text()
            logger.debug(f"Full card text: {card_text}")
            
            # Strategy 2: Look for quantity in the product name first
            name_element = card_locator.locator('.line-clamp-2')
            if await name_element.count() > 0:
                name_text = await name_element.inner_text()
                logger.debug(f"Product name: {name_text}")
                
                # Enhanced regex patterns for quantity extraction
                quantity_patterns = [
                    r'(\d+(?:\.\d+)?\s*(?:ml|ML))',  # milliliters
                    r'(\d+(?:\.\d+)?\s*(?:g|G|gm|GM|gms|GMS))',  # grams
                    r'(\d+(?:\.\d+)?\s*(?:kg|KG|Kg))',  # kilograms
                    r'(\d+(?:\.\d+)?\s*(?:l|L|ltr|LTR|litre|LITRE|litres|LITRES))',  # liters
                    r'(\d+\s*(?:pieces|piece|pcs|PCS|pc|PC))',  # pieces
                    r'(\d+\s*(?:pack|packs|PACK|PACKS))',  # packs
                    r'(\d+\s*(?:nos|NOS|no|NO))',  # numbers
                    r'(\d+\s*(?:units|unit|UNIT|UNITS))',  # units
                    r'(\d+\s*(?:eggs|egg|EGG|EGGS))',  # for eggs specifically
                ]
                
                for pattern in quantity_patterns:
                    match = re.search(pattern, name_text, re.IGNORECASE)
                    if match:
                        quantity = match.group(1).strip()
                        logger.debug(f"Found quantity in name: {quantity}")
                        return quantity
            
            # Strategy 3: Look for quantity in other text elements within the card
            text_elements = await card_locator.locator('span, div, p').all()
            for element in text_elements:
                try:
                    element_text = await element.inner_text()
                    if element_text:
                        # Check if this text contains quantity information
                        for pattern in [
                            r'(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|litre|pieces|pcs|pack|nos|units|eggs))',
                            r'(\d+\s*(?:pieces|pcs|eggs|pack))',
                        ]:
                            match = re.search(pattern, element_text, re.IGNORECASE)
                            if match:
                                quantity = match.group(1).strip()
                                logger.debug(f"Found quantity in element: {quantity}")
                                return quantity
                except:
                    continue
            
            # Strategy 4: Look near the price element specifically
            try:
                container_locator = price_element.locator('xpath=ancestor::div[1]')
                if await container_locator.count() > 0:
                    container_text = await container_locator.inner_text()
                    logger.debug(f"Price container text: {container_text}")
                    
                    # Search for quantity in the price container
                    quantity_pattern = r'(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|litre|pieces|pcs|pack|nos|units|eggs))'
                    match = re.search(quantity_pattern, container_text, re.IGNORECASE)
                    if match:
                        quantity = match.group(1).strip()
                        logger.debug(f"Found quantity near price: {quantity}")
                        return quantity
            except Exception as e:
                logger.debug(f"Error checking price container: {e}")
            
            # Strategy 5: Extract from full card text as last resort
            quantity_pattern = r'(\d+(?:\.\d+)?\s*(?:ml|g|kg|l|litre|pieces|pcs|pack|nos|units|eggs))'
            match = re.search(quantity_pattern, card_text, re.IGNORECASE)
            if match:
                quantity = match.group(1).strip()
                logger.debug(f"Found quantity in full card text: {quantity}")
                return quantity
            
            logger.debug("No quantity found using any strategy")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting quantity: {e}")
            return ""
    
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
    
    # This method is still needed because the `scrape_products` method calls it when PLAYWRIGHT_AVAILABLE is False.
    # It provides dummy data for local testing/development without Playwright.
    def _generate_dummy_data(self, query: str, max_cards: int) -> List[Product]:
        logger.info("Generating dummy data for testing")
        dummy_products = [
            Product(
                brand="Fresho",
                name="Farm Fresh Eggs 6 pieces",
                offers=[
                    ProductOffer(platform="BigBasket", price="₹48", quantity="6 pieces"),
                    ProductOffer(platform="Blinkit", price="₹52", quantity="6 pieces"),
                    ProductOffer(platform="Zepto", price="₹45", quantity="6 pieces")
                ]
            ),
            Product(
                brand="Happy Hens",
                name="Brown Eggs 12 pieces",
                offers=[
                    ProductOffer(platform="Swiggy Instamart", price="₹85", quantity="12 pieces"),
                    ProductOffer(platform="JioMart", price="₹88", quantity="12 pieces"),
                    ProductOffer(platform="BigBasket", price="₹82", quantity="12 pieces")
                ]
            ),
            Product(
                brand="Country Eggs",
                name="Organic White Eggs 10 pieces",
                offers=[
                    ProductOffer(platform="Blinkit", price="₹95", quantity="10 pieces"),
                    ProductOffer(platform="Zepto", price="₹92", quantity="10 pieces")
                ]
            )
        ]
        return dummy_products[:min(len(dummy_products), max_cards)]

# MCP Tools #
@mcp.tool()
async def quickcompare_scraper(query: str, max_cards: int = 5) -> str:
    """
    Scrape product data using QuickCompare and return formatted results.
    
    Args:
        query: The product search query (e.g., "patato", "milk", "eggs")
        max_cards: Maximum number of product cards to scrape (default: 5, max: 20)
    
    Returns:
        JSON string with scraped product data or error information
    """
    # Validate inputs
    if not query or not query.strip():
        return json.dumps({
            "success": False,
            "error": "invalid_input",
            "message": "Query cannot be empty"
        })
    
    if max_cards < 1 or max_cards > 20:
        max_cards = min(max(max_cards, 1), 20)
    
    logger.info(f"MCP Tool called - Scraping for query: '{query}' with max_cards: {max_cards}")
    
    try:
        # Create scraper instance with headless mode
        scraper = QuickCompareScraper(headless=True) #
        
        logger.info("Scraper initialized, starting product scraping...")
        products = await scraper.scrape_products(query, max_cards)

        if not products:
            logger.warning(f"No products found for query: '{query}'")
            return json.dumps({
                "success": False,
                "message": f"No products found for '{query}'. Please try a different search term.",
                "query": query,
                "total_products": 0,
                "products": []
            }, indent=2, ensure_ascii=False)

        # Format the products response
        response = format_products_response(products, query) #
        logger.info(f"Successfully scraped {len(products)} products for '{query}'")
        return response

    except ImportError as e:
        error_msg = f"Missing dependencies: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "success": False,
            "error": "dependency_missing",
            "message": error_msg,
            "suggestion": "Please install missing dependencies: pip install playwright && playwright install"
        }, indent=2, ensure_ascii=False)
    
    except Exception as e:
        error_msg = f"Scraping error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Check if it's a Playwright-specific error
        if "BrowserType.launch" in str(e) or "playwright" in str(e).lower():
            return json.dumps({
                "success": False,
                "error": "browser_setup_error",
                "message": "Browser dependencies are missing. Please run: sudo playwright install-deps",
                "technical_details": str(e)
            }, indent=2, ensure_ascii=False)
        
        return json.dumps({
            "success": False,
            "error": "scraping_error",
            "message": error_msg,
            "query": query
        }, indent=2, ensure_ascii=False)

def format_products_response(products: list, query: str) -> str:
    """
    Format products into a structured response with proper Unicode handling.
    """
    response = {
        "success": True,
        "query": query,
        "total_products": len(products),
        "products": [],
    }

    for product in products:
        product_data = {
            "brand": getattr(product, 'brand', ''),
            "name": getattr(product, 'name', ''),
            "offers": [],
        }

        offers = getattr(product, 'offers', [])
        for offer in offers:
            offer_data = {
                "platform": getattr(offer, 'platform', ''),
                "price": getattr(offer, 'price', ''),
                "quantity": getattr(offer, 'quantity', ''),
                "numeric_price": getattr(offer, 'get_numeric_price', lambda: None)() if hasattr(offer, 'get_numeric_price') else None,
            }
            product_data["offers"].append(offer_data)

        response["products"].append(product_data)

    # Use ensure_ascii=False to properly handle Unicode characters like ₹
    return json.dumps(response, indent=2, ensure_ascii=False)

# Add a health check tool #
@mcp.tool()
async def health_check() -> str:
    """
    Check if the MCP server and dependencies are working correctly.
    """
    try:
        import playwright
        return json.dumps({
            "status": "healthy" if PLAYWRIGHT_AVAILABLE else "partial",
            "message": "MCP server is running and dependencies are available" if PLAYWRIGHT_AVAILABLE else "MCP server running but Playwright not available",
            "playwright_available": PLAYWRIGHT_AVAILABLE,
            "playwright_version": getattr(playwright, '__version__', 'unknown') if PLAYWRIGHT_AVAILABLE else None,
            "tools_available": ["quickcompare_scraper", "health_check", "echo"]
        }, indent=2, ensure_ascii=False)
    except ImportError as e:
        return json.dumps({
            "status": "unhealthy",
            "message": f"Missing dependencies: {str(e)}",
            "playwright_available": False,
            "suggestion": "Install playwright: pip install playwright && playwright install"
        }, indent=2, ensure_ascii=False)

# Add a simple test tool for connectivity #
@mcp.tool()
async def echo(message: str = "Hello from MCP server!") -> str:
    """
    Simple echo tool to test MCP connectivity.
    
    Args:
        message: Message to echo back
    
    Returns:
        The same message with a timestamp
    """
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    return json.dumps({
        "echo": message,
        "timestamp": timestamp,
        "server": "QuickCompare MCP Server"
    }, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    try:
        logger.info("Starting QuickCompare MCP Server (Integrated)...") #
        logger.info("Available tools: quickcompare_scraper, health_check, echo") #
        
        # Run the MCP server #
        mcp.run(transport="stdio") #
        
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}", exc_info=True)
        sys.exit(1)