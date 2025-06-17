import unittest
import asyncio
from services.gpt_client import GPTClient
from router.parser import IntentParser
from router.orchestrator import WorkflowOrchestrator
from agents.inventory_agent import InventoryAgent
from agents.recipe_agent import RecipeAgent
from agents.shopping_agent import ShoppingAgent
from agents.health_agent import HealthAgent


class MockAzureGPTClient:
    """Mock Azure OpenAI client for testing"""

    async def generate_completion(self, prompt, system_message="", temperature=None):
        return "This is a mock response from Azure OpenAI"

    async def generate_structured_output(self, prompt, system_message, output_schema, temperature=None):
        # Return different mock data based on the prompt
        if "Analyze this kitchen assistant query" in prompt:
            return {
                "primary_intent": "recipe_generation",
                "secondary_intents": ["shopping_comparison", "health_advice"],
                "entities": {
                    "dish": "hyderabadi chicken biryani"
                },
                "required_agents": ["recipe_agent", "inventory_agent", "shopping_agent", "health_agent"]
            }
        elif "Generate a detailed recipe" in prompt or "recipe for" in prompt:
            return {
                "name": "Hyderabadi Chicken Biryani",
                "ingredients": [
                    {"name": "rice", "amount": "2 cups", "required": True},
                    {"name": "chicken", "amount": "500g", "required": True},
                    {"name": "onion", "amount": "2 large", "required": True}
                ],
                "missing_ingredients": [
                    {"name": "saffron", "amount": "a pinch"},
                    {"name": "mint", "amount": "1/4 cup"}
                ],
                "instructions": [
                    "Marinate chicken with yogurt and spices for 1 hour",
                    "Parboil rice with whole spices until 70% cooked",
                    "Layer marinated chicken and parboiled rice in a heavy-bottomed pot",
                    "Cook on low heat (dum) for 25 minutes"
                ],
                "cooking_time": "1 hour 30 minutes",
                "servings": 4
            }
        elif "Check inventory" in prompt:
            return {
                "available": [
                    {"name": "rice", "quantity": 500, "unit": "g"},
                    {"name": "chicken", "quantity": 1, "unit": "kg"},
                    {"name": "onion", "quantity": 5, "unit": "pieces"}
                ],
                "missing": [
                    {"name": "saffron", "quantity": 1, "unit": "g"},
                    {"name": "mint", "quantity": 1, "unit": "bunch"}
                ]
            }
        elif "Compare prices" in prompt:
            return {
                "platform_comparisons": {
                    "blinkit": {"total": 450, "delivery_time": "15 min"},
                    "zepto": {"total": 420, "delivery_time": "10 min"},
                    "instamart": {"total": 480, "delivery_time": "20 min"}
                },
                "best_option": "zepto",
                "total_cost": 420
            }
        elif "Calculate nutritional information" in prompt:
            return {
                "calories_per_serving": 650,
                "macros": {"protein": 35, "carbs": 80, "fat": 22},
                "dietary_notes": "High in protein, contains gluten"
            }
        else:
            return {"error": "Unrecognized prompt"}


class TestWorkflow(unittest.TestCase):
    def test_basic_workflow(self):
        """Test the basic workflow with all agents"""

        async def run_async_test():
            # Setup with mock Azure GPT client
            mock_gpt_client = MockAzureGPTClient()
            intent_parser = IntentParser(gpt_client=mock_gpt_client)
            orchestrator = WorkflowOrchestrator()

            # Register agents with mock Azure GPT client
            orchestrator.register_agent(InventoryAgent(gpt_client=mock_gpt_client))
            orchestrator.register_agent(RecipeAgent(gpt_client=mock_gpt_client))
            orchestrator.register_agent(ShoppingAgent(gpt_client=mock_gpt_client))
            orchestrator.register_agent(HealthAgent(gpt_client=mock_gpt_client))

            # Build workflow
            orchestrator.build_workflow()

            # Test query
            query = "give me recipe to make hyderabadi chicken biryani and give what and all i have to buy and where i can buy and tell the calories"

            # Parse intent
            parsed_intent = await intent_parser.parse(query)

            # Execute workflow
            result = await orchestrator.execute({
                "query": query,
                "parsed_intent": parsed_intent,
                "required_agents": parsed_intent.get("required_agents", []),
                "completed_agents": []
            })

            return result

        # Run the async test in the synchronous test method
        result = asyncio.run(run_async_test())

        # Assertions
        self.assertIn("response", result)
        self.assertTrue("error" not in result or not result["error"])
        self.assertIn("recipe_data", result)
        self.assertIn("shopping_data", result)
        self.assertIn("health_data", result)


if __name__ == "__main__":
    unittest.main()