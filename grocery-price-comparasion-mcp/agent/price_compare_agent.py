import logging
from typing import Optional, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor

# Updated import with fallback handling
try:
    from tools.quickcompare_tool import get_quickcompare_tool
    TOOLS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import tools: {e}")
    TOOLS_AVAILABLE = False


# Import prompt (create this file if it doesn't exist)
try:
    from agent.price_compare_agent_prompt import PRICE_COMPARE_SYSTEM_PROMPT
except ImportError:
    # Fallback prompt if file doesn't exist
    PRICE_COMPARE_SYSTEM_PROMPT = """
    You are a helpful price comparison assistant for Indian e-commerce platforms.
    
    You have access to a tool that can scrape and compare product prices across multiple platforms like:
    - BigBasket
    - Blinkit
    - Swiggy Instamart
    - Zepto
    - JioMart
    - Amazon
    - Flipkart
    
    When a user asks about product prices:
    1. Use the quickcompare_scraper tool to get current price data
    2. Present the information in a clear, organized manner
    3. Highlight the cheapest and most expensive options
    4. Include quantity information when available
    5. Be helpful and conversational
    
    If the tool returns an error, explain the issue and suggest alternatives.
    """

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceComparisonAgent:
        
    # Removed use_manual from constructor as it was unused
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash", use_direct_scraper: bool = False):
        
        if not TOOLS_AVAILABLE:
            raise ImportError("Tools are not available. Please ensure tools/quickcompare_tool.py exists.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=google_api_key
        )
        
        # Get the appropriate tool - now always MCP client through get_quickcompare_tool
        # The use_direct_scraper parameter here is passed but will be ignored by the modified get_quickcompare_tool
        self.tools = [get_quickcompare_tool(use_direct=use_direct_scraper)]
        self.use_direct_scraper = use_direct_scraper # Still keeps this internal flag for consistency if needed elsewhere, though its effect is nullified by tool.py changes
        
        # Create the agent and executor
        self.agent_executor = self._create_agent_executor()
    
    def _create_agent_executor(self) -> AgentExecutor:
    
        # Create prompt template with only the variables we actually use
        prompt = ChatPromptTemplate.from_messages([
            ("system", PRICE_COMPARE_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the tool-calling agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3,
            early_stopping_method="generate",
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )
        
        return agent_executor
    
    async def run(self, question: str, chat_history: Optional[List[BaseMessage]] = None) -> Optional[str]:

        try:
            logger.info(f"Processing question: {question}")
            
            # Prepare input - only include variables that the prompt expects
            agent_input = {
                "input": question,
                "chat_history": chat_history or []
            }
            
            # Run the agent
            result = await self.agent_executor.ainvoke(agent_input)
            
            # Extract the output
            if isinstance(result, dict) and "output" in result:
                response = result["output"]
                logger.info(f"Agent response generated successfully")
                return response
            else:
                logger.warning("Unexpected result format from agent")
                return None
                
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            return f"I encountered an error while processing your request: {str(e)}. Please try again with a different query."

# Removed use_manual from function signature as it was unused
def create_price_comparison_agent(google_api_key: str, model_name: str = "gemini-2.0-flash", use_direct_scraper: bool = False):
    """
    Create a price comparison agent.
    
    Args:
        google_api_key: Google API key for Gemini
        model_name: Model name to use
        use_direct_scraper: Whether to use direct scraper instead of MCP client.
                            Note: This parameter is now effectively ignored by quickcompare_tool.get_quickcompare_tool().
    """

    # Passes use_direct_scraper, but get_quickcompare_tool now always returns MCP tool
    return PriceComparisonAgent(google_api_key, model_name, use_direct_scraper)