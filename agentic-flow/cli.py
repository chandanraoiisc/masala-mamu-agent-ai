import asyncio
import os
import logging
from dotenv import load_dotenv
from services.gpt_client import GPTClient
from router.parser import IntentParser
from router.orchestrator import WorkflowOrchestrator
from agents.inventory_agent import InventoryAgent
from agents.receipe_agent import RecipeAgent
from agents.shopping_agent import ShoppingAgent
from agents.health_agent import HealthAgent
from agents.response_generator_agent import ResponseGeneratorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


async def main():
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    if not api_key or not endpoint or not deployment:
        print("ERROR: Missing Azure OpenAI settings. Please check your .env file.")
        print(f"API Key: {'Set' if api_key else 'Missing'}")
        print(f"Endpoint: {'Set' if endpoint else 'Missing'}")
        print(f"Deployment: {'Set' if deployment else 'Missing'}")
        return

    print(f"Using Azure OpenAI API key: {api_key[:5]}...{api_key[-4:]}")
    print(f"Using Azure OpenAI endpoint: {endpoint}")
    print(f"Using Azure OpenAI deployment: {deployment}")

    try:
        gpt_client = GPTClient(
            api_key=api_key,
            endpoint=endpoint,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            deployment=deployment
        )

        print("Testing Azure OpenAI API connection...")
        try:
            test_response = await gpt_client.generate_completion("Hello", "Respond with 'Connection successful'")
            print(f"Connection test result: {test_response}")
        except ConnectionError as e:
            print(f"ERROR: Could not connect to Azure OpenAI API: {str(e)}")
            print("Continuing with fallback responses only...")

        intent_parser = IntentParser(gpt_client=gpt_client)
        orchestrator = WorkflowOrchestrator()

        orchestrator.register_agent(InventoryAgent(gpt_client=gpt_client))
        orchestrator.register_agent(RecipeAgent())
        orchestrator.register_agent(ShoppingAgent(gpt_client=gpt_client))
        orchestrator.register_agent(HealthAgent())
        orchestrator.register_agent(ResponseGeneratorAgent(gpt_client=gpt_client))  # Add this line

        orchestrator.build_workflow()

        print("\nKitchen Assistant CLI")
        print("Type 'exit' to quit")

        while True:
            query = input("\nEnter your query: ")

            if query.lower() == 'exit':
                break

            try:
                print("Parsing intent...")
                parsed_intent = await intent_parser.parse(query)
                print(f"Detected intent: {parsed_intent['primary_intent']}")
                print(parsed_intent)
                initial_state = {
                    "query": query,
                    "parsed_intent": parsed_intent,
                    "required_agents": parsed_intent.get("required_agents", []),
                    "completed_agents": []
                }

                print("Processing...")
                result = await orchestrator.execute(initial_state)

                if "response" in result:
                    print("\n" + "=" * 50)
                    print(result["response"])
                    print("=" * 50)
                else:
                    print("No response generated")

            except Exception as e:
                print(f"Error: {str(e)}")

    except Exception as e:
        print(f"Fatal error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())