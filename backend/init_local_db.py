
from sqlalchemy import create_engine, text
from models import Base
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    url = settings.DATABASE_URL
    logger.info(f"Initializing DB at {url}")
    engine = create_engine(url)
    
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        logger.info("Vector extension enabled.")
        
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

if __name__ == "__main__":
    init_db()
