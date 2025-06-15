import os
import argparse
from dotenv import load_dotenv
from health_diet_agent import HealthDietAgent
from llm_config import create_llm_config
import json
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def main():
    """Example usage of the Health & Diet Agent."""
    # Setup logger
    logger = setup_logger(__name__)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Health & Diet Agent")
    parser.add_argument(
        "--model-provider",
        choices=["openai", "github", "groq"],
        default="openai",
        help="Model provider to use (openai, github, or groq)"
    )
    args = parser.parse_args()

    try:
        # Environment variables for models are set in .env file
        logger.info(f"Initializing Health Diet Agent with {args.model_provider} provider")
        agent = HealthDietAgent(llm_provider=args.model_provider)
    except ValueError as e:
        logger.error(f"Error initializing agent: {str(e)}")
        print(f"Error initializing agent: {e}")
        return

    print("Health & Diet Agent initialized successfully!")
    print("Ask me about nutrition facts for recipes or ingredients.")
    print("Examples:")
    print("- 'What are the macros for chicken tikka masala recipe?'")
    print("- 'Analyze nutrition for 200g chicken breast, 1 cup rice, and vegetables'")
    print("- 'Give me individual breakdown for each ingredient in pasta carbonara'")
    print("\nType 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            logger.info("User exited the application")
            break

        if not user_input:
            continue

        logger.info(f"Processing user query: {user_input}")
        print("\nAnalyzing nutrition... This may take a moment.\n")

        # Analyze nutrition
        result = agent.analyze_nutrition(user_input)

        # Extract Macros JSON
        macros = agent.extract_macros(result).to_dict()

        if result["success"]:
            logger.info("Successfully analyzed nutrition query")
            print("Agent:", result["analysis"])
            print("\nMacros Breakdown:")
            print(json.dumps(macros, indent=2))
        else:
            logger.error(f"Error during nutrition analysis: {result['error']}")
            print(f"Error: {result['error']}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
