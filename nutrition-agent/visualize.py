"""
Visualization utility for nutrition data

This script provides visualization functionality for nutrition data
stored in the SQLite database.
"""

import os
import argparse
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import db
from utils.logger import setup_logger

logger = setup_logger(__name__)

def load_nutrition_data(days=30, user_id='anonymous'):
    """
    Load nutrition data from the database for visualization.

    Args:
        days: Number of days to look back
        user_id: User identifier

    Returns:
        Pandas DataFrame with nutrition data
    """
    try:
        conn = sqlite3.connect(db.DB_FILE)

        # Query to get daily nutrition data
        query = """
        SELECT
            date(nq.timestamp) as date,
            SUM(nr.calories) as calories,
            SUM(nr.protein) as protein,
            SUM(nr.carbohydrates) as carbs,
            SUM(nr.fat) as fat,
            COUNT(*) as entries
        FROM nutrition_inquiries nq
        JOIN nutrition_records nr ON nq.id = nr.inquiry_id
        WHERE nq.user_id = ?
        AND nq.timestamp >= date('now', ?)
        GROUP BY date(nq.timestamp)
        ORDER BY date(nq.timestamp)
        """

        # Load data into DataFrame
        df = pd.read_sql_query(query, conn, params=(user_id, f'-{days} days'))

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Fill in missing dates
        if not df.empty:
            date_range = pd.date_range(
                start=max(df['date'].min(), datetime.now() - timedelta(days=days)),
                end=datetime.now(),
                freq='D'
            )

            # Create a complete DataFrame with all dates
            complete_df = pd.DataFrame({'date': date_range})
            df = pd.merge(complete_df, df, on='date', how='left')
            df.fillna(0, inplace=True)

        conn.close()
        return df

    except Exception as e:
        logger.error(f"Error loading nutrition data: {str(e)}")
        return pd.DataFrame()

def plot_macro_trends(days=30, user_id='anonymous', save_path=None):
    """
    Generate plots for macro consumption trends.

    Args:
        days: Number of days to analyze
        user_id: User identifier
        save_path: Path to save the plot image (if None, shows the plot)
    """
    df = load_nutrition_data(days, user_id)

    if df.empty:
        logger.warning("No nutrition data available for plotting")
        return False

    # Create figure with subplots
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    # Set suptitle
    fig.suptitle(f'Nutrition Trends - Past {days} Days', fontsize=16)

    # Plot calories
    axs[0, 0].plot(df['date'], df['calories'], 'b-o', linewidth=2, markersize=6)
    axs[0, 0].set_title('Daily Calorie Intake')
    axs[0, 0].set_ylabel('Calories (kcal)')
    axs[0, 0].grid(True)
    axs[0, 0].xaxis.set_major_formatter(DateFormatter('%m-%d'))

    # Plot protein
    axs[0, 1].plot(df['date'], df['protein'], 'r-o', linewidth=2, markersize=6)
    axs[0, 1].set_title('Daily Protein Intake')
    axs[0, 1].set_ylabel('Protein (g)')
    axs[0, 1].grid(True)
    axs[0, 1].xaxis.set_major_formatter(DateFormatter('%m-%d'))

    # Plot carbs
    axs[1, 0].plot(df['date'], df['carbs'], 'g-o', linewidth=2, markersize=6)
    axs[1, 0].set_title('Daily Carbohydrate Intake')
    axs[1, 0].set_xlabel('Date')
    axs[1, 0].set_ylabel('Carbs (g)')
    axs[1, 0].grid(True)
    axs[1, 0].xaxis.set_major_formatter(DateFormatter('%m-%d'))

    # Plot fat
    axs[1, 1].plot(df['date'], df['fat'], 'y-o', linewidth=2, markersize=6)
    axs[1, 1].set_title('Daily Fat Intake')
    axs[1, 1].set_xlabel('Date')
    axs[1, 1].set_ylabel('Fat (g)')
    axs[1, 1].grid(True)
    axs[1, 1].xaxis.set_major_formatter(DateFormatter('%m-%d'))

    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save or display
    if save_path:
        plt.savefig(save_path)
        logger.info(f"Saved nutrition trends plot to {save_path}")
        plt.close()
        return True
    else:
        plt.show()
        return True

def plot_macro_distribution(days=30, user_id='anonymous', save_path=None):
    """
    Generate a pie chart showing the distribution of macronutrients.

    Args:
        days: Number of days to analyze
        user_id: User identifier
        save_path: Path to save the plot image (if None, shows the plot)
    """
    df = load_nutrition_data(days, user_id)

    if df.empty:
        logger.warning("No nutrition data available for plotting")
        return False

    # Calculate totals
    total_protein = df['protein'].sum()
    total_carbs = df['carbs'].sum()
    total_fat = df['fat'].sum()

    # Calculate calories from each macro
    protein_cals = total_protein * 4  # 4 calories per gram
    carb_cals = total_carbs * 4       # 4 calories per gram
    fat_cals = total_fat * 9          # 9 calories per gram

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # Plot 1: Macro Distribution by Weight
    labels = ['Protein', 'Carbs', 'Fat']
    sizes = [total_protein, total_carbs, total_fat]
    colors = ['#ff9999', '#66b3ff', '#99ff99']
    explode = (0.1, 0, 0)  # explode the 1st slice (Protein)

    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax1.set_title('Macronutrient Distribution by Weight')

    # Plot 2: Macro Distribution by Calories
    sizes_cals = [protein_cals, carb_cals, fat_cals]

    ax2.pie(sizes_cals, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax2.axis('equal')
    ax2.set_title('Macronutrient Distribution by Calories')

    # Add main title
    fig.suptitle(f'Nutrition Distribution - Past {days} Days', fontsize=16)

    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save or display
    if save_path:
        plt.savefig(save_path)
        logger.info(f"Saved nutrition distribution plot to {save_path}")
        plt.close()
        return True
    else:
        plt.show()
        return True

def main():
    """Main function for visualization CLI."""
    parser = argparse.ArgumentParser(description='Nutrition Data Visualization')

    parser.add_argument('--type', choices=['trends', 'distribution', 'all'], default='all',
                        help='Type of visualization to generate')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to analyze')
    parser.add_argument('--user', type=str, default='anonymous',
                        help='User ID to analyze')
    parser.add_argument('--save', type=str,
                        help='Directory to save the plots (if not provided, displays plots instead)')

    args = parser.parse_args()

    # Create save directory if provided
    if args.save and not os.path.exists(args.save):
        os.makedirs(args.save)

    # Generate plots based on type
    if args.type in ['trends', 'all']:
        save_path = os.path.join(args.save, 'macro_trends.png') if args.save else None
        plot_macro_trends(args.days, args.user, save_path)

    if args.type in ['distribution', 'all']:
        save_path = os.path.join(args.save, 'macro_distribution.png') if args.save else None
        plot_macro_distribution(args.days, args.user, save_path)

if __name__ == '__main__':
    main()
