
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    DB_URL = settings.DATABASE_URL
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        print("Altering published_date and updated_date to TIMESTAMP...")
        conn.execute(text("ALTER TABLE papers ALTER COLUMN published_date TYPE TIMESTAMP WITHOUT TIME ZONE"))
        conn.execute(text("ALTER TABLE papers ALTER COLUMN updated_date TYPE TIMESTAMP WITHOUT TIME ZONE"))
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
