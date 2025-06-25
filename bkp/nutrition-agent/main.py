import os
import argparse
from dotenv import load_dotenv
from health_diet_agent import HealthDietAgent
from llm_config import create_llm_config
import json
from utils.logger import setup_logger
import matplotlib.pyplot as plt
from datetime import datetime

# Import the streamlit visualization module
try:
    import streamlit
    STREAMLIT_AVAILABLE = True
    from streamlit_viz import show_nutrition_dashboard
except ImportError:
    STREAMLIT_AVAILABLE = False

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
        default="github",
        help="Model provider to use (openai, github, or groq)"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Disable database storage of nutrition inquiries"
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Display nutrition inquiry history"
    )
    parser.add_argument(
        "--trends",
        type=int,
        metavar="DAYS",
        help="Show macro trends for the specified number of days"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive Streamlit visualization dashboard"
    )
    parser.add_argument(
        "--delete",
        type=int,
        metavar="ID",
        help="Delete a nutrition record by ID"
    )
    args = parser.parse_args()

    try:
        # Environment variables for models are set in .env file
        logger.info(f"Initializing Health Diet Agent with {args.model_provider} provider")
        agent = HealthDietAgent(
            llm_provider=args.model_provider,
            enable_db=not args.no_db
        )
    except ValueError as e:
        logger.error(f"Error initializing agent: {str(e)}")
        print(f"Error initializing agent: {e}")
        return

    # Handle special commands
    if args.history:
        show_nutrition_history(agent)
        return

    if args.trends:
        show_macro_trends(agent, args.trends)
        return

    if args.interactive:
        if STREAMLIT_AVAILABLE:
            logger.info("Launching interactive Streamlit dashboard")
            print("Launching interactive Streamlit visualization dashboard...")
            # Use sys.argv to directly call streamlit since we need to modify the arguments
            # We use exec as a workaround to run streamlit from within Python
            import sys
            import subprocess
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_viz.py")
            subprocess.call(["streamlit", "run", script_path])
            return
        else:
            logger.error("Streamlit is not installed. Please install it with: pip install streamlit plotly")
            print("Streamlit is not installed. Please install it with: pip install streamlit plotly")
            return

    if args.delete:
        delete_nutrition_record(agent, args.delete)
        return

    print("Health & Diet Agent initialized successfully!")
    print("Ask me about nutrition facts for recipes or ingredients.")
    print("Examples:")
    print("- 'What are the macros for chicken tikka masala recipe?'")
    print("- 'Analyze nutrition for 200g chicken breast, 1 cup rice, and vegetables'")
    print("- 'Give me individual breakdown for each ingredient in pasta carbonara'")
    print("\nSpecial commands:")
    print("- Type 'history' to view your nutrition inquiry history")
    print("- Type 'trends' to see your macro consumption trends")
    if STREAMLIT_AVAILABLE:
        print("- Type 'dashboard' to launch interactive nutrition dashboard")
    print("\nType 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            logger.info("User exited the application")
            break

        if user_input.lower() == 'history':
            show_nutrition_history(agent)
            continue

        if user_input.lower() == 'trends':
            show_macro_trends(agent, 30)  # Default to 30 days
            continue

        if user_input.lower() == 'dashboard' and STREAMLIT_AVAILABLE:
            print("\nLaunching interactive nutrition dashboard...\n")
            import subprocess
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_viz.py")
            subprocess.Popen(["streamlit", "run", script_path])
            print("Dashboard launched in a new window. You can continue using this command line interface.")
            continue

        if not user_input:
            continue

        logger.info(f"Processing user query: {user_input}")
        print("\nAnalyzing nutrition... This may take a moment.\n")

        # Analyze nutrition (now with integrated DB save)
        result = agent.analyze_nutrition(user_input)

        if not result["success"]:
            logger.error(f"Error during nutrition analysis: {result['error']}")
            print(f"Error: {result['error']}")
            continue

        # Get macros from the result
        macros = result["macros"]
        if not macros:
            logger.error("Failed to extract macros from analysis")
            print("Error: Could not extract macronutrients from the analysis.")
            continue

        # Display results
        logger.info("Successfully analyzed nutrition query")
        print("Agent:", result["analysis"])
        print("\nMacros Breakdown:")
        print(json.dumps(macros.to_dict(), indent=2))

        print("\n" + "="*50 + "\n")


def show_nutrition_history(agent, limit=10):
    """Display the user's nutrition inquiry history."""
    print("\nRetrieving nutrition history...\n")

    history = agent.get_nutrition_history(limit=limit)

    if not history:
        print("No nutrition history found.")
        return

    print(f"Found {len(history)} nutrition records:\n")

    for i, record in enumerate(history, 1):
        print(f"{i}. [ID: {record.id}] {record.timestamp.strftime('%Y-%m-%d %H:%M')} - {record.recipe_name or 'Ingredients'}")
        print(f"   Query: {record.query_text}")
        print(f"   Calories: {record.macros.calories or 0} kcal, Protein: {record.macros.protein or 0}g, " +
              f"Carbs: {record.macros.carbohydrates or 0}g, Fat: {record.macros.fat or 0}g")
        print()

    print("=" * 50)


def show_macro_trends(agent, days=30):
    """Show macro consumption trends over time."""
    print(f"\nAnalyzing macro trends for the past {days} days...\n")

    trends = agent.get_macro_trends(days=days)

    if "error" in trends:
        print(f"Error retrieving trends: {trends['error']}")
        return

    if not trends["dates"]:
        print("No data available for the specified period.")
        return

    # Plot macro trends if matplotlib is available
    try:
        plt.figure(figsize=(12, 8))

        # Create 4 subplots for different macros
        plt.subplot(2, 2, 1)
        plt.plot(trends["dates"], trends["calories"], 'b-o')
        plt.title('Calorie Intake Over Time')
        plt.ylabel('Calories')
        plt.grid(True)

        plt.subplot(2, 2, 2)
        plt.plot(trends["dates"], trends["protein"], 'r-o')
        plt.title('Protein Intake Over Time')
        plt.ylabel('Protein (g)')
        plt.grid(True)

        plt.subplot(2, 2, 3)
        plt.plot(trends["dates"], trends["carbohydrates"], 'g-o')
        plt.title('Carbohydrate Intake Over Time')
        plt.xlabel('Date')
        plt.ylabel('Carbs (g)')
        plt.grid(True)

        plt.subplot(2, 2, 4)
        plt.plot(trends["dates"], trends["fat"], 'y-o')
        plt.title('Fat Intake Over Time')
        plt.xlabel('Date')
        plt.ylabel('Fat (g)')
        plt.grid(True)

        plt.tight_layout()

        # Save the plot
        plt.savefig('macro_trends.png')
        plt.close()

        print("Macro trends have been saved as 'macro_trends.png'")
        print("You can open this file to view your nutrition trends.")

    except Exception as e:
        # Print trends as text if plotting fails
        print("Macro Trends (table view):")
        print("Date\t\tCalories\tProtein(g)\tCarbs(g)\tFat(g)")
        for i in range(len(trends["dates"])):
            print(f"{trends['dates'][i]}\t{trends['calories'][i]:.1f}\t\t{trends['protein'][i]:.1f}\t\t{trends['carbohydrates'][i]:.1f}\t\t{trends['fat'][i]:.1f}")

    print("\n" + "=" * 50)


def delete_nutrition_record(agent, record_id):
    """Delete a nutrition record by ID."""
    print(f"\nDeleting nutrition record {record_id}...\n")

    success = agent.delete_nutrition_record(record_id)

    if success:
        print(f"Successfully deleted nutrition record {record_id}.")
    else:
        print(f"Failed to delete nutrition record {record_id}.")

    print("\n" + "=" * 50)


def launch_interactive_dashboard(agent):
    """Launch the interactive Streamlit visualization dashboard."""
    print("\nLaunching interactive Streamlit dashboard...\n")

    # Here we would typically call streamlit.run() or similar,
    # but for this script, we'll just simulate the action.
    try:
        import streamlit as st

        # Sample code to demonstrate launching Streamlit (this won't run in a non-streamlit context)
        st.title("Health & Diet Agent - Nutrition Dashboard")
        st.write("Welcome to the interactive nutrition dashboard.")
        st.write("Ask me about nutrition facts for recipes or ingredients.")

        # Placeholder for actual dashboard content
        # In a real Streamlit app, we would define the layout and components here
        st.write("Dashboard content goes here...")

        # For example, showing trends in Streamlit
        trends = agent.get_macro_trends(days=30)
        if trends and "dates" in trends:
            st.line_chart({
                "data": trends["dates"],
                "calories": trends["calories"],
                "protein": trends["protein"],
                "carbohydrates": trends["carbohydrates"],
                "fat": trends["fat"],
            })
        else:
            st.write("No trends data available.")

        st.write("End of dashboard.")

    except Exception as e:
        print(f"Error launching dashboard: {e}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
