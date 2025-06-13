from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from typing import Dict, Any, Optional, List, Literal, Union
import json
import os
import re
from models import NutritionQuery, RecipeNutrition, MacroNutrient, IngredientNutrition
from tools import create_nutrition_search_tools
from llm_config import get_llm
from utils.logger import setup_logger


class HealthDietAgent:
    """LangChain-based Health & Diet Agent for nutrition analysis."""

    def __init__(
        self,
        llm_provider: Literal["openai", "github", "groq"] = "openai",
        llm_config: Optional[Dict[str, Any]] = None,
    ):
        # Setup logger
        self.logger = setup_logger(__name__, log_level="DEBUG")
        # Prepare config dict based on the provider
        config = llm_config or {}

        self.logger.info(f"Initializing HealthDietAgent with {llm_provider} provider")

        # Get the LLM from the configuration provider
        self.llm = get_llm(llm_provider, config)

        self.tools = create_nutrition_search_tools()

        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # Create agent executor with memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the nutrition agent."""
        return """
        You are a specialized Health & Diet Agent that analyzes recipes and ingredients for nutritional information.

        Your capabilities:
        1. Analyze complete recipes for total nutritional content
        2. Break down individual ingredients and their macros
        3. Calculate per-serving nutrition information
        4. Consider cooking methods that affect nutrition
        5. Provide detailed macro breakdowns (calories, protein, carbs, fat, fiber, sugar, sodium)

        Instructions:
        - Always search for current, accurate nutrition data using available tools
        - When analyzing recipes, extract individual ingredients first
        - Calculate total nutrition by summing individual ingredients
        - Account for cooking methods that may change nutritional content (e.g., oil absorption in frying)
        - Provide both total recipe nutrition and per-serving breakdowns
        - Be precise with units (grams, cups, etc.)
        - If user asks for individual ingredient breakdown, provide detailed analysis for each item

        Response Format:
        - Start with a summary of total macros for the dish
        - If requested, provide individual ingredient breakdowns
        - Always specify serving size assumptions
        - Mention any important nutritional notes or health considerations

        Remember: You're part of a larger kitchen assistant system, so format responses to be easily integrated with other agents.
        """

    def parse_user_input(self, user_input: str) -> NutritionQuery:
        """Parse user input to determine query type and extract relevant information."""
        self.logger.debug(f"Parsing user input: {user_input}")
        user_input_lower = user_input.lower()

        # Determine if it's asking for individual breakdown
        include_breakdown = any(phrase in user_input_lower for phrase in [
            "each ingredient", "individual", "breakdown", "separate", "per ingredient"
        ])

        # Determine query type
        if any(phrase in user_input_lower for phrase in ["recipe", "dish", "make", "cook"]):
            query_type = "recipe"
        else:
            query_type = "ingredients"

        # Extract serving information
        servings = 1
        serving_match = re.search(r'(\d+)\s*(?:serving|portion|people)', user_input_lower)
        if serving_match:
            servings = int(serving_match.group(1))

        return NutritionQuery(
            query_type=query_type,
            content=user_input,
            servings=servings,
            include_individual_breakdown=include_breakdown
        )

    def analyze_nutrition(self, user_input: str) -> Dict[str, Any]:
        """Main method to analyze nutrition based on user input."""
        self.logger.info(f"Analyzing nutrition query: {user_input[:50]}...")
        query = self.parse_user_input(user_input)
        self.logger.debug(f"Parsed query: {query}")

        # Enhance the prompt with structured information
        enhanced_input = f"""
        Analyze the nutrition for the following:

        Query Type: {query.query_type}
        Content: {query.content}
        Servings: {query.servings}
        Include Individual Breakdown: {query.include_individual_breakdown}

        Please provide comprehensive nutritional analysis including:
        1. Total macros for the entire dish/recipe
        2. Per-serving macros (divide by {query.servings} servings)
        3. {"Individual ingredient breakdown" if query.include_individual_breakdown else "Summary only"}

        Use the available tools to search for accurate, current nutrition data.
        """

        try:
            self.logger.info("Invoking nutrition agent executor")
            result = self.agent_executor.invoke({"input": enhanced_input})
            self.logger.info("Successfully generated nutrition analysis")
            return {
                "success": True,
                "analysis": result["output"],
                "query_info": query.dict()
            }
        except Exception as e:
            self.logger.error(f"Error during nutrition analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_info": query.dict()
            }

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history for integration with router."""
        messages = self.memory.chat_memory.messages
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append(HumanMessage(content=msg.content))
            elif isinstance(msg, AIMessage):
                history.append(AIMessage(content=msg.content))
        return history

    def clear_memory(self):
        """Clear conversation memory."""
        self.logger.info("Clearing conversation memory")
        self.memory.clear()

    def set_context(self, context: str):
        """Set additional context for the agent (useful for router integration)."""
        self.logger.debug(f"Setting additional context: {context[:50]}...")
        self.memory.chat_memory.add_user_message(f"Context: {context}")

    # Router-friendly methods
    def can_handle_query(self, query: str) -> bool:
        """Determine if this agent can handle the given query."""
        nutrition_keywords = [
            "nutrition", "calories", "macros", "protein", "carbs", "fat",
            "diet", "healthy", "nutritional", "ingredients nutrition",
            "recipe nutrition", "food nutrition", "macro breakdown"
        ]

        query_lower = query.lower()
        can_handle = any(keyword in query_lower for keyword in nutrition_keywords)
        self.logger.debug(f"Query check: '{query[:30]}...' - Can handle: {can_handle}")
        return can_handle

    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information for router registration."""
        return {
            "name": "health_diet_agent",
            "description": "Analyzes recipes and ingredients for nutritional information including macros breakdown",
            "capabilities": [
                "Recipe nutrition analysis",
                "Individual ingredient macro breakdown",
                "Calorie calculation",
                "Macro nutrient analysis (protein, carbs, fat, fiber)",
                "Per-serving nutrition calculation",
                "Cooking method impact on nutrition"
            ],
            "keywords": [
                "nutrition", "calories", "macros", "protein", "carbs",
                "fat", "diet", "healthy", "nutritional"
            ]
        }
