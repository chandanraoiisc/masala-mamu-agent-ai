"""
Database Module for Nutrition Agent

This module handles database operations for storing nutrition inquiries and results.
It uses SQLite for persistence.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from models import MacroNutrient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Database file path
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db/nutrition_records.db')

def init_db():
    """Initialize the database with the required tables if they don't exist."""
    logger.info(f"Initializing database at {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create inquiries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nutrition_inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT NOT NULL,
        query_type TEXT NOT NULL,  -- 'recipe' or 'ingredients'
        timestamp DATETIME NOT NULL,
        user_id TEXT DEFAULT 'anonymous'
    )
    ''')

    # Create nutrition_records table to store the actual nutrition data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nutrition_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inquiry_id INTEGER NOT NULL,
        recipe_name TEXT,
        servings INTEGER DEFAULT 1,
        calories REAL,
        protein REAL,
        carbohydrates REAL,
        fat REAL,
        fiber REAL,
        sugar REAL,
        sodium REAL,
        raw_analysis TEXT,
        FOREIGN KEY (inquiry_id) REFERENCES nutrition_inquiries (id)
    )
    ''')

    # Create a table for individual ingredients from recipes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ingredient_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nutrition_record_id INTEGER NOT NULL,
        ingredient_name TEXT NOT NULL,
        amount TEXT,
        calories REAL,
        protein REAL,
        carbohydrates REAL,
        fat REAL,
        fiber REAL,
        sugar REAL,
        sodium REAL,
        FOREIGN KEY (nutrition_record_id) REFERENCES nutrition_records (id)
    )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def save_nutrition_inquiry(
    query_text: str,
    query_type: str,
    macros: MacroNutrient,
    raw_analysis: Dict[str, Any],
    recipe_name: Optional[str] = None,
    servings: int = 1,
    ingredients: Optional[List[Dict[str, Any]]] = None,
    user_id: str = 'anonymous'
) -> int:
    """
    Save a nutrition inquiry and its results to the database.

    Args:
        query_text: The original user query
        query_type: Type of query ('recipe' or 'ingredients')
        macros: MacroNutrient object with nutrition information
        raw_analysis: Raw analysis result from the agent
        recipe_name: Name of the recipe (if applicable)
        servings: Number of servings
        ingredients: List of ingredient nutrition info (if available)
        user_id: ID of the user (for multi-user support)

    Returns:
        The ID of the created record
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Convert datetime to string
        timestamp = datetime.now().isoformat()

        # Insert the inquiry
        cursor.execute(
            '''
            INSERT INTO nutrition_inquiries (query_text, query_type, timestamp, user_id)
            VALUES (?, ?, ?, ?)
            ''',
            (query_text, query_type, timestamp, user_id)
        )
        inquiry_id = cursor.lastrowid

        # Insert the nutrition record
        cursor.execute(
            '''
            INSERT INTO nutrition_records (
                inquiry_id, recipe_name, servings, calories, protein,
                carbohydrates, fat, fiber, sugar, sodium, raw_analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                inquiry_id,
                recipe_name,
                servings,
                macros.calories,
                macros.protein,
                macros.carbohydrates,
                macros.fat,
                macros.fiber,
                macros.sugar,
                macros.sodium,
                json.dumps(raw_analysis)
            )
        )
        nutrition_record_id = cursor.lastrowid

        # Insert ingredient records if available
        if ingredients:
            for ingredient in ingredients:
                ingredient_name = ingredient.get('ingredient', '')
                amount = ingredient.get('amount', '')
                ing_macros = ingredient.get('macros', {})

                cursor.execute(
                    '''
                    INSERT INTO ingredient_records (
                        nutrition_record_id, ingredient_name, amount,
                        calories, protein, carbohydrates, fat, fiber, sugar, sodium
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        nutrition_record_id,
                        ingredient_name,
                        amount,
                        ing_macros.get('calories'),
                        ing_macros.get('protein'),
                        ing_macros.get('carbohydrates'),
                        ing_macros.get('fat'),
                        ing_macros.get('fiber'),
                        ing_macros.get('sugar'),
                        ing_macros.get('sodium')
                    )
                )

        conn.commit()
        logger.info(f"Saved nutrition inquiry with ID {inquiry_id}")
        return inquiry_id

    except Exception as e:
        logger.error(f"Error saving nutrition inquiry: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_nutrition_history(
    user_id: str = 'anonymous',
    query_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get nutrition inquiry history for a user.

    Args:
        user_id: ID of the user
        query_type: Filter by type ('recipe' or 'ingredients')
        limit: Maximum number of records to return

    Returns:
        List of nutrition inquiry records
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
        SELECT
            nq.id, nq.query_text, nq.query_type, nq.timestamp,
            nr.recipe_name, nr.servings,
            nr.calories, nr.protein, nr.carbohydrates, nr.fat,
            nr.fiber, nr.sugar, nr.sodium
        FROM nutrition_inquiries nq
        JOIN nutrition_records nr ON nq.id = nr.inquiry_id
        WHERE nq.user_id = ?
        '''

        params = [user_id]

        if query_type:
            query += ' AND nq.query_type = ?'
            params.append(query_type)

        query += ' ORDER BY nq.timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to dictionaries
        history = []
        for row in rows:
            record = dict(row)

            # Get ingredients for all record types - both recipes and ingredients
            cursor.execute(
                '''
                SELECT
                    ir.id, ir.nutrition_record_id, ir.ingredient_name,
                    ir.amount, ir.calories, ir.protein, ir.carbohydrates,
                    ir.fat, ir.fiber, ir.sugar, ir.sodium
                FROM ingredient_records ir
                JOIN nutrition_records nr ON ir.nutrition_record_id = nr.id
                WHERE nr.inquiry_id = ?
                ''',
                (record['id'],)
            )
            ingredients = [dict(ing) for ing in cursor.fetchall()]

            # Map the database field names to the expected model field names
            for ing in ingredients:
                ing['ingredient'] = ing.pop('ingredient_name', '')

            record['ingredients'] = ingredients

            history.append(record)

        logger.info(f"Retrieved {len(history)} nutrition history records for user {user_id}")
        return history

    except Exception as e:
        logger.error(f"Error getting nutrition history: {str(e)}")
        return []
    finally:
        conn.close()


def get_macro_trends(
    user_id: str = 'anonymous',
    days: int = 30,
    macro_type: str = 'all'
) -> List[Dict[str, Any]]:
    """
    Get macro consumption trends over time.

    Args:
        user_id: ID of the user
        days: Number of days to look back
        macro_type: Type of macro to analyze ('calories', 'protein', 'carbohydrates', 'fat', or 'all')

    Returns:
        List of daily macro records
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # SQL query to get daily macro consumption
        query = '''
        SELECT
            date(nq.timestamp) as record_date,
            SUM(nr.calories) as total_calories,
            SUM(nr.protein) as total_protein,
            SUM(nr.carbohydrates) as total_carbs,
            SUM(nr.fat) as total_fat,
            COUNT(*) as record_count
        FROM nutrition_inquiries nq
        JOIN nutrition_records nr ON nq.id = nr.inquiry_id
        WHERE nq.user_id = ?
        AND nq.timestamp >= date('now', ?)
        GROUP BY date(nq.timestamp)
        ORDER BY date(nq.timestamp) ASC
        '''

        cursor.execute(query, (user_id, f'-{days} days'))
        rows = cursor.fetchall()

        trends = [dict(row) for row in rows]
        logger.info(f"Retrieved macro trends for {len(trends)} days for user {user_id}")
        return trends

    except Exception as e:
        logger.error(f"Error getting macro trends: {str(e)}")
        return []
    finally:
        conn.close()


def delete_nutrition_record(record_id: int) -> bool:
    """
    Delete a nutrition record from the database.

    Args:
        record_id: ID of the nutrition inquiry to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Delete related ingredient records first
        cursor.execute(
            '''
            DELETE FROM ingredient_records
            WHERE nutrition_record_id IN (
                SELECT id FROM nutrition_records WHERE inquiry_id = ?
            )
            ''',
            (record_id,)
        )

        # Delete nutrition record
        cursor.execute(
            'DELETE FROM nutrition_records WHERE inquiry_id = ?',
            (record_id,)
        )

        # Delete inquiry
        cursor.execute(
            'DELETE FROM nutrition_inquiries WHERE id = ?',
            (record_id,)
        )

        conn.commit()
        logger.info(f"Deleted nutrition record with ID {record_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting nutrition record: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()
