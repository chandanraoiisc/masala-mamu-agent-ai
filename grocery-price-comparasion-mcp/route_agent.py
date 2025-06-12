import asyncio
import re
import logging
from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator
from dataclasses import dataclass

# LangChain/LangGraph imports
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Playwright for web scraping
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not found. Please install it with: pip install playwright && playwright install")
    PLAYWRIGHT_AVAILABLE = False
    
    #  dummy classes for better testing
    class PlaywrightTimeout(Exception):
        pass
    
    class DummyPlaywright:
        async def ____end____(self): return self
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
        async def goto(self, url, timeout=None): 
            logging.info(f"Dummy: Navigating to {url}")
        async def wait_for_selector(self, selector, timeout=None): 
            logging.info(f"Dummy: Waiting for {selector}")
        async def inner_text(self, selector): return "Hyderabad, Telangana"
        async def fill(self, selector, value): 
            logging.info(f"Dummy: Filling {selector} with {value}")
        def keyboard(self): return DummyKeyboard()
        async def wait_for_timeout(self, ms): await asyncio.sleep(ms / 1000)
        async def evaluate(self, script): return 1000
        def mouse(self): return DummyMouse()
        def locator(self, selector): return DummyLocator()
    
    class DummyKeyboard:
        async def press(self, key): 
            logging.info(f"Dummy: Pressing {key}")
    
    class DummyMouse:
        async def wheel(self, x, y): 
            logging.info(f"Dummy: Scrolling by {y}")
    
    class DummyLocator:
        def __init__(self, count=3): self._count = count
        async def count(self): return self._count
        def nth(self, n): return self
        async def inner_text(self): 
            dummy_responses = ["Fresho", "Farm Fresh Eggs 6 pieces", "₹48", "₹52", "₹45"]
            return dummy_responses[n % len(dummy_responses)]
        async def get_attribute(self, attr): return "blinkit_logo.png"
    
    async_playwright = DummyPlaywright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProductOffer:
    """Represents a single offer for a product"""
    platform: str
    price: str
    
    def get_numeric_price(self) -> float:
        """Extract numeric price for comparison"""
        try:
            # Remove currency symbols and extract numbers
            price_str = re.sub(r'[^\d.]', '', self.price)
            return float(price_str) if price_str else float('inf')
        except:
            return float('inf')
    
@dataclass
class Product:
    """Represents a product with its offers"""
    brand: str
    name: str
    offers: List[ProductOffer]
    
    def __post_init__(self):
        """Validate product data"""
        if not self.brand or not self.name:
            raise ValueError("Product must have both brand and name")
        if not self.offers:
            logger.warning(f"Product {self.brand} {self.name} has no offers")
    
    def get_cheapest_offer(self) -> Optional[ProductOffer]:
        """Get the cheapest offer for this product"""
        if not self.offers:
            return None
        return min(self.offers, key=lambda x: x.get_numeric_price())
    
    def get_most_expensive_offer(self) -> Optional[ProductOffer]:
        """Get the most expensive offer for this product"""
        if not self.offers:
            return None
        return max(self.offers, key=lambda x: x.get_numeric_price())

class PlatformExtractor:
    """Utility class for extracting platform names from various sources"""
    
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
        """Extract platform name from image source or alt text"""
        if not img_src and not alt_text:
            return "Unknown Platform"
        
        text_to_search = (img_src or "") + " " + (alt_text or "")
        text_to_search = text_to_search.lower()
        
        for pattern, platform_name in cls.PLATFORM_PATTERNS.items():
            if re.search(pattern, text_to_search):
                return platform_name
        
        # Fallback: extract from filename
        if img_src:
            filename = img_src.split('/')[-1].split('.')[0]
            return filename.replace('_', ' ').title()
        
        return alt_text.title() if alt_text else "Unknown Platform"

