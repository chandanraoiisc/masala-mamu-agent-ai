import json
import os,logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, InventoryData
from agents.inventory_service.inventory_store import fetch_all_inventory
# from agents.inventory_service.rag import generate_answer
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
class InventoryAgent(BaseAgent):
    """Agent for managing kitchen inventory"""

    def __init__(self, gpt_client=None):
        self.gpt_client = gpt_client

    @property
    def name(self) -> str:
        return "inventory_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    def _load_inventory(self):
        """Load inventory from the database"""
        try:
            # Fetch inventory from the database
            inventory_data = fetch_all_inventory()
            return {"available": inventory_data}
        except Exception as e:
            print(f"Error loading inventory from database: {str(e)}")
            return {"available": []}  # Return an empty inventory in case of an error

    async def process(self, state: AgentState) -> Dict[str, Any]:
        logger.debug("Entering process method of InventoryAgent")
        query = state["query"]
        logger.debug(f"Query: {query}")

        # Step 1: Fetch all available inventory items
        inventory = self._load_inventory()
        available_items = inventory.get("available", [])
        logger.debug(f"Available items: {available_items}")

        # Step 2: Load and validate recipe_data from state
        recipe_data = state.get("recipe_data")
        missing_ingredients = []
        if recipe_data:
            try:
                recipe_ingredients = recipe_data.ingredients
                logger.debug(f"Recipe ingredients: {recipe_ingredients}")
            except AttributeError as e:
                logger.error(f"Error accessing recipe_data: {str(e)}")
                recipe_ingredients = []

            # Compare recipe ingredients with available inventory
            available_names = [item["name"].lower() for item in available_items]
            for ingredient in recipe_ingredients:
                if ingredient.name.lower() not in available_names:
                    missing_ingredients.append({
                        "name": ingredient.name,
                        "quantity": ingredient.quantity,
                        "unit": ingredient.unit
                    })

        # Step 3: Populate InventoryData
        inventory_data = InventoryData(
            available=available_items,
            missing=missing_ingredients
        )
        logger.debug(f"Inventory data: {inventory_data}")

        return {"inventory_data": inventory_data}
        # Step 4: Decide whether to return inventory data or call generate_answer
        # if "inventory" in query.lower():
        #     # Return inventory data
        #     return {"inventory_data": inventory_data}
        # else:
        #     # Call generate_answer from rag.py
        #     try:
        #         response = generate_answer(query)
        #         return {"response": response}
        #     except Exception as e:
        #         print(f"Error calling generate_answer: {str(e)}")
        #         return {"error": "Failed to process the query"}