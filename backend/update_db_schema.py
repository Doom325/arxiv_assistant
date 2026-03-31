
from sqlalchemy import create_engine
from config import settings
from models import Base, BatchQueue # Import BatchQueue explicitly to ensure it is registered

def update_schema():
    print(f"Connecting to DB...")
    # Use the DB URL from environment
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating tables...")
    # create_all checks for existence first, so it is safe to run
    Base.metadata.create_all(engine)
    print("Schema update complete. BatchQueue table should exist.")

if __name__ == "__main__":
    update_schema()
