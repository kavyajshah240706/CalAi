import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def get_food_macros(food_name: str) -> dict:
    """
    Search the database for the requested food macros per 100g.
    Returns dictionary with macros or None if not found.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        with conn.cursor() as cursor:
            # Fuzzy matching or ILIKE for Postgres
            query = """
                SELECT food_name, density_g_ml, kcal_per_100g, protein_per_100g, carbs_per_100g, fats_per_100g 
                FROM food_macros 
                WHERE food_name ILIKE %s
                LIMIT 1
            """
            cursor.execute(query, (f"%{food_name}%",))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Error querying food macros: {e}")
        return None
    finally:
        conn.close()
