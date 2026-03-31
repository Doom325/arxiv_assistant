import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from models import SummarizationMetric

# Use localhost:5434 for Mac Local
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def show_results():
    db = SessionLocal()
    try:
        # Get basic stats
        count = db.query(SummarizationMetric).count()
        print(f"Total Metrics Collected: {count}")
        
        if count == 0:
            print("No metrics found.")
            return

        # Get averages and peaks for SUCCESS
        stats = db.query(
            func.avg(SummarizationMetric.peak_memory_mb).label('avg_mem'),
            func.max(SummarizationMetric.peak_memory_mb).label('max_mem'),
            func.avg(SummarizationMetric.num_input_tokens).label('avg_in'),
            func.avg(SummarizationMetric.num_output_tokens).label('avg_out'),
            func.avg(SummarizationMetric.num_chars).label('avg_chars')
        ).filter(SummarizationMetric.status == 'SUCCESS').first()

        print("-" * 30)
        print(f"Stats (SUCCESS only):")
        print(f"Average Peak Memory: {stats.avg_mem:.2f} MB")
        print(f"Max Peak Memory:     {stats.max_mem:.2f} MB")
        print(f"Average Input Tokens: {stats.avg_in:.1f}")
        print("-" * 30)
        
        # Show breakdown of Failures
        failed_count = db.query(SummarizationMetric).filter(SummarizationMetric.status == 'FAILED').count()
        print(f"Failed Count: {failed_count}")
        
        # Show recent entries with size and status
        print("\nRecent Entries:")
        metrics = db.query(SummarizationMetric).order_by(SummarizationMetric.id.desc()).limit(10).all()
        for m in metrics:
            size_mb = (m.file_size_bytes or 0) / (1024*1024)
            print(f"ID: {m.paper_id} | Size: {size_mb:.2f}MB | Status: {m.status} | Mem: {m.peak_memory_mb:.0f}MB | Msg: {m.error_message or ''}")

    except Exception as e:
        print(f"Error querying metrics: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_results()
