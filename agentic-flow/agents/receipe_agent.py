from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, RecipeData
from agents.receipe_service.dish_suggester import suggest_dish
import json

class RecipeAgent(BaseAgent):
    """Agent for generating recipes using HuggingFace LLM logic"""

    def __init__(self):
        self.system_message = """
        You are a professional chef assistant. Your task is to generate detailed recipes based on user requests.
        Include ingredients with quantities, step-by-step instructions, cooking time, and servings.
        If information about available ingredients is provided, adapt the recipe accordingly.
        """

    @property
    def name(self) -> str:
        return "recipe_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        query = state["query"]
        parsed_intent = state["parsed_intent"]
        dish_name = parsed_intent.get("entities", {}).get("dish", "Unknown Dish")

        input_ingredients = []

        # Include inventory-based ingredients if available
        if inventory_data := state.get("inventory_data"):
            input_ingredients = [item["name"] for item in inventory_data.available]
            ingredients_str = f"{query} using ingredients: {', '.join(input_ingredients)}"
        else:
            ingredients_str = query

        try:
            suggestion_text = suggest_dish(ingredients_str)

            # Extract and parse JSON from the response text
            json_str = suggestion_text.strip().split("```")[-1]
            parsed_json = json.loads(json_str)

            # Convert parsed JSON into RecipeData
            recipe_data = RecipeData(
                name=parsed_json.get("dish_name", dish_name),
                ingredients=[
                    {"name": k, "amount": v, "required": True}
                    for k, v in parsed_json.get("ingredients", {}).items()
                ],
                missing_ingredients=[],  # Extend if needed
                instructions=[
                    step for _, step in sorted(parsed_json.get("instructions", {}).items())
                ] if "instructions" in parsed_json else [],
                cooking_time="unknown",
                servings=1
            )

            return {"recipe_data": recipe_data}

        except Exception as e:
            print(f"Dish suggestion failed: {str(e)}")
            return {
                "recipe_data": RecipeData(
                    name="Error", ingredients=[], instructions=[], cooking_time="N/A", servings=0
                )
            }
