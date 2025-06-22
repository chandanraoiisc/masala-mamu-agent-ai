import json
import os,logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, InventoryData
from agents.inventory_service.inventory_store import fetch_all_inventory
# from agents.inventory_service.rag import generate_answer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class InventoryAgent(BaseAgent):
    """Agent for managing kitchen inventory"""

    def __init__(self, gpt_client=None):
        self.gpt_client = gpt_client
        self.system_message = (
            "You are a kitchen assistant system that routes queries to the correct action.\n"
            "Classify the user's query into one of the intents: insert, update, delete, fetch.\n"
            "If the query is about adding or updating items when they say bought or purchased, classify it as 'insert' or 'update'.\n"
            "If not clear, default to 'fetch'. Return only the intent."
        )
        self.output_schema = {
            "intent": "The intent behind the query. Must be one of: insert, update, delete, fetch"
        }

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

        inventory = self._load_inventory()
        available_items = inventory.get("available", [])
        logger.debug(f"Available items: {available_items}")
        # Step 2: Load and validate recipe_data from state
        recipe_data = state.get("recipe_data")

        missing_ingredients = []
        if recipe_data:
            try:
                logger.debug(f"Recipe ingredients: {recipe_data}")

                # Compare recipe ingredients with available inventory
                available_names = [item["name"].lower() for item in available_items]
                for ingredient in recipe_data.ingredients:
                    if ingredient["name"].lower() not in available_names:
                        missing_ingredients.append({
                            "name":ingredient.name,
                            "quantity": ingredient.quantity,
                            "unit": 'unkown'
                        })
            except AttributeError as e:
                logger.error(f"Error accessing recipe_data: {str(e)}")
                recipe_ingredients = []
        print("missing ingredients",missing_ingredients)
        # Step 3: Populate InventoryData
        inventory_data = InventoryData(
            available=available_items,
            missing=missing_ingredients
        )
        logger.debug(f"Inventory data: {inventory_data}")
        # Step 1: Get intent using GPT
        # intent = None
        try:
            parsed_result = await self.gpt_client.generate_structured_output(
                prompt=f"Analyze this kitchen assistant query and determine the optimal agent flow: {query}",
                system_message=self.system_message,
                output_schema=self.output_schema
            )
            intent = parsed_result.get("intent", "fetch").lower()
            logger.debug(f"[InventoryAgent] Parsed intent: {intent}")
        except Exception as e:
            logger.error(f"Failed to classify intent via GPT: {e}")
            intent = "fetch"
        # Step 2: If it's insert/update/delete, call RAG and return immediately
        if intent in ["insert", "update", "delete"]:
            try:
                from agents.inventory_service.rag import generate_answer
                answer = generate_answer(query)
                logger.info("📦 Returning inventory response from InventoryAgent.")
                return {
                    "direct_response": answer,
                    "inventory_data": inventory_data,
                    "__next__": "__end__"  # prevent routing loop
                }
            except Exception as e:
                print(f"Error in RAG processing: {str(e)}")
                logger.error(f"RAG error: {str(e)}")
                return {
                    "inventory_data": inventory_data,
                    "__next__": "__end__"
                }
        # Step 1: Fetch all available inventory items

        logger.info("📦 Returning inventory response from InventoryAgent.")
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