import json
import os
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, InventoryData


class InventoryAgent(BaseAgent):
    """Agent for managing kitchen inventory"""

    def __init__(self, gpt_client=None, inventory_file="inventory.json"):
        self.gpt_client = gpt_client
        self.inventory_file = inventory_file

    @property
    def name(self) -> str:
        return "inventory_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    def _load_inventory(self):
        """Load inventory from file"""
        if not os.path.exists(self.inventory_file):
            # Create default inventory if file doesn't exist
            default_inventory = {
                "available": [
                    {"name": "rice", "quantity": 500, "unit": "g"},
                    {"name": "chicken", "quantity": 1, "unit": "kg"},
                    {"name": "onion", "quantity": 5, "unit": "pieces"},
                    {"name": "garlic", "quantity": 1, "unit": "head"},
                    {"name": "tomato", "quantity": 3, "unit": "pieces"},
                    {"name": "salt", "quantity": 200, "unit": "g"}
                ]
            }
            with open(self.inventory_file, 'w') as f:
                json.dump(default_inventory, f, indent=2)

        with open(self.inventory_file, 'r') as f:
            return json.load(f)

    def _save_inventory(self, inventory):
        """Save inventory to file"""
        with open(self.inventory_file, 'w') as f:
            json.dump(inventory, f, indent=2)

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Check what ingredients are available in inventory

        Args:
            state: Current workflow state

        Returns:
            Dict with inventory_data key
        """
        query = state["query"]
        parsed_intent = state["parsed_intent"]

        # Load actual inventory from file
        inventory = self._load_inventory()

        # Format the response based on the query
        if "what" in query.lower() and "ingredients" in query.lower() and "have" in query.lower():
            # Direct query about available ingredients
            available_items = inventory.get("available", [])

            # Format the response
            response = "Here are the ingredients you have in your kitchen:\n\n"
            for item in available_items:
                response += f"- {item['name']}: {item['quantity']} {item['unit']}\n"

            # Use the GPT client to enhance the response if available
            if self.gpt_client:
                try:
                    enhanced_response = await self.gpt_client.generate_completion(
                        prompt=f"""
                        Original user query: "{query}"
                        Available ingredients: {', '.join([item['name'] for item in available_items])}

                        Generate a concise response listing only the available ingredients in a clear format.
                        """,
                        system_message="You are a helpful kitchen assistant. Respond directly to the user's query about their inventory. Be concise and only list the ingredients they have."
                    )
                    response = enhanced_response
                except Exception as e:
                    print(f"Error enhancing response: {str(e)}")

            # Create inventory data
            inventory_data = InventoryData(
                available=inventory.get("available", []),
                missing=[]  # No missing ingredients for a direct inventory query
            )

            return {
                "inventory_data": inventory_data,
                "direct_response": response  # Add a direct response field
            }
        else:
            # For recipe-related queries, determine missing ingredients
            dish_name = parsed_intent.get("entities", {}).get("dish", "Unknown Dish")

            # If we have a GPT client, use it to determine missing ingredients
            missing_ingredients = []
            if self.gpt_client and dish_name != "Unknown Dish":
                try:
                    # Ask GPT what ingredients might be needed for the dish
                    recipe_ingredients = await self.gpt_client.generate_structured_output(
                        prompt=f"What ingredients are needed to make {dish_name}?",
                        system_message="List the ingredients needed for this recipe.",
                        output_schema={
                            "type": "object",
                            "properties": {
                                "ingredients": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "quantity": {"type": "number"},
                                            "unit": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    )

                    # Compare with available ingredients
                    available_names = [item["name"].lower() for item in inventory.get("available", [])]
                    for ingredient in recipe_ingredients.get("ingredients", []):
                        if ingredient["name"].lower() not in available_names:
                            missing_ingredients.append(ingredient)
                except Exception as e:
                    print(f"Error determining missing ingredients: {str(e)}")

            # Create inventory data
            inventory_data = InventoryData(
                available=inventory.get("available", []),
                missing=missing_ingredients
            )

            return {"inventory_data": inventory_data}