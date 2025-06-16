import logging
from typing import Optional, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools.quickcompare_tool import quickcompare_scraper
from agent.price_compare_agent_prompt import PRICE_COMPARE_SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceComparisonAgent:
    """Fixed agent class for price comparison using LangChain's agentic framework and Gemini."""
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the price comparison agent.
        
        Args:
            google_api_key (str): Google API key for Gemini
            model_name (str): Gemini model name to use
        """
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=google_api_key
        )
        
        # Available tools
        self.tools = [quickcompare_scraper]
        
        # Create the agent and executor
        self.agent_executor = self._create_agent_executor()
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create and configure the LangChain agent executor."""
        
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
        """
        Run the agent with a user question.
        
        Args:
            question (str): User's question about price comparison
            chat_history (Optional[List[BaseMessage]]): Previous conversation history
            
        Returns:
            Optional[str]: Agent's response or None if error occurred
        """
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

class ManualPriceComparisonAgent:
    """Alternative manual implementation of the price comparison agent."""
    
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=google_api_key
        )
        self.tools = [quickcompare_scraper]
        self.tools_dict = {tool.name: tool for tool in self.tools}
    
    async def run(self, question: str) -> Optional[str]:
        """
        Manually run the agent logic with tool calling.
        
        Args:
            question (str): User's question
            
        Returns:
            Optional[str]: Agent's response
        """
        try:
            # Create messages
            messages = [
                SystemMessage(content=FIXED_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]
            
            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools(self.tools)
            
            # First LLM call
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)
            
            # Check if tools were called
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"Tool calls detected: {len(response.tool_calls)}")
                
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if tool_name in self.tools_dict:
                        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                        tool_result = await self.tools_dict[tool_name].ainvoke(tool_args)
                        
                        # Add tool result to messages
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call["id"]
                        )
                        messages.append(tool_message)
                
                # Second LLM call with tool results
                final_response = await self.llm.ainvoke(messages)
                return final_response.content
            else:
                # No tools called, return direct response
                return response.content
                
        except Exception as e:
            logger.error(f"Error in manual agent execution: {e}", exc_info=True)
            return f"I encountered an error while processing your request: {str(e)}. Please try again."

def create_price_comparison_agent(google_api_key: str, model_name: str = "gemini-2.0-flash", use_manual: bool = False):
    """
    Factory function to create a price comparison agent.
    
    Args:
        google_api_key (str): Google API key
        model_name (str): Gemini model name
        use_manual (bool): Whether to use manual implementation
        
    Returns:
        PriceComparisonAgent or ManualPriceComparisonAgent
    """
    if use_manual:
        return ManualPriceComparisonAgent(google_api_key, model_name)
    else:
        return PriceComparisonAgent(google_api_key, model_name)