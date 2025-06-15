# filepath: /Users/brbharad/Desktop/IISc/Course Work/Deep Learning/Project/nutrition-agent/health_diet_agent.py

"""
Health Diet Agent Module

This module implements the Health Diet Agent which analyzes recipes and ingredients
for their nutritional content and provides macronutrient breakdowns.
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools import Tool
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from llm_config import get_llm
from models import MacroNutrient, IngredientNutrition, RecipeNutrition, NutritionRecord
from utils.logger import setup_logger
import db
from tools import create_nutrition_search_tools


# Define system prompt for the health diet agent
NUTRITION_SYSTEM_PROMPT = """
You are a specialized nutrition assistant that provides accurate macronutrient information
for food items, ingredients, and recipes.

Your responsibilities:
1. Analyze user questions about nutrition facts for specific foods or recipes
2. Use search tools to gather accurate nutritional data
3. Interpret and summarize search results into structured macronutrient breakdowns
4. Present nutrition information in a helpful, easy-to-understand format
5. When analyzing recipes, consider the cooking methods and how they affect nutrition
6. Provide per-serving information when applicable

When presenting nutrition information, use this structure:
- Calories: [value] kcal
- Protein: [value]g
- Carbohydrates: [value]g
- Fat: [value]g
- Fiber: [value]g (if available)
- Sugar: [value]g (if available)

