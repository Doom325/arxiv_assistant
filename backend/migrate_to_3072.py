
import os
import glob
from sqlalchemy import create_engine, text
from config import settings

def migrate():
    print(f"🚀 Starting migration to 3072d dimensionality...")
    
    # 1. Database Update
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            print("Resetting all embeddings to NULL first...")
            conn.execute(text("UPDATE papers SET embedding = NULL"))
            conn.commit()
            
            print("Changing embedding column to Vector(3072)...")
            conn.execute(text("ALTER TABLE papers ALTER COLUMN embedding TYPE vector(3072)"))
            conn.commit()
            print("✅ Database schema updated and embeddings reset.")
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return

    # 2. Cleanup local files
    print("Cleaning up old batch tracking files...")
    
    # Batch input files
    batch_files = glob.glob("batch_input_*.jsonl")
    for f in batch_files:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except:
            pass

    # Batch tracking JSON
    if os.path.exists("batch_embedding_jobs.json"):
        try:
            os.remove("batch_embedding_jobs.json")
            print("Removed batch_embedding_jobs.json")
        except:
            pass
            
    # Results files
    result_files = glob.glob("results_*.jsonl")
    for f in result_files:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except:
            pass

    print("✅ Cleanup complete.")
    print("Done! You can now run 'python batch_embed_manager.py prepare' followed by 'submit_all'.")

if __name__ == "__main__":
    migrate()
