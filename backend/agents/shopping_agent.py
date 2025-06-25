from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState, ShoppingData
from services.gpt_client import GPTClient
from agents.shopping_service.agent.price_compare_agent import create_price_comparison_agent
from config import settings


class ShoppingAgent(BaseAgent):
    """Agent for comparing prices across shopping platforms"""

    def __init__(self, gpt_client: GPTClient = None, google_api_key: str = ""):
        print(google_api_key)
        self.gpt_client = gpt_client
        self.price_agent = create_price_comparison_agent(settings.GOOGLE_API_KEY)
        self.system_message = """
        You are a smart price comparison assistant. Your job is to extract the best shopping platform 
        and total cost from the price comparison report provided below.

        The report may mention prices from platforms like Zepto, Instamart, Blinkit, etc.

        Your output must always be in JSON format with exactly these keys:
        - best_option: the platform offering the lowest overall cost for all ingredients
        - total_cost: the numeric total price (in INR) of the cheapest option

        Ignore brand preferences. Just pick the cheapest option.
        """

        self.output_schema = {
            "type": "object",
            "properties": {
                # "platform_comparisons": {
                #     "type": "object",
                #     "properties": {
                #         "blinkit": {
                #             "type": "object",
                #             "properties": {
                #                 "total": {"type": "number"},
                #                 "delivery_time": {"type": "string"},
                #                 "items": {"type": "object"}
                #             }
                #         },
                #         "zepto": {
                #             "type": "object",
                #             "properties": {
                #                 "total": {"type": "number"},
                #                 "delivery_time": {"type": "string"},
                #                 "items": {"type": "object"}
                #             }
                #         },
                #         "instamart": {
                #             "type": "object",
                #             "properties": {
                #                 "total": {"type": "number"},
                #                 "delivery_time": {"type": "string"},
                #                 "items": {"type": "object"}
                #             }
                #         }
                #     }
                # },
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

    # async def process(self, state: AgentState) -> Dict[str, Any]:
    #     """
    #     Compare prices for ingredients across different platforms
    #
    #     Args:
    #         state: Current workflow state
    #
    #     Returns:
    #         Dict with shopping_data key
    #     """
    #     # Get missing ingredients from recipe data
    #     missing_ingredients = []
    #     if recipe_data := state.get("recipe_data"):
    #         missing_ingredients = recipe_data.missing_ingredients
    #         print(missing_ingredients)
    #
    #     query = state.get("query", "").strip()
    #
    #     # Fallback if no recipe context
    #     if not missing_ingredients and query:
    #         # Extract ingredients from query (optionally use an NLP model)
    #         ingredients_list = query
    #     elif missing_ingredients:
    #         ingredients_list = ", ".join([f"{item['amount']} {item['name']}" for item in missing_ingredients])
    #     else:
    #         return {"shopping_data": ShoppingData(
    #             platform_comparisons={},
    #             best_option="",
    #             total_cost=0
    #         )}
    #
    #     # Prepare prompt for Azure OpenAI
    #     # ingredients_list = ", ".join([f"{item['amount']} {item['name']}" for item in missing_ingredients])
    #     prompt = f"Compare prices for these ingredients : {ingredients_list}"
    #
    #     try:
    #         result_str = await self.price_agent.run(prompt)
    #         print("data from shopping ",result_str)
    #         # Only attempt to use GPT if client is available
    #         if self.gpt_client:
    #             # Generate shopping comparison using Azure OpenAI
    #             price_list = "this is the result from my scrapper: " + result_str
    #             shopping_json = await self.gpt_client.generate_structured_output(
    #                 prompt=price_list,
    #                 system_message=self.system_message,
    #                 output_schema=self.output_schema
    #             )
    #             print("shopping json: ",shopping_json)
    #             # Convert to ShoppingData model
    #             shopping_data = ShoppingData(**shopping_json)
    #             return {"shopping_data": shopping_data}
    #         # else:
    #         #     raise ConnectionError("GPT client not available")
    #         return {"shopping_data": result_str}
    #     except Exception as e:
    #         # Fallback to mock data if Azure OpenAI fails
    #         print(f"Azure OpenAI shopping comparison failed: {str(e)}")
    #
    #         # Mock shopping data
    #         shopping_data = ShoppingData(
    #             platform_comparisons={
    #                 "blinkit": {
    #                     "total": 450,
    #                     "delivery_time": "15 min",
    #                     "items": {
    #                         "saffron": {"price": 250, "brand": "Organic"},
    #                         "mint": {"price": 80, "brand": "Fresh"}
    #                     }
    #                 },
    #                 "zepto": {
    #                     "total": 420,
    #                     "delivery_time": "10 min",
    #                     "items": {
    #                         "saffron": {"price": 230, "brand": "Premium"},
    #                         "mint": {"price": 80, "brand": "Fresh"}
    #                     }
    #                 },
    #                 "instamart": {
    #                     "total": 480,
    #                     "delivery_time": "20 min",
    #                     "items": {
    #                         "saffron": {"price": 270, "brand": "Kashmir"},
    #                         "mint": {"price": 80, "brand": "Fresh"}
    #                     }
    #                 }
    #             },
    #             best_option="zepto",
    #             total_cost=420
    #         )
    #
    #         return {"shopping_data": shopping_data}
    async def process(self, state: AgentState) -> Dict[str, Any]:
        missing_ingredients = []
        if recipe_data := state.get("inventory_data"):
            missing_ingredients = recipe_data.missing

        query = state.get("query", "").strip()
        print(missing_ingredients)
        if not missing_ingredients and query:
            ingredients_list = query
        elif missing_ingredients:
            ingredients_list = ", ".join([f"{item['quantity']} {item['name']}" for item in missing_ingredients])
        else:
            return {"shopping_data": ShoppingData(
                platform_comparisons={},
                best_option="",
                total_cost=0
            )}

        try:
            print(ingredients_list)
            # 🔁 Step 1: Get result from price agent
            result_str = await self.price_agent.run(f"Compare prices for: {ingredients_list}")
            print("Scraper result:\n", result_str)

            # 🔁 Step 2: Use GPT to extract best_option and total_cost from it
            price_list = "This is the result from my scrapper:\n" + result_str

            if self.gpt_client:
                shopping_json = await self.gpt_client.generate_structured_output(
                    prompt=price_list,
                    system_message=self.system_message,
                    output_schema=self.output_schema
                )
                print("Parsed shopping JSON:", shopping_json)
                shopping_data = ShoppingData(**shopping_json)
                print("Shopping data:", shopping_data)
                return {"shopping_data": shopping_data}

            # fallback
            return {"shopping_data": result_str}

        except Exception as e:
            print(f"Shopping agent failed: {str(e)}")

            # fallback mock
            shopping_data = ShoppingData(
                best_option="Zepto",
                total_cost=420
            )
            return {"shopping_data": shopping_data}

