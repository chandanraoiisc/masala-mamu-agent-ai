from typing import Dict, Any, List
from services.gpt_client import GPTClient


class IntentParser:

    def __init__(self, gpt_client: GPTClient = None):
        self.gpt_client = gpt_client
        self.system_message = """
        You are an AI assistant for a kitchen management system with four specialized agents:
        1. inventory_agent: Tracks available ingredients in the kitchen
        2. recipe_agent: Generates recipes based on user requests
        3. shopping_agent: Compares prices across Blinkit, Zepto, and Instamart
        4. health_agent: Provides nutritional information and dietary advice

        Analyze the user query and determine:
        1. The primary intent (recipe_generation, inventory_check, shopping_comparison, health_advice)
        2. Secondary intents (if any)
        3. Key entities (dish names, ingredients, dietary restrictions, etc.)
        4. Which agents should be called and in what order to best fulfill the request

        For example:
        - "What ingredients do I need for pasta?" → inventory_agent → recipe_agent
        - "Give me a recipe for chicken curry" → recipe_agent
        - "Where can I buy tomatoes cheapest?" → shopping_agent
        - "How many calories in a pizza?" → recipe_agent → health_agent
        - "Give me a recipe for biryani, tell me what to buy and the calories" → recipe_agent → inventory_agent → shopping_agent → health_agent

        Respond with a structured JSON object only.
        """
        self.output_schema = {
            "type": "object",
            "properties": {
                "primary_intent": {"type": "string"},
                "secondary_intents": {"type": "array", "items": {"type": "string"}},
                "entities": {
                    "type": "object",
                    "properties": {
                        "dish": {"type": "string"},
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "dietary_restrictions": {"type": ["string", "null"]}
                    }
                },
                "agent_flow": {"type": "array", "items": {"type": "string"}},
                "reasoning": {"type": "string"}
            }
        }

    async def parse(self, query: str) -> Dict[str, Any]:

        try:

            if self.gpt_client:
                parsed_result = await self.gpt_client.generate_structured_output(
                    prompt=f"Analyze this kitchen assistant query and determine the optimal agent flow: {query}",
                    system_message=self.system_message,
                    output_schema=self.output_schema
                )

                if "agent_flow" in parsed_result:
                    parsed_result["required_agents"] = parsed_result["agent_flow"]

                return parsed_result
            else:
                raise ConnectionError("GPT client not available")
        except Exception as e:
            print(f"Azure OpenAI parsing failed: {str(e)}")
            return self._simple_fallback(query)

    def _simple_fallback(self, query: str) -> Dict[str, Any]:

        return {
            "primary_intent": "recipe_generation",
            "secondary_intents": ["inventory_check", "shopping_comparison", "health_advice"],
            "entities": {"dish": "food"},
            "required_agents": ["recipe_agent", "inventory_agent", "shopping_agent", "health_agent"],
            "reasoning": "Fallback due to LLM unavailability"
        }