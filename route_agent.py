import asyncio
import logging
from agent.price_compare_agent import create_price_comparison_agent

model_name = "gemini-2.0-flash"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_price_agent_sync(user_question: str, api_key: str) -> str:
    """
    Synchronous wrapper for the MCP-based price agent.
    
    Args:
        user_question: User's question about product prices
        api_key: Google API key
    """
    try:
        return asyncio.run(run_price_agent(user_question, api_key))
    except Exception as e:
        logger.error(f"Error in run_price_agent_sync: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}"

async def run_price_agent(user_question: str, api_key: str) -> str:
    """
    MCP-based price agent runner.
    
    Args:
        user_question: User's question about product prices
        api_key: Google API key
    """
    try:
        # Validate inputs
        if not api_key:
            return "Please provide a valid Google API key in the settings."
        
        if not user_question or not user_question.strip():
            return "Please provide a valid question about product prices."
        
        # Create MCP-based agent (default configuration)
        logger.info("Creating MCP-based price comparison agent")
        # Ensure use_direct_scraper is False to use the MCP client
        agent = create_price_comparison_agent(
            google_api_key=api_key,
            model_name=model_name,
            # use_manual=False is removed as it was unused
            use_direct_scraper=False  # Explicitly set to False for MCP client
        )
        
        logger.info(f"Running agent with question: {user_question}")
        response = await agent.run(user_question)
        
        if response:
            return response
        else:
            logger.warning("Agent returned empty response")
            return "I wasn't able to get price information at the moment. Please try again later."
                
    except Exception as e:
        logger.error(f"Error in run_price_agent: {str(e)}", exc_info=True)
        return f"An error occurred while processing your request: {str(e)}. Please try again later."
