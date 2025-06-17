from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, RecipeData
from services.gpt_client import GPTClient


class RecipeAgent(BaseAgent):
    """Agent for generating recipes"""

    def __init__(self, gpt_client: GPTClient = None):
        self.gpt_client = gpt_client
        self.system_message = """
        You are a professional chef assistant. Your task is to generate detailed recipes based on user requests.
        Include ingredients with quantities, step-by-step instructions, cooking time, and servings.
        If information about available ingredients is provided, adapt the recipe accordingly.
        """
        self.output_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "amount": {"type": "string"},
                            "required": {"type": "boolean"}
                        }
                    }
                },
                "missing_ingredients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "amount": {"type": "string"}
                        }
                    }
                },
                "instructions": {"type": "array", "items": {"type": "string"}},
                "cooking_time": {"type": "string"},
                "servings": {"type": "integer"}
            }
        }

    @property
    def name(self) -> str:
        return "recipe_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate recipe based on user query

        Args:
            state: Current workflow state

        Returns:
            Dict with recipe_data key
        """
        query = state["query"]
        parsed_intent = state["parsed_intent"]
        dish_name = parsed_intent.get("entities", {}).get("dish", "Unknown Dish")

        # Prepare prompt with available ingredients if present
        prompt_parts = [f"Generate a detailed recipe for {dish_name}."]

        if inventory_data := state.get("inventory_data"):
            available_ingredients = [item["name"] for item in inventory_data.available]
            prompt_parts.append(f"Available ingredients: {', '.join(available_ingredients)}.")
            prompt_parts.append("Please indicate which ingredients are missing and need to be purchased.")

        prompt = " ".join(prompt_parts)

        try:
            # Only attempt to use GPT if client is available
            if self.gpt_client:
                # Generate recipe using Azure OpenAI
                recipe_json = await self.gpt_client.generate_structured_output(
                    prompt=prompt,
                    system_message=self.system_message,
                    output_schema=self.output_schema
                )

                # Convert to RecipeData model
                recipe_data = RecipeData(**recipe_json)
                return {"recipe_data": recipe_data}
            else:
                raise ConnectionError("GPT client not available")

        except Exception as e:
            # Fallback to mock data if Azure OpenAI fails
            print(f"Azure OpenAI recipe generation failed: {str(e)}")

            # Mock recipe data
            recipe_data = RecipeData(
                name=dish_name,
                ingredients=[
                    {"name": "rice", "amount": "2 cups", "required": True},
                    {"name": "chicken", "amount": "500g", "required": True},
                    {"name": "onion", "amount": "2 large", "required": True},
                    {"name": "yogurt", "amount": "1 cup", "required": True},
                    {"name": "saffron", "amount": "a pinch", "required": False},
                    {"name": "mint", "amount": "1/4 cup", "required": True}
                ],
                missing_ingredients=[
                    {"name": "yogurt", "amount": "1 cup"},
                    {"name": "saffron", "amount": "a pinch"},
                    {"name": "mint", "amount": "1/4 cup"}
                ],
                instructions=[
                    "Marinate chicken with yogurt and spices for 1 hour",
                    "Parboil rice with whole spices until 70% cooked",
                    "Layer marinated chicken and parboiled rice in a heavy-bottomed pot",
                    "Cook on low heat (dum) for 25 minutes",
                    "Garnish with fried onions, mint, and saffron milk"
                ],
                cooking_time="1 hour 30 minutes",
                servings=4
            )

            return {"recipe_data": recipe_data}