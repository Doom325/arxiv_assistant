
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
        
        from models import Base # Import here for all blocks
        
        # 1. Start JobLogs Table
        # We rely on sqlalchemy to create new tables
        if not inspector.has_table("job_logs"):
            print("Creating job_logs table...")
            from models import Base
            # This creates ALL tables that don't exist
            Base.metadata.create_all(engine)
            print("job_logs table created.")
        else:
             print("job_logs table already exists.")
             # Check columns just in case?
             cols = [c['name'] for c in inspector.get_columns("job_logs")]
             print(f"Columns: {cols}")

        if not inspector.has_table("summarization_metrics"):
             print("Creating summarization_metrics table...")
             Base.metadata.create_all(engine)
             print("summarization_metrics table created.")
        else:
            # Check for new columns
            cols = [c['name'] for c in inspector.get_columns("summarization_metrics")]
            if "status" not in cols:
                print("Adding columns to summarization_metrics...")
                conn.execute(text("ALTER TABLE summarization_metrics ADD COLUMN file_size_bytes BIGINT"))
                conn.execute(text("ALTER TABLE summarization_metrics ADD COLUMN status VARCHAR DEFAULT 'SUCCESS'"))
                conn.execute(text("ALTER TABLE summarization_metrics ADD COLUMN error_message TEXT"))
                print("Column migration complete.")

        # 2. Add Column is_downloaded to papers
        columns = [c['name'] for c in inspector.get_columns("papers")]
        if "is_downloaded" not in columns:
            print("Adding is_downloaded column to papers table...")
            conn.execute(text("ALTER TABLE papers ADD COLUMN is_downloaded BOOLEAN DEFAULT FALSE"))
            print("Column added.")
        else:
            print("Column is_downloaded already exists.")

        # 3. Add list_name to user_library
        if inspector.has_table("user_library"):
            lib_columns = [c['name'] for c in inspector.get_columns("user_library")]
            if "list_name" not in lib_columns:
                print("Adding list_name column to user_library table...")
                conn.execute(text("ALTER TABLE user_library ADD COLUMN list_name VARCHAR DEFAULT 'Bookmarks'"))
                conn.execute(text("CREATE INDEX idx_user_list ON user_library (user_id, list_name)"))
                print("Column and index added.")
            else:
                print("Column list_name already exists.")

if __name__ == "__main__":
    migrate()
