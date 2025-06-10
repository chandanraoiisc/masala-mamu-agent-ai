import os
from dotenv import load_dotenv
from router_integration import create_kitchen_assistant_with_nutrition
import json

# Load environment variables
load_dotenv()

def test_router_integration():
    """Test the router integration with sample queries."""

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        return

    # Create kitchen assistant router with nutrition agent
    router = create_kitchen_assistant_with_nutrition(
        openai_api_key=openai_api_key
    )

    # Test queries
    test_queries = [
        "What are the macros for a chicken tikka masala recipe?",
        "Can you break down the nutrition for each ingredient in pasta carbonara?",
        "How many calories are in 200g of grilled chicken breast?",
        "What's the weather like today?",  # This should not be handled
        "Analyze the nutrition of 1 cup rice, 150g chicken, and mixed vegetables"
    ]

    print("Testing Kitchen Assistant Router with Nutrition Agent")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)

        # Add some context for demonstration
        context = {
            "user_preferences": "Looking for healthy options",
            "previous_queries": ["Previous nutrition analysis"]
        }

        result = router.route_query(query, context)

        print(f"Can Handle: {result['can_handle']}")
        print(f"Agent: {result.get('agent_name', 'None')}")
        print(f"Success: {result.get('success', 'N/A')}")
        print(f"Response: {result['response'][:200]}..." if len(result['response']) > 200 else f"Response: {result['response']}")

    print("\n" + "=" * 60)
    print("Router integration test completed!")

if __name__ == "__main__":
    test_router_integration()
