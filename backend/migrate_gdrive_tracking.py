
from sqlalchemy import create_engine, text, inspect
from config import settings
import logging

# Ensure correct DB URL
DB_URL = settings.DATABASE_URL

def migrate():
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # Add in_drive_details to papers
        columns = [c['name'] for c in inspector.get_columns("papers")]
        if "in_drive_details" not in columns:
            print("Adding in_drive_details column to papers table...")
            # Use JSONB for PostgreSQL if possible, but SQLAlchemy JSON maps to JSONB in Postgres
            conn.execute(text("ALTER TABLE papers ADD COLUMN in_drive_details JSONB"))
            print("Column added.")
        else:
            print("Column in_drive_details already exists.")

if __name__ == "__main__":
    migrate()
