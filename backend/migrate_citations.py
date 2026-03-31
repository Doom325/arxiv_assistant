from sqlalchemy import create_engine, text
from config import settings

def migrate():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Checking for 'citations' column...")
        # Check if column exists
        if "postgresql" in settings.DATABASE_URL:
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='papers' AND column_name='citations';
            """)
        else:
            # SQLite fallback
            check_sql = text("PRAGMA table_info(papers);")
            
        result = conn.execute(check_sql).fetchall()
        
        column_exists = False
        if "postgresql" in settings.DATABASE_URL:
            column_exists = len(result) > 0
        else:
            column_exists = any(row[1] == 'citations' for row in result)

        if not column_exists:
            print("Adding 'citations' column to 'papers' table...")
            if "postgresql" in settings.DATABASE_URL:
                conn.execute(text("ALTER TABLE papers ADD COLUMN citations JSONB;"))
            else:
                conn.execute(text("ALTER TABLE papers ADD COLUMN citations JSON;"))
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column 'citations' already exists.")

if __name__ == "__main__":
    migrate()
