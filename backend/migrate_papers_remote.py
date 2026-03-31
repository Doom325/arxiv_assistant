
from sqlalchemy import create_engine, text
import logging

# Connect to Khadas IP
DB_URL = "postgresql://user:password@192.168.1.49:5434/arxiv_db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RemoteMigration")

def migrate():
    logger.info(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        logger.info("Updating 'papers' table schema...")
        
        # Add columns if they don't exist
        # PostgreSQL doesn't support multiple columns in one ADD COLUMN with IF NOT EXISTS in all versions, 
        # so we do them individually for safety.
        columns = [
            ("is_downloaded", "BOOLEAN DEFAULT FALSE"),
            ("extracted_abstract", "TEXT"),
            ("extracted_introduction", "TEXT"),
            ("citations", "JSONB"),
            ("abstract_embedding", "VECTOR(768)"),
            ("introduction_embedding", "VECTOR(768)")
        ]
        
        for name, type_def in columns:
            try:
                conn.execute(text(f"ALTER TABLE papers ADD COLUMN IF NOT EXISTS {name} {type_def};"))
                logger.info(f"✅ Column 'papers.{name}' checked/added.")
            except Exception as e:
                logger.error(f"❌ Failed to add column 'papers.{name}': {e}")

        # Update user_library table
        logger.info("Updating 'user_library' table schema...")
        try:
            conn.execute(text("ALTER TABLE user_library ADD COLUMN IF NOT EXISTS list_name VARCHAR DEFAULT 'Bookmarks';"))
            logger.info("✅ Column 'user_library.list_name' checked/added.")
        except Exception as e:
            logger.error(f"❌ Failed to add column 'user_library.list_name': {e}")

        # Handle search_vector (Generated column)
        logger.info("Checking for 'search_vector'...")
        res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='papers' AND column_name='search_vector'")).fetchone()
        if not res:
            try:
                logger.info("Adding 'search_vector' generated column...")
                conn.execute(text("""
                    ALTER TABLE papers 
                    ADD COLUMN search_vector tsvector 
                    GENERATED ALWAYS AS (
                        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, ''))
                    ) STORED;
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_papers_search ON papers USING GIN(search_vector);"))
                logger.info("✅ Added 'search_vector' and index.")
            except Exception as e:
                logger.error(f"❌ Failed to add 'search_vector': {e}")
        else:
            logger.info("✅ Column 'search_vector' already exists.")

        # Ensure vector extension is enabled just in case
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("✅ Extension 'vector' checked.")
        except Exception as e:
            logger.error(f"❌ Failed to check/add 'vector' extension: {e}")

        conn.commit()
    logger.info("🚀 Remote migration complete!")

if __name__ == "__main__":
    migrate()
