from langchain_community.tools import DuckDuckGoSearchResults
from langchain.tools import Tool
from typing import Dict, List, Any, Tuple
import json
import re
from models import MacroNutrient, IngredientNutrition
from utils.logger import setup_logger


class NutritionSearchTool:
    """Tool for searching nutrition information using web search."""

    def __init__(self, _=None):  # Parameter kept for backwards compatibility
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing NutritionSearchTool")
        self.search_tool = DuckDuckGoSearchResults(
            output_format="list",
            num_results=5
        )
        self.include_sources = True

    def search_ingredient_nutrition(self, ingredient: str, amount: str = None) -> Dict[str, Any]:
        """Search for nutrition information of a specific ingredient."""
        self.logger.info(f"Searching nutrition for ingredient: {ingredient}, amount: {amount or 'not specified'}")
        search_query = f"nutrition facts macros calories protein carbs fat {ingredient} {amount or '100g'}"

        self.logger.debug(f"Search query: {search_query}")
        results = self.search_tool.invoke(search_query)
        self.logger.info(f"Found {len(results)} search results for {ingredient}")

        # Process results to include source information
        processed_results = []
        sources = []

        if results:
            self.logger.debug(f"Search results: {results}")
            # Process each search result to extract sources
            for result in results:
                processed_results.append(result)

                # Create source entry
                if isinstance(result, dict) and 'title' in result and 'link' in result:
                    sources.append({
                        "title": result['title'],
                        "url": result['link'],
                        "snippet": result.get('snippet', '')
                    })
                elif isinstance(result, str):
                    # Simple string result with no source info
                    continue

        if not results:
            self.logger.warning(f"No results found for ingredient: {ingredient}")
            return {
                "ingredient": ingredient,
                "amount": amount or "100g",
                "search_results": [],
                "sources": []
            }

        return {
            "ingredient": ingredient,
            "amount": amount or "100g",
            "search_results": processed_results,
            "sources": sources
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
        results = self.search_tool.invoke(search_query)
        self.logger.info(f"Found {len(results)} search results for recipe {recipe_name}")

        # Process results to include source information
        processed_results = []
        sources = []

        if results:
            # Process each search result to extract sources
            for result in results:
                processed_results.append(result)

                # Create source entry
                if isinstance(result, dict) and 'title' in result and 'link' in result:
                    sources.append({
                        "title": result['title'],
                        "url": result['link'],
                        "snippet": result.get('snippet', '')
                    })
                elif isinstance(result, str):
                    # Simple string result with no source info
                    continue

        return {
            "recipe": recipe_name,
            "search_results": processed_results,
            "sources": sources
        }

    def search_cooking_method_impact(self, cooking_method: str, ingredient: str) -> Dict[str, Any]:
        """Search for how cooking methods affect nutrition."""
        self.logger.info(f"Searching nutrition impact of {cooking_method} on {ingredient}")
        search_query = f"nutrition impact {cooking_method} {ingredient} calories protein fat"
        self.logger.debug(f"Search query: {search_query}")
        results = self.search_tool.invoke(search_query)
        self.logger.info(f"Found {len(results)} search results for cooking impact")

        # Process results to include source information
        processed_results = []
        sources = []

        if results:
            # Process each search result to extract sources
            for result in results:
                processed_results.append(result)

                # Create source entry
                if isinstance(result, dict) and 'title' in result and 'link' in result:
                    sources.append({
                        "title": result['title'],
                        "url": result['link'],
                        "snippet": result.get('snippet', '')
                    })
                elif isinstance(result, str):
                    # Simple string result with no source info
                    continue

        return {
            "cooking_method": cooking_method,
            "ingredient": ingredient,
            "search_results": processed_results,
            "sources": sources
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
