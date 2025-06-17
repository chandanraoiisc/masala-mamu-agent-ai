from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, HealthData
from services.gpt_client import GPTClient


class HealthAgent(BaseAgent):
    """Agent for providing nutritional information and dietary advice"""

    def __init__(self, gpt_client: GPTClient = None):
        self.gpt_client = gpt_client
        self.system_message = """
        You are a nutritionist assistant. Your task is to provide accurate nutritional information for recipes.
        Include calories per serving, macronutrient breakdown, and dietary notes.
        """
        self.output_schema = {
            "type": "object",
            "properties": {
                "calories_per_serving": {"type": "integer"},
                "macros": {
                    "type": "object",
                    "properties": {
                        "protein": {"type": "number"},
                        "carbs": {"type": "number"},
                        "fat": {"type": "number"}
                    }
                },
                "dietary_notes": {"type": "string"}
            }
        }

    @property
    def name(self) -> str:
        return "health_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Calculate nutritional information for recipes

        Args:
            state: Current workflow state

        Returns:
            Dict with health_data key
        """
        # Get recipe data
        recipe_name = "Unknown Dish"
        ingredients = []

        if recipe_data := state.get("recipe_data"):
            recipe_name = recipe_data.name
            ingredients = recipe_data.ingredients

        if not ingredients:
            # If no ingredients, return default health data
            return {"health_data": HealthData(
                calories_per_serving=0,
                macros={"protein": 0, "carbs": 0, "fat": 0},
                dietary_notes="No recipe information available"
            )}

        # Prepare prompt for Azure OpenAI
        ingredients_list = ", ".join([f"{item['amount']} {item['name']}" for item in ingredients])
        prompt = f"Calculate nutritional information for {recipe_name} with these ingredients: {ingredients_list}"

        try:
            # Only attempt to use GPT if client is available
            if self.gpt_client:
                # Generate nutritional information using Azure OpenAI
                health_json = await self.gpt_client.generate_structured_output(
                    prompt=prompt,
                    system_message=self.system_message,
                    output_schema=self.output_schema
                )

                # Convert to HealthData model
                health_data = HealthData(**health_json)
                return {"health_data": health_data}
            else:
                raise ConnectionError("GPT client not available")

        except Exception as e:
            # Fallback to mock data if Azure OpenAI fails
            print(f"Azure OpenAI nutritional calculation failed: {str(e)}")

            # Mock health
            health_data = HealthData(
                calories_per_serving=650,
                macros={
                    "protein": 35,
                    "carbs": 80,
                    "fat": 22
                },
                dietary_notes="High in protein. Contains gluten from the rice. Rich in complex carbohydrates."
            )

            return {"health_data": health_data}