class QuickCompareScraper:
    """ scraper for QuickCompare.in with better error handling and structure"""
    
    BASE_URL = "https://quickcompare.in"
    LOCATION_COORDS = {"latitude": 13.02120018, "longitude": 77.57039642}  # Bangalore IISc
    
    def __init__(self, headless: bool = True, timeout: int = 60000):
        self.headless = headless
        self.timeout = timeout
        self.platform_extractor = PlatformExtractor()
    
    async def scrape_products(self, query: str, max_cards: int = 5) -> List[Product]:
        """
        Scrape product information from QuickCompare
        
        Args:
            query: Search term for products
            max_cards: Maximum number of product cards to scrape
            
        Returns:
            List of Product objects
        """
        logger.info(f"Starting scrape for query: '{query}' with max_cards: {max_cards}")
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, returning dummy data")
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
        """Internal method to handle scraping with a page object"""
        
        # Navigate to the site
        try:
            logger.info("Navigating to QuickCompare...")
            await page.goto(self.BASE_URL, timeout=self.timeout)
            await page.wait_for_timeout(2000)
        except PlaywrightTimeout:
            logger.warning("Page load timeout, attempting to continue")
        except Exception as e:
            logger.error(f"Failed to navigate to QuickCompare: {e}")
            return []
        
        # Verify location detection
        await self._verify_location(page)
        
        # Perform search
        try:
            await self._perform_search(page, query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        
        # Load more results by scrolling
        await self._scroll_for_more_results(page)
        
        # Extract product data
        return await self._extract_products(page, max_cards)
    
    async def _verify_location(self, page):
        """Verify that location was detected correctly"""
        try:
            await page.wait_for_selector("div.truncate", timeout=10000)
            location = await page.inner_text("div.truncate")
            logger.info(f"Location detected: {location.strip()}")
        except PlaywrightTimeout:
            logger.warning("Could not verify location detection")
    
    async def _perform_search(self, page, query: str):
        """Perform the search operation"""
        logger.info(f"Searching for: {query}")
        
        # Find and fill search input
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
        
        # Wait for results
        await page.wait_for_selector('div.flex.flex-col.gap-2.rounded-md.bg-white', timeout=15000)
        await page.wait_for_timeout(2000)
    
    async def _scroll_for_more_results(self, page, max_attempts: int = 5):
        """Scroll to load more results"""
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
        """Extract product information from the page"""
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
        """Extract information from a single product card"""
        try:
            # Extract brand
            brand_element = card_locator.locator('.line-clamp-1')
            brand = await brand_element.inner_text() if await brand_element.count() > 0 else ""
            
            # Extract name
            name_element = card_locator.locator('.line-clamp-2')
            name = await name_element.inner_text() if await name_element.count() > 0 else ""
            
            # Extract offers
            offers = await self._extract_offers(card_locator)
            
            if brand and name and offers:
                return Product(brand=brand.strip(), name=name.strip(), offers=offers)
            
            logger.warning(f"Incomplete product data: brand='{brand}', name='{name}', offers={len(offers)}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting single product: {e}")
            return None
    
    async def _extract_offers(self, card_locator) -> List[ProductOffer]:
        """Extract all offers from a product card"""
        offers = []
        price_locators = card_locator.locator('span.text-m.font-bold')
        num_prices = await price_locators.count()
        
        for i in range(num_prices):
            try:
                price_element = price_locators.nth(i)
                price = await price_element.inner_text()
                
                # Find platform information
                platform = await self._extract_platform_for_price(price_element)
                
                if platform and price.strip():
                    offers.append(ProductOffer(platform=platform.strip(), price=price.strip()))
                
            except Exception as e:
                logger.error(f"Error extracting offer {i}: {e}")
                continue
        
        return offers
    
    async def _extract_platform_for_price(self, price_element) -> str:
        """Extract platform name for a given price element"""
        try:
            # Navigate to the container with platform image
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
    
    def _generate_dummy_data(self, query: str, max_cards: int) -> List[Product]:
        """Generate dummy data when Playwright is not available"""
        logger.info("Generating dummy data for testing")
        
        dummy_products = [
            Product(
                brand="Fresho",
                name="Farm Fresh Eggs 6 pieces",
                offers=[
                    ProductOffer(platform="BigBasket", price="₹48"),
                    ProductOffer(platform="Blinkit", price="₹52"),
                    ProductOffer(platform="Zepto", price="₹45")
                ]
            ),
            Product(
                brand="Happy Hens",
                name="Brown Eggs 12 pieces",
                offers=[
                    ProductOffer(platform="Swiggy Instamart", price="₹85"),
                    ProductOffer(platform="JioMart", price="₹88"),
                    ProductOffer(platform="BigBasket", price="₹82")
                ]
            ),
            Product(
                brand="Country Eggs",
                name="Organic White Eggs 10 pieces",
                offers=[
                    ProductOffer(platform="Blinkit", price="₹95"),
                    ProductOffer(platform="Zepto", price="₹92")
                ]
            )
        ]
        
        return dummy_products[:min(len(dummy_products), max_cards)]

# ---  Tool Definition ---
@tool
async def quickcompare_scraper(query: str, max_cards: int = 5) -> str:
    """
    Uses QuickCompare (quickcompare.in) to search for products and compare prices across various online platforms.
    Returns detailed product information with price analysis including cheapest and most expensive options.

    Args:
        query (str): The product you want to search for.
        max_cards (int): The maximum number of distinct product cards to process and return. Defaults to 5.
    """
    logger.info(f"QuickCompare tool called with query: '{query}', max_cards: {max_cards}")
    
    scraper = QuickCompareScraper()
    products = await scraper.scrape_products(query, max_cards)
    
    if not products:
        return f"No comparison results found on QuickCompare for '{query}'. Please try a different or more specific query."
    
    #  formatting with price analysis
    formatted_output = f"🛒 PRICE COMPARISON RESULTS FOR '{query.upper()}'\n"
    formatted_output += "=" * 50 + "\n\n"
    
    # Find overall best deals
    all_offers = []
    for product in products:
        for offer in product.offers:
            all_offers.append((product, offer))
    
    if all_offers:
        # Sort by price for overall cheapest
        all_offers.sort(key=lambda x: x[1].get_numeric_price())
        cheapest_overall = all_offers[0]
        
        formatted_output += f"🏆 BEST DEAL OVERALL:\n"
        formatted_output += f"   {cheapest_overall[0].brand} {cheapest_overall[0].name}\n"
        formatted_output += f"   💰 {cheapest_overall[1].price} on {cheapest_overall[1].platform}\n\n"
    
    formatted_output += "📋 DETAILED COMPARISON:\n"
    formatted_output += "-" * 30 + "\n\n"
    
    for i, product in enumerate(products, 1):
        formatted_output += f"{i}. {product.brand} - {product.name}\n"
        
        if product.offers:
            # Sort offers by price for this product
            sorted_offers = sorted(product.offers, key=lambda x: x.get_numeric_price())
            cheapest = sorted_offers[0]
            most_expensive = sorted_offers[-1] if len(sorted_offers) > 1 else None
            
            formatted_output += f"   💚 CHEAPEST: {cheapest.price} on {cheapest.platform}\n"
            
            if most_expensive and most_expensive != cheapest:
                formatted_output += f"   💸 MOST EXPENSIVE: {most_expensive.price} on {most_expensive.platform}\n"
                
                # Calculate savings
                try:
                    savings = most_expensive.get_numeric_price() - cheapest.get_numeric_price()
                    if savings > 0:
                        formatted_output += f"   💡 SAVINGS: ₹{savings:.0f} by choosing {cheapest.platform}\n"
                except:
                    pass
            
            formatted_output += f"   📊 ALL PRICES:\n"
            for offer in sorted_offers:
                formatted_output += f"      • {offer.platform}: {offer.price}\n"
        else:
            formatted_output += "   ❌ No offers found for this product.\n"
        
        formatted_output += "\n"
    
    # Add summary
    if len(products) > 1:
        formatted_output += "💡 SHOPPING TIP:\n"
        formatted_output += f"Found {len(products)} different products. Compare per-unit prices for the best value!\n"
    
    logger.info(f"Generated  formatted output for {len(products)} products")
    return formatted_output.strip()

# --- LangGraph State ---
class AgentState(TypedDict):
    """Represents the state of our LangGraph agent"""
    messages: Annotated[List[BaseMessage], operator.add]

# ---  Agent Configuration ---
class PriceComparisonAgent:
    """ agent class with better prompt engineering"""
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,  # Lower temperature for more consistent responses
            google_api_key=google_api_key
        )
        self.tools = [quickcompare_scraper]
        self.tool_node = ToolNode(self.tools)
        self.app = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_llm)
        workflow.add_node("call_tool", self.tool_node)
        workflow.add_node("end_summary", lambda state: state)
        
        # Define edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._decide_next_step,
            {
                "call_tool": "call_tool",
                "end_summary": "end_summary"
            }
        )
        workflow.add_edge("call_tool", "agent")
        workflow.add_edge("end_summary", END)
        
        return workflow.compile()
    
    def _get__system_prompt(self) -> str:
        """Return  system prompt with better instructions"""
        return """You are Masala Mamu, a friendly and expert price comparison assistant specializing in helping users find the best deals on grocery and household items in India.

WHEN TO USE TOOLS:
- Use the quickcompare_scraper tool when users ask about product prices, price comparisons, or want to find deals
- Keywords that indicate price queries: "price", "cost", "compare", "cheaper", "expensive", "deal", "offer", "how much"

YOUR RESPONSE STYLE:
✅ DO:
- Always provide clear, actionable recommendations
- Highlight the BEST DEAL prominently with emojis
- Explain WHY something is the best choice (price, convenience, savings)
- Use a friendly, conversational tone with appropriate emojis
- Format responses in a scannable way with clear sections
- Calculate and mention savings when applicable
- Give practical shopping advice

❌ DON'T:
- Just list prices without analysis
- Use overly technical language
- Give generic responses without specific recommendations
- Ignore the user's intent to find the best deal

RESPONSE FORMAT FOR PRICE QUERIES:
1. Start with a brief acknowledgment of their query
2. Present the tool results in a user-friendly format
3. Clearly highlight the BEST DEAL with reasoning
4. Provide additional context or shopping tips if helpful
5. End with a helpful suggestion or question

NON-PRICE QUERIES:
For questions unrelated to price comparison, respond helpfully without using tools, maintaining your friendly Masala Mamu personality.

Remember: Your goal is to save users money and time by providing clear, actionable price comparison insights!"""
    
    async def _call_llm(self, state: AgentState) -> Dict[str, List[BaseMessage]]:
        """Node that invokes the LLM to get a response or tool call"""
        logger.info("Calling LLM (Agent Node)")
        messages = state["messages"]
        
        # Add  system message if this is the first call
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            system_message = HumanMessage(content=self._get__system_prompt())
            messages = [system_message] + messages
        
        llm_with_tools = self.llm.bind_tools(self.tools)
        response = await llm_with_tools.ainvoke(messages)
        logger.info(f"LLM Response type: {type(response)}")
        
        return {"messages": [response]}
    
    def _decide_next_step(self, state: AgentState) -> str:
        """Determine the next step based on LLM's response"""
        logger.info("Deciding next step...")
        
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            tool_name = last_message.tool_calls[0]['name']
            logger.info(f"LLM wants to call tool: {tool_name}")
            return "call_tool"
        else:
            logger.info("LLM has final answer, ending graph")
            return "end_summary"
    
    async def run(self, question: str) -> Optional[str]:
        """Run the agent for a given question"""
        logger.info(f"Running agent for question: '{question}'")
        
        inputs = {"messages": [HumanMessage(content=question)]}
        
        try:
            final_state = None
            async for step in self.app.astream(inputs):
                logger.debug(f"Step keys: {list(step.keys())}")
                # Keep track of the latest state
                for key, value in step.items():
                    if key != "__end__":
                        final_state = value
                
                if "__end__" in step:
                    final_state = step["__end__"]
                    break
            
            if final_state and final_state.get("messages"):
                # Find the last AI message
                for message in reversed(final_state["messages"]):
                    if hasattr(message, 'content') and isinstance(message.content, str) and message.content.strip():
                        # Skip tool calls, return actual content
                        if not (hasattr(message, 'tool_calls') and message.tool_calls):
                            logger.info("Found final AI response")
                            return message.content
                
                # Fallback: return the last message content
                last_message = final_state["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    return last_message.content
            
            logger.warning("Agent finished without clear final answer")
            return None
            
        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            return None

# --- Main Execution Functions ---
async def run_price_agent(user_question: str, api_key: str) -> str:
    """
    Run the  price comparison agent with the given user question and API key.
    
    Args:
        user_question: The user's question about product prices
        api_key: Google API key for Gemini model
        
    Returns:
        str: The agent's  response
    """
    try:
        if not api_key:
            return "❌ Please provide a valid Google API key in the settings."
            
        if not user_question or not user_question.strip():
            return "❌ Please provide a valid question about product prices."
            
        # Initialize the  agent
        agent = PriceComparisonAgent(google_api_key=api_key)
        
        # Run the agent
        response = await agent.run(user_question)
        
        if not response:
            return "❌ Sorry, I couldn't find any price information for your query. Please try rephrasing your question or check if the product name is spelled correctly."
            
        return response
        
    except Exception as e:
        logger.error(f"Error in run_price_agent: {str(e)}")
        return f"❌ An error occurred while processing your request: {str(e)}"

# Add a synchronous wrapper for Streamlit
def run_price_agent_sync(user_question: str, api_key: str) -> str:
    """
    Synchronous wrapper for run_price_agent to be used with Streamlit.
    
    Args:
        user_question: The user's question about product prices
        api_key: Google API key for Gemini model
        
    Returns:
        str: The agent's  response
    """
    try:
        return asyncio.run(run_price_agent(user_question, api_key))
    except Exception as e:
        logger.error(f"Error in run_price_agent_sync: {str(e)}")
        return f"❌ An error occurred while processing your request: {str(e)}"

if __name__ == "__main__":
    # Test with  prompting
    async def test_agent():
        import os
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Please set GOOGLE_API_KEY environment variable")
            return
        
        test_questions = [
            "What is the price of eggs?",
            "I want to buy milk, show me the cheapest options",
            "Compare prices for Surf Excel detergent",
            "Find me the best deal on potatoes"
        ]
        
        for question in test_questions:
            print(f"\n🔍 Testing: {question}")
            print("=" * 50)
            response = await run_price_agent(question, api_key)
            print(response)
            print("\n")
    
    # Uncomment to run tests
    # asyncio.run(test__agent())