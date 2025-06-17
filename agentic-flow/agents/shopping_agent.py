from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, ShoppingData
from services.gpt_client import GPTClient


class ShoppingAgent(BaseAgent):
    """Agent for comparing prices across shopping platforms"""

    def __init__(self, gpt_client: GPTClient = None):
        self.gpt_client = gpt_client
        self.system_message = """
        You are a shopping assistant that compares prices across different grocery delivery platforms.
        Your task is to provide price comparisons for ingredients across Blinkit, Zepto, and Instamart.
        Recommend the best option based on price and delivery time.
        """
        self.output_schema = {
            "type": "object",
            "properties": {
                "platform_comparisons": {
                    "type": "object",
                    "properties": {
                        "blinkit": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "number"},
                                "delivery_time": {"type": "string"},
                                "items": {"type": "object"}
                            }
                        },
                        "zepto": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "number"},
                                "delivery_time": {"type": "string"},
                                "items": {"type": "object"}
                            }
                        },
                        "instamart": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "number"},
                                "delivery_time": {"type": "string"},
                                "items": {"type": "object"}
                            }
                        }
                    }
                },
                "best_option": {"type": "string"},
                "total_cost": {"type": "number"}
            }
        }

    @property
    def name(self) -> str:
        return "shopping_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Compare prices for ingredients across different platforms

        Args:
            state: Current workflow state

        Returns:
            Dict with shopping_data key
        """
        # Get missing ingredients from recipe data
        missing_ingredients = []
        if recipe_data := state.get("recipe_data"):
            missing_ingredients = recipe_data.missing_ingredients

        if not missing_ingredients:
            # If no missing ingredients, return empty shopping data
            return {"shopping_data": ShoppingData(
                platform_comparisons={},
                best_option="",
                total_cost=0
            )}

        # Prepare prompt for Azure OpenAI
        ingredients_list = ", ".join([f"{item['amount']} {item['name']}" for item in missing_ingredients])
        prompt = f"Compare prices for these ingredients across Blinkit, Zepto, and Instamart: {ingredients_list}"

        try:
            # Only attempt to use GPT if client is available
            if self.gpt_client:
                # Generate shopping comparison using Azure OpenAI
                shopping_json = await self.gpt_client.generate_structured_output(
                    prompt=prompt,
                    system_message=self.system_message,
                    output_schema=self.output_schema
                )

                # Convert to ShoppingData model
                shopping_data = ShoppingData(**shopping_json)
                return {"shopping_data": shopping_data}
            else:
                raise ConnectionError("GPT client not available")

        except Exception as e:
            # Fallback to mock data if Azure OpenAI fails
            print(f"Azure OpenAI shopping comparison failed: {str(e)}")

            # Mock shopping data
            shopping_data = ShoppingData(
                platform_comparisons={
                    "blinkit": {
                        "total": 450,
                        "delivery_time": "15 min",
                        "items": {
                            "saffron": {"price": 250, "brand": "Organic"},
                            "mint": {"price": 80, "brand": "Fresh"}
                        }
                    },
                    "zepto": {
                        "total": 420,
                        "delivery_time": "10 min",
                        "items": {
                            "saffron": {"price": 230, "brand": "Premium"},
                            "mint": {"price": 80, "brand": "Fresh"}
                        }
                    },
                    "instamart": {
                        "total": 480,
                        "delivery_time": "20 min",
                        "items": {
                            "saffron": {"price": 270, "brand": "Kashmir"},
                            "mint": {"price": 80, "brand": "Fresh"}
                        }
                    }
                },
                best_option="zepto",
                total_cost=420
            )

            return {"shopping_data": shopping_data}