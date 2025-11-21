import sys
import os

# 将 backend 目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from app.db.base import Base
from app.models.item import RawItem
from app.models.hotspot import Hotspot

def init_db():
    print("Creating database tables...")
    try:
        # Enable pgvector extension
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
            
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
