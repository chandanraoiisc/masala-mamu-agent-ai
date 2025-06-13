from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain.tools import Tool
from typing import Dict, List, Any
import json
import re
from models import MacroNutrient, IngredientNutrition
from utils.logger import setup_logger


class NutritionSearchTool:
    """Tool for searching nutrition information using web search."""

    def __init__(self, _=None):  # Parameter kept for backwards compatibility
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing NutritionSearchTool")
        self.search_tool = DuckDuckGoSearchAPIWrapper(
            max_results=5
        )

    def search_ingredient_nutrition(self, ingredient: str, amount: str = None) -> Dict[str, Any]:
        """Search for nutrition information of a specific ingredient."""
        self.logger.info(f"Searching nutrition for ingredient: {ingredient}, amount: {amount or 'not specified'}")
        search_query = f"nutrition facts macros calories protein carbs fat {ingredient}"
        if amount:
            search_query += f" {amount}"

        self.logger.debug(f"Search query: {search_query}")
        results = self.search_tool.run(search_query)
        self.logger.info(f"Found {len(results)} search results for {ingredient}")
        return {
            "ingredient": ingredient,
            "amount": amount or "100g",
            "search_results": results
        }

    def search_recipe_nutrition(self, recipe_name: str, ingredients: List[str] = None) -> Dict[str, Any]:
        """Search for nutrition information of a complete recipe."""
        self.logger.info(f"Searching nutrition for recipe: {recipe_name}")
        search_query = f"nutrition facts calories macros {recipe_name} recipe"
        if ingredients:
            # Add key ingredients to search query
            key_ingredients = ingredients[:3]  # Use first 3 ingredients
            search_query += f" with {' '.join(key_ingredients)}"
            self.logger.debug(f"Including key ingredients: {key_ingredients}")

        self.logger.debug(f"Search query: {search_query}")
        results = self.search_tool.run(search_query)
        self.logger.info(f"Found {len(results)} search results for recipe {recipe_name}")
        return {
            "recipe": recipe_name,
            "search_results": results
        }

    def search_cooking_method_impact(self, cooking_method: str, ingredient: str) -> Dict[str, Any]:
        """Search for how cooking methods affect nutrition."""
        self.logger.info(f"Searching nutrition impact of {cooking_method} on {ingredient}")
        search_query = f"nutrition impact {cooking_method} {ingredient} calories protein fat"
        self.logger.debug(f"Search query: {search_query}")
        results = self.search_tool.run(search_query)
        self.logger.info(f"Found {len(results)} search results for cooking impact")
        return {
            "cooking_method": cooking_method,
            "ingredient": ingredient,
            "search_results": results
        }


def create_nutrition_search_tools(_=None) -> List[Tool]:
    """Create LangChain tools for nutrition searching."""
    nutrition_searcher = NutritionSearchTool()

    ingredient_tool = Tool(
        name="search_ingredient_nutrition",
        description="Search for detailed nutrition information (calories, protein, carbs, fat, fiber) for a specific ingredient with amount",
        func=lambda query: nutrition_searcher.search_ingredient_nutrition(
            *query.split(" | ") if " | " in query else (query, None)
        )
    )

    recipe_tool = Tool(
        name="search_recipe_nutrition",
        description="Search for nutrition information for a complete recipe or dish",
        func=nutrition_searcher.search_recipe_nutrition
    )

    cooking_impact_tool = Tool(
        name="search_cooking_impact",
        description="Search for how cooking methods (frying, baking, steaming) affect nutritional content",
        func=lambda query: nutrition_searcher.search_cooking_method_impact(
            *query.split(" | ")
        )
    )

    return [ingredient_tool, recipe_tool, cooking_impact_tool]
