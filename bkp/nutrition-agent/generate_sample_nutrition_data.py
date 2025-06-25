"""
Sample Data Generator for Nutrition Dashboard Testing

This script generates sample nutrition data to test the dashboard functionality.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the agentic-flow directory to Python path
AGENTIC_FLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agentic-flow')
if AGENTIC_FLOW_DIR not in sys.path:
    sys.path.append(AGENTIC_FLOW_DIR)

import agents.health_diet_agent.db as db
from models.state import MacroNutrient

def generate_sample_nutrition_data(user_id='test_user', days=14):
    """
    Generate sample nutrition data for testing the dashboard.

    Args:
        user_id: User identifier for the sample data
        days: Number of days of historical data to generate
    """
    print(f"Generating {days} days of sample nutrition data for user '{user_id}'...")

    # Sample meals with their approximate nutrition values
    sample_meals = [
        {
            'name': 'Grilled Chicken Salad',
            'calories': 350, 'protein': 35, 'carbs': 15, 'fat': 12,
            'fiber': 8, 'sugar': 5, 'sodium': 450
        },
        {
            'name': 'Salmon with Rice and Vegetables',
            'calories': 520, 'protein': 42, 'carbs': 35, 'fat': 22,
            'fiber': 4, 'sugar': 8, 'sodium': 380
        },
        {
            'name': 'Greek Yogurt with Berries',
            'calories': 180, 'protein': 15, 'carbs': 25, 'fat': 3,
            'fiber': 5, 'sugar': 18, 'sodium': 85
        },
        {
            'name': 'Avocado Toast with Egg',
            'calories': 320, 'protein': 14, 'carbs': 25, 'fat': 18,
            'fiber': 8, 'sugar': 3, 'sodium': 420
        },
        {
            'name': 'Quinoa Bowl with Vegetables',
            'calories': 380, 'protein': 12, 'carbs': 58, 'fat': 8,
            'fiber': 12, 'sugar': 6, 'sodium': 320
        },
        {
            'name': 'Protein Smoothie',
            'calories': 280, 'protein': 25, 'carbs': 30, 'fat': 6,
            'fiber': 4, 'sugar': 22, 'sodium': 150
        },
        {
            'name': 'Turkey Wrap',
            'calories': 420, 'protein': 28, 'carbs': 45, 'fat': 14,
            'fiber': 6, 'sugar': 8, 'sodium': 850
        },
        {
            'name': 'Oatmeal with Nuts',
            'calories': 340, 'protein': 12, 'carbs': 55, 'fat': 12,
            'fiber': 8, 'sugar': 12, 'sodium': 180
        }
    ]

    # Generate data for each day
    for day_offset in range(days):
        date = datetime.now() - timedelta(days=day_offset)

        # Generate 2-4 meals per day
        meals_per_day = random.randint(2, 4)

        for meal_num in range(meals_per_day):
            meal = random.choice(sample_meals)

            # Add some variation to the nutrition values (±20%)
            variation = 0.8 + random.random() * 0.4  # 0.8 to 1.2

            # Create macro nutrient object
            macros = MacroNutrient(
                calories=meal['calories'] * variation,
                protein=meal['protein'] * variation,
                carbohydrates=meal['carbs'] * variation,
                fat=meal['fat'] * variation,
                fiber=meal.get('fiber', 0) * variation,
                sugar=meal.get('sugar', 0) * variation,
                sodium=meal.get('sodium', 0) * variation
            )

            # Store the nutrition inquiry
            inquiry_id = db.save_nutrition_inquiry(
                query_text=f"What are the nutrition facts for {meal['name']}?",
                query_type="recipe",
                macros=macros,
                raw_analysis={"source": "sample_data", "meal": meal['name']},
                recipe_name=meal['name'],
                servings=1,
                user_id=user_id
            )

    print(f"✅ Successfully generated {days} days of sample data!")

    # Show summary
    conn = db.sqlite3.connect(db.DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM nutrition_inquiries
        WHERE user_id = ? AND timestamp >= date('now', '-' || ? || ' days')
    """, (user_id, days))

    inquiry_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            SUM(nr.calories) as total_calories,
            AVG(nr.calories) as avg_calories,
            SUM(nr.protein) as total_protein,
            SUM(nr.carbohydrates) as total_carbs,
            SUM(nr.fat) as total_fat
        FROM nutrition_inquiries nq
        JOIN nutrition_records nr ON nq.id = nr.inquiry_id
        WHERE nq.user_id = ? AND nq.timestamp >= date('now', '-' || ? || ' days')
    """, (user_id, days))

    stats = cursor.fetchone()
    conn.close()

    print(f"\nSample Data Summary for user '{user_id}':")
    print(f"  Total inquiries: {inquiry_count}")
    print(f"  Total calories: {stats[0]:.0f}")
    print(f"  Average calories per meal: {stats[1]:.0f}")
    print(f"  Total protein: {stats[2]:.1f}g")
    print(f"  Total carbs: {stats[3]:.1f}g")
    print(f"  Total fat: {stats[4]:.1f}g")

def main():
    """Main function to generate sample data"""
    print("Nutrition Dashboard Sample Data Generator")
    print("=" * 50)

    # Initialize database
    db.init_db()

    # Generate sample data for multiple users
    users = ['test_user', 'demo_user', 'anonymous']

    for user in users:
        generate_sample_nutrition_data(user, days=21)  # 3 weeks of data
        print()

    print("🎉 Sample data generation complete!")
    print("\nYou can now test the nutrition dashboard with:")
    print("- User IDs: test_user, demo_user, anonymous")
    print("- Time range: Up to 21 days of historical data")
    print("\nRun the dashboard to see the visualizations!")

if __name__ == "__main__":
    main()
