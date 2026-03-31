import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import UserConfig

DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

def check_configs():
    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        configs = db.query(UserConfig).all()
        
        print(f"User Configs Found: {len(configs)}")
        if configs:
            for c in configs:
                print(f"User Email: {c.email}")
                print(f"Categories: {c.categories}")
        else:
            print("No User Configs found. System is using DEFAULT categories:")
            defaults = {
                "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", 
                "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY"
            }
            print(defaults)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_configs()
