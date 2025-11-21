import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine

def update_schema():
    print("Updating database schema...")
    try:
        with engine.connect() as connection:
            # Enable vector extension
            print("Enabling vector extension...")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            
            # Add embedding column if not exists
            print("Ensuring embedding column exists...")
            try:
                connection.execute(text("ALTER TABLE raw_items ADD COLUMN IF NOT EXISTS embedding vector(2560)"))
                print("Column verified (created if missing).")
            except Exception as e:
                print(f"Error ensuring column: {e}")

            print("Aligning embedding column dimension...")
            try:
                connection.execute(text("ALTER TABLE raw_items ALTER COLUMN embedding TYPE vector(2560)"))
                print("Column dimension updated to 2560.")
            except Exception as e:
                print(f"Error updating column dimension: {e}")
                
            connection.commit()
            print("Schema update completed.")
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
