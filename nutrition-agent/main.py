import os
import argparse
from dotenv import load_dotenv
from health_diet_agent import HealthDietAgent
from llm_config import create_llm_config
import json

# Load environment variables
load_dotenv()

def main():
    """Example usage of the Health & Diet Agent."""

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
        agent = HealthDietAgent(llm_provider=args.model_provider)
    except ValueError as e:
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
            break

        if not user_input:
            continue

        print("\nAnalyzing nutrition... This may take a moment.\n")

        # Analyze nutrition
        result = agent.analyze_nutrition(user_input)

        if result["success"]:
            print("Agent:", result["analysis"])
        else:
            print(f"Error: {result['error']}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
