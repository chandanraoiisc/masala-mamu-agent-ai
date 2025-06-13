import asyncio
import logging
from agent.langgraph_agent import PriceComparisonAgent

def run_price_agent_sync(user_question: str, api_key: str) -> str:
    """
    Synchronous wrapper for run_price_agent to be used with Streamlit.
    """
    try:
        return asyncio.run(run_price_agent(user_question, api_key))
    except Exception as e:
        logging.error(f"Error in run_price_agent_sync: {str(e)}")
        return f"❌ An error occurred while processing your request: {str(e)}"

async def run_price_agent(user_question: str, api_key: str) -> str:
    """
    Run the price comparison agent with the given user question and API key.
    """
    try:
        if not api_key:
            return "❌ Please provide a valid Google API key in the settings."
        if not user_question or not user_question.strip():
            return "❌ Please provide a valid question about product prices."
        agent = PriceComparisonAgent(google_api_key=api_key)
        response = await agent.run(user_question)
        if not response:
            return "❌ Sorry, I couldn't find any price information for your query. Please try rephrasing your question or check if the product name is spelled correctly."
        return response
    except Exception as e:
        logging.error(f"Error in run_price_agent: {str(e)}")
        return f"❌ An error occurred while processing your request: {str(e)}"