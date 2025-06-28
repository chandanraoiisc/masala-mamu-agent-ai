import asyncio
import json
import logging
import sys # Import sys module
from typing import Dict, Any, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickCompareInput(BaseModel):
    """Input schema for QuickCompare tool."""
    query: str = Field(description="The product to search for (e.g., 'rice', 'milk', 'eggs')")
    max_cards: int = Field(default=5, description="Maximum number of products to return (1-20)")

class QuickCompareScrapingTool(BaseTool):
    """
    LangChain tool that interfaces with the QuickCompare MCP server.
    """
    name: str = "quickcompare_scraper"
    description: str = """
    Search and compare product prices across multiple e-commerce platforms in India.
    Use this tool to find price comparisons for groceries, household items, and other products.
    
    Examples:
    - "rice" - finds rice products and prices
    - "milk" - finds milk products across platforms
    - "eggs" - finds egg prices and availability
    """
    args_schema: Type[BaseModel] = QuickCompareInput
    server_params: StdioServerParameters = Field(
        # MODIFICATION HERE: Use sys.executable to ensure the correct python interpreter
        default_factory=lambda: StdioServerParameters(
            command=sys.executable, # Use the current Python executable
            args=["quickcompare_mcp_server.py"],
            env=None
        ),
        description="MCP server parameters"
    )
    
    async def _arun(self, query: str, max_cards: int = 5) -> str:
        """
        Async implementation of the tool.
        """
        try:
            logger.info(f"QuickCompare tool called with query: '{query}', max_cards: {max_cards}")
            
            # Validate inputs
            if not query or not query.strip():
                return json.dumps({
                    "success": False,
                    "error": "Empty query provided"
                })
            
            # Clamp max_cards to valid range
            max_cards = max(1, min(max_cards, 20))
            
            # Connect to MCP server and execute
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize session
                    await session.initialize()
                    
                    # Call the scraper tool
                    result = await session.call_tool("quickcompare_scraper", {
                        "query": query,
                        "max_cards": max_cards
                    })
                    
                    # Extract the result content
                    if result.content and len(result.content) > 0:
                        response_text = result.content[0].text
                        logger.info(f"Successfully retrieved data for query: '{query}'")
                        return response_text
                    else:
                        logger.warning(f"Empty response from MCP server for query: '{query}'")
                        return json.dumps({
                            "success": False,
                            "error": "Empty response from server"
                        })
                        
        except Exception as e:
            logger.error(f"Error in QuickCompare tool: {str(e)}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "fallback_suggestion": "Try a different product name or check if the server is running"
            })
    
    def _run(self, query: str, max_cards: int = 5) -> str:
        """
        Synchronous wrapper for the async implementation.
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(query, max_cards))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self._arun(query, max_cards))

# Create the tool instance
quickcompare_scraper = QuickCompareScrapingTool()

# Tool selection function - MODIFIED to only return MCP tool
def get_quickcompare_tool(use_direct: bool = False) -> BaseTool:
    """
    Get the appropriate QuickCompare tool.
    
    Args:
        use_direct: This parameter is now ignored as only the MCP tool is available.
    
    Returns:
        The MCP-based quickcompare_scraper tool instance.
    """
    if use_direct: # This block is effectively dead code now, but kept for signature compatibility
        logger.warning("Attempted to use direct scraper, but only MCP approach is enabled.")
    return quickcompare_scraper