Always use the appropriate tools to search for accurate information before providing
an answer. If information is inconsistent across sources, provide a reasonable estimate
and note the discrepancy.
"""


class HealthDietAgent:
    """
    Agent for analyzing nutrition information of recipes and ingredients.
    Uses LLM and nutrition search tools to provide detailed nutrition breakdowns.
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_config: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        enable_db: bool = True
    ):
        """
        Initialize the Health Diet Agent.

        Args:
            llm_provider: The LLM provider to use ('openai', 'github', or 'groq')
            llm_config: Configuration parameters for the LLM provider
            temperature: Temperature setting for the LLM (used if not in llm_config)
            enable_db: Whether to enable database storage of nutrition inquiries
        """
        self.logger = setup_logger(__name__)
        self.logger.info(f"Initializing Health Diet Agent with {llm_provider} provider")

        # Process llm_config
        config = llm_config or {}
        if "temperature" not in config and temperature != 0.1:
            config["temperature"] = temperature

        # Initialize the LLM
        self.llm = get_llm(llm_provider, config)
        self.logger.info("LLM initialized successfully")

        # Create nutrition search tools using the tools module
        self.logger.info("Creating nutrition search tools")
        self.tools = create_nutrition_search_tools()
        self.logger.info(f"Created {len(self.tools)} nutrition search tools")

        # Initialize conversation memory
        self.conversation_history = []

        # Initialize database storage if enabled
        self.enable_db = enable_db
        if self.enable_db:
            db.init_db()
            self.logger.info("Database initialized for nutrition record storage")

        # Initialize the agent
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the LangChain agent with tools and LLM."""
        self.logger.info("Initializing nutrition analysis agent")

        # Create the agent with the system message and tools
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=NUTRITION_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create the agent
        agent = create_openai_functions_agent(self.llm, self.tools, prompt)

        # Create the executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False
        )

        self.logger.info("Agent initialization complete")

    def analyze_nutrition(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze nutrition information based on user query.
        If database is enabled, saves the results to the database.

        Args:
            user_query: User's query about recipe or ingredients

        Returns:
            Dictionary with analysis results, macros, and error information
        """
        self.logger.info(f"Processing nutrition analysis for query: {user_query}")

        try:
            # Run the agent to get nutrition analysis
            result = self.agent_executor.invoke({"input": user_query})

            analysis_result = {
                "success": True,
                "analysis": result["output"],
                "raw_result": result
            }

            # Extract macronutrient data
            macros = self.extract_macros(analysis_result)

            # Save to database if enabled and macros were extracted successfully
            record_id = None
            if macros and self.enable_db:
                record_id = self.save_to_db(user_query, analysis_result, macros)
                if record_id:
                    self.logger.info(f"Saved nutrition inquiry to database with ID {record_id}")

            # Add macros and record_id to the result
            analysis_result["macros"] = macros
            analysis_result["record_id"] = record_id

            self.logger.info("Successfully completed nutrition analysis")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Error during nutrition analysis: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to analyze nutrition: {str(e)}",
                "query": user_query,
                "macros": None,
                "record_id": None
            }

    def extract_macros(self, analysis_result: Dict[str, Any]) -> Optional[MacroNutrient]:
        """
        Extract structured macronutrient data from analysis result.

        Args:
            analysis_result: The result from nutrition analysis

        Returns:
            MacroNutrient object or None if extraction fails
        """
        try:
            self.logger.info("Extracting macronutrient data from analysis result")

            # Ask the LLM to extract structured data from the analysis
            extraction_prompt = f"""
            Extract the precise macronutrient values from this nutrition analysis:

            {analysis_result['analysis']}

            Return only a valid JSON object with these fields (include only if values are present):
            - calories (number)
            - protein (number, in grams)
            - carbohydrates (number, in grams)
            - fat (number, in grams)
            - fiber (number, in grams, if available)
            - sugar (number, in grams, if available)
            - sodium (number, in mg, if available)
            """

            messages = [
                SystemMessage(content="You are a data extraction assistant that extracts structured data from text."),
                HumanMessage(content=extraction_prompt)
            ]

            response = self.llm.invoke(messages)

            # Extract JSON from response
            # Find JSON in the response
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.content

            # Clean up any non-JSON parts
            json_str = re.sub(r'^[^{]*', '', json_str)
            json_str = re.sub(r'[^}]*$', '', json_str)

            # Parse JSON data
            macro_data = json.loads(json_str)

            # Create MacroNutrient object
            macros = MacroNutrient(**macro_data)

            self.logger.info(f"Successfully extracted macronutrient data: {macros.to_dict()}")
            return macros

        except Exception as e:
            self.logger.error(f"Failed to extract macronutrient data: {str(e)}")
            return None

    def extract_recipe_data(self, user_query: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured recipe data from analysis results.

        Args:
            user_query: Original user query
            analysis_result: The result from nutrition analysis

        Returns:
            Dictionary with recipe data
        """
        try:
            self.logger.info("Extracting recipe data from analysis result")

            # Ask LLM to extract recipe information
            extraction_prompt = f"""
            Extract the recipe information from this user query and nutrition analysis:

            USER QUERY: {user_query}

            NUTRITION ANALYSIS: {analysis_result['analysis']}

            Extract the following information and return as JSON:
            1. recipe_name: The name of the recipe or dish
            2. query_type: "recipe" if this is a complete dish, or "ingredients" if just a list of ingredients
            3. servings: Number of servings mentioned (default to 1 if not specified)
            4. ingredients: Array of ingredient names mentioned (if available)
            """

            messages = [
                SystemMessage(content="You are a data extraction assistant that extracts structured data from text."),
                HumanMessage(content=extraction_prompt)
            ]

            response = self.llm.invoke(messages)

            # Extract JSON from response
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.content

            # Clean up any non-JSON parts
            json_str = re.sub(r'^[^{]*', '', json_str)
            json_str = re.sub(r'[^}]*$', '', json_str)

            # Parse JSON data
            recipe_data = json.loads(json_str)

            self.logger.info(f"Successfully extracted recipe data: {recipe_data}")
            return recipe_data

        except Exception as e:
            self.logger.error(f"Failed to extract recipe data: {str(e)}")
            return {
                "recipe_name": "Unknown",
                "query_type": "ingredients",
                "servings": 1,
                "ingredients": []
            }

    def save_to_db(self, user_query: str, analysis_result: Dict[str, Any], macros: MacroNutrient) -> Optional[int]:
        """
        Save nutrition inquiry to the database.

        Args:
            user_query: Original user query
            analysis_result: The result from nutrition analysis
            macros: Extracted macronutrient information

        Returns:
            ID of the saved record or None if saving failed
        """
        if not self.enable_db:
            self.logger.info("Database storage is disabled, skipping save")
            return None

        try:
            # Extract recipe information
            recipe_data = self.extract_recipe_data(user_query, analysis_result)

            # Save to database
            record_id = db.save_nutrition_inquiry(
                query_text=user_query,
                query_type=recipe_data.get('query_type', 'ingredients'),
                macros=macros,
                raw_analysis=analysis_result,
                recipe_name=recipe_data.get('recipe_name'),
                servings=recipe_data.get('servings', 1),
                ingredients=[{"ingredient": ing, "amount": "unknown"} for ing in recipe_data.get('ingredients', [])],
                user_id='anonymous'  # For future multi-user support
            )

            self.logger.info(f"Saved nutrition inquiry to database with ID {record_id}")
            return record_id

        except Exception as e:
            self.logger.error(f"Failed to save nutrition inquiry to database: {str(e)}")
            return None

    def get_nutrition_history(self, user_id: str = 'anonymous', limit: int = 10) -> List[NutritionRecord]:
        """
        Get nutrition inquiry history for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of records to return

        Returns:
            List of nutrition inquiry records
        """
        if not self.enable_db:
            self.logger.info("Database is disabled, cannot retrieve history")
            return []

        try:
            # Get records from database
            records = db.get_nutrition_history(user_id=user_id, limit=limit)

            # Convert to NutritionRecord objects
            nutrition_records = []
            for record in records:
                # Create MacroNutrient object
                macros = MacroNutrient(
                    calories=record.get('calories'),
                    protein=record.get('protein'),
                    carbohydrates=record.get('carbohydrates'),
                    fat=record.get('fat'),
                    fiber=record.get('fiber'),
                    sugar=record.get('sugar'),
                    sodium=record.get('sodium')
                )

                # Format ingredients data if present
                ingredients_list = []
                if 'ingredients' in record and record['ingredients']:
                    for ing in record['ingredients']:
                        # Create ingredient macros
                        ing_macros = MacroNutrient(
                            calories=ing.get('calories'),
                            protein=ing.get('protein'),
                            carbohydrates=ing.get('carbohydrates'),
                            fat=ing.get('fat'),
                            fiber=ing.get('fiber'),
                            sugar=ing.get('sugar'),
                            sodium=ing.get('sodium')
                        )

                        # Create ingredient nutrition object
                        ing_nutrition = IngredientNutrition(
                            ingredient=ing.get('ingredient_name', ''),
                            amount=ing.get('amount', ''),
                            macros=ing_macros
                        )
                        ingredients_list.append(ing_nutrition)

                # Create NutritionRecord object
                nutrition_record = NutritionRecord(
                    id=record.get('id'),
                    query_text=record.get('query_text'),
                    query_type=record.get('query_type'),
                    timestamp=record.get('timestamp'),
                    user_id=user_id,
                    recipe_name=record.get('recipe_name'),
                    servings=record.get('servings', 1),
                    macros=macros,
                    ingredients=ingredients_list
                )

                nutrition_records.append(nutrition_record)

            self.logger.info(f"Retrieved {len(nutrition_records)} nutrition records")
            return nutrition_records

        except Exception as e:
            self.logger.error(f"Failed to retrieve nutrition history: {str(e)}")
            return []

    def get_macro_trends(self, user_id: str = 'anonymous', days: int = 30) -> Dict[str, Any]:
        """
        Get macro consumption trends over time.

        Args:
            user_id: ID of the user
            days: Number of days to look back

        Returns:
            Dictionary with trend data for plotting
        """
        if not self.enable_db:
            self.logger.info("Database is disabled, cannot retrieve trends")
            return {"error": "Database is disabled"}

        try:
            # Get trend data from database
            trends = db.get_macro_trends(user_id=user_id, days=days)

            # Format data for plotting
            dates = [trend.get('record_date') for trend in trends]
            calories = [trend.get('total_calories', 0) for trend in trends]
            protein = [trend.get('total_protein', 0) for trend in trends]
            carbs = [trend.get('total_carbs', 0) for trend in trends]
            fat = [trend.get('total_fat', 0) for trend in trends]

            self.logger.info(f"Retrieved macro trends for {len(trends)} days")
            return {
                "dates": dates,
                "calories": calories,
                "protein": protein,
                "carbohydrates": carbs,
                "fat": fat
            }

        except Exception as e:
            self.logger.error(f"Failed to retrieve macro trends: {str(e)}")
            return {"error": str(e)}

    def delete_nutrition_record(self, record_id: int) -> bool:
        """
        Delete a nutrition record from the database.

        Args:
            record_id: ID of the record to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.enable_db:
            self.logger.info("Database is disabled, cannot delete record")
            return False

        try:
            result = db.delete_nutrition_record(record_id)
            self.logger.info(f"Deleted nutrition record {record_id}: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to delete nutrition record: {str(e)}")
            return False

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return information about the agent's capabilities.
        Used by router systems to determine which agent to route queries to.

        Returns:
            Dictionary with agent information
        """
        self.logger.info("Retrieving agent information")
        return {
            "name": "NutritionAgent",
            "description": "Nutrition analysis for recipes and ingredients",
            "capabilities": [
                "Recipe nutrition analysis",
                "Ingredient macro breakdown",
                "Per-serving calculations",
                "Cooking method impact analysis",
                "Nutrition history tracking and visualization"
            ],
            "keywords": [
                "nutrition", "calories", "macros", "protein", "carbs", "fat",
                "recipe", "ingredient", "diet", "food", "serving", "meal",
                "history", "tracking", "trends"
            ]
        }

    def can_handle_query(self, query: str) -> bool:
        """
        Determine if this agent can handle the given query.
        Used by router systems to determine which agent to route queries to.

        Args:
            query: User query string

        Returns:
            True if this agent can handle the query, False otherwise
        """
        self.logger.info(f"Evaluating if agent can handle query: '{query}'")

        # List of nutrition-related keywords
        nutrition_keywords = [
            "nutrition", "nutritional", "calories", "caloric", "calorie",
            "protein", "proteins", "carb", "carbs", "carbohydrate", "carbohydrates",
            "fat", "fats", "macro", "macros", "macronutrient", "macronutrients",
            "diet", "dietary", "serving", "servings", "recipe", "recipes",
            "ingredient", "ingredients", "food", "meal", "meals", "dish", "dishes",
            "vitamin", "vitamins", "mineral", "minerals", "fiber", "sugar", "sodium",
            "healthy", "unhealthy", "history", "track", "tracking", "trend", "trends"
        ]

        # Check if query contains nutrition keywords
        query_lower = query.lower()
        for keyword in nutrition_keywords:
            if keyword in query_lower:
                self.logger.info(f"Agent can handle query (matched keyword: {keyword})")
                return True

        # If no keywords match, the agent cannot handle this query
        self.logger.info("Agent cannot handle query (no matching keywords)")
        return False

    def set_context(self, context_str: str) -> None:
        """
        Set context information for the agent.
        This allows the agent to have access to information from previous interactions
        or other agents in a multi-agent system.

        Args:
            context_str: Context information as a string
        """
        self.logger.info(f"Setting context for agent: {context_str[:50]}...")
        # Store context in conversation history
        self.conversation_history.append({
            "role": "system",
            "content": f"Context: {context_str}"
        })

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the agent's conversation history.
        Used by router systems to maintain context across agent switches.

        Returns:
            List of conversation entries
        """
        self.logger.info(f"Retrieving conversation history ({len(self.conversation_history)} entries)")
        return self.conversation_history

    def clear_memory(self) -> None:
        """
        Clear the agent's conversation memory.
        """
        self.logger.info("Clearing agent conversation memory")
        self.conversation_history = []
