import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return
        
    print(f"Connecting to {db_url.split('@')[-1]}...")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Enable pgvector
        print("Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. Create food_macros table
        print("Creating food_macros table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_macros (
                id SERIAL PRIMARY KEY,
                food_name VARCHAR(255) NOT NULL,
                density_g_ml NUMERIC,
                kcal_per_100g NUMERIC,
                protein_per_100g NUMERIC,
                carbs_per_100g NUMERIC,
                fats_per_100g NUMERIC
            );
        """)
        
        # 3. Create meal_logs table
        print("Creating meal_logs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meal_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) DEFAULT 'test_user',
                food_name VARCHAR(255) NOT NULL,
                weight_g NUMERIC,
                calories NUMERIC,
                protein NUMERIC,
                carbs NUMERIC,
                fats NUMERIC,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3.5 Create chat_logs table
        print("Creating chat_logs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) DEFAULT 'test_user',
                role VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert some dummy food data if empty
        cursor.execute("SELECT COUNT(*) FROM food_macros;")
        if cursor.fetchone()[0] == 0:
            print("Inserting default macro data...")
            cursor.execute("""
                INSERT INTO food_macros (food_name, density_g_ml, kcal_per_100g, protein_per_100g, carbs_per_100g, fats_per_100g)
                VALUES 
                ('Apple', 0.8, 52, 0.3, 14, 0.2),
                ('Grilled Chicken Breast', 1.05, 165, 31, 0, 3.6),
                ('Steamed Broccoli', 0.9, 34, 2.8, 6.6, 0.4),
                ('White Rice (Cooked)', 1.0, 130, 2.7, 28, 0.3);
            """)
            
        # 4. Create user_profiles table
        print("Creating user_profiles table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                age INTEGER,
                gender VARCHAR(20),
                height_cm NUMERIC,
                weight_kg NUMERIC,
                activity_level VARCHAR(50),
                daily_calorie_target NUMERIC,
                protein_goal_g NUMERIC,
                carbs_goal_g NUMERIC,
                fats_goal_g NUMERIC
            );
        """)
        
        # Insert default profile if empty
        cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE user_id = 'admin_user';")
        if cursor.fetchone()[0] == 0:
            print("Inserting default user profile...")
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, email, age, gender, height_cm, weight_kg, activity_level, daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g)
                VALUES 
                ('admin_user', 'Alex Mercer', 'alex.mercer@example.com', 32, 'Male', 180, 75.5, 'Moderately Active', 2450, 160, 245, 82);
            """)

        # Enable Row Level Security (RLS) on all public tables to prevent Supabase warnings
        print("Enabling Row Level Security (RLS) on public tables...")
        for table in ["food_macros", "meal_logs", "user_profiles", "chat_logs", "langchain_pg_collection", "langchain_pg_embedding"]:
            try:
                cursor.execute(f"ALTER TABLE IF EXISTS {table} ENABLE ROW LEVEL SECURITY;")
            except Exception as e:
                print(f"Note: Could not enable RLS on {table} (it might not exist yet). {e}")

        print("Database setup complete!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database setup failed: {e}")

if __name__ == "__main__":
    setup_database()
