import os
from dotenv import load_dotenv
from health_diet_agent import HealthDietAgent
import json

# Load environment variables
load_dotenv()

def main():
    """Example usage of the Health & Diet Agent."""

    # Initialize the agent
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        print("Please set OPENAI_API_KEY in your .env file")
        return

    agent = HealthDietAgent(
        openai_api_key=openai_api_key
    )

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
