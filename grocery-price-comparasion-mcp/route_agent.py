import asyncio
import logging
from agent.price_compare_agent import create_price_comparison_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_price_agent_sync(user_question: str, api_key: str, use_manual: bool = False) -> str:

    try:
        return asyncio.run(run_price_agent(user_question, api_key, use_manual))
    except Exception as e:
        logger.error(f"Error in run_price_agent_sync: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}"

async def run_price_agent(user_question: str, api_key: str, use_manual: bool = False) -> str:

    try:
        # Validate inputs
        if not api_key:
            return "Please provide a valid Google API key in the settings."
        
        if not user_question or not user_question.strip():
            return "Please provide a valid question about product prices."
        
        # Create agent instance
        logger.info(f"Creating agent with manual={use_manual}")
        agent = create_price_comparison_agent(
            google_api_key=api_key,
            use_manual=use_manual
        )
        
        # Run the agent
        logger.info(f"Running agent with question: {user_question}")
        response = await agent.run(user_question)
        
        # Validate response
        if not response:
            return "Sorry, I couldn't find any price information for your query. Please try rephrasing your question or check if the product name is spelled correctly."
        
        return response
        
    except Exception as e:
        logger.error(f"Error in run_price_agent: {str(e)}", exc_info=True)
        
        # Try fallback to manual implementation if main agent fails
        if not use_manual:
            logger.info("Attempting fallback to manual implementation")
            try:
                return await run_price_agent(user_question, api_key, use_manual=True)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
        
        return f"An error occurred while processing your request: {str(e)}. Please try again or contact support if the issue persists."

# # Test function for development
# async def test_agent(question: str = "What is the price of eggs?"):
#     """Test function for development purposes."""
#     import os
#     api_key = os.getenv("GOOGLE_API_KEY")
    
#     if not api_key:
#         print("Please set GOOGLE_API_KEY environment variable")
#         return
    
#     print(f"Testing with question: {question}")
#     result = await run_price_agent(question, api_key)
#     print(f"Result: {result}")

# if __name__ == "__main__":
#     # Run test if executed directly
#     asyncio.run(test_agent())