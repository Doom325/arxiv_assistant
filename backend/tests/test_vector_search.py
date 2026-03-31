
import logging
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pdf_processor import PDFProcessor

# Configuration
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

logging.basicConfig(level=logging.ERROR) # Quiet pypdf logs
logger = logging.getLogger("VectorSearch")
logger.setLevel(logging.INFO)

def search_papers(query: str, top_k: int = 5):
    # 1. Generate Embedding for Query
    logger.info(f"Generating embedding for query: '{query}'")
    processor = PDFProcessor()
    query_embedding = processor.generate_embedding(query)
    
    if not query_embedding:
        logger.error("Failed to generate embedding.")
        return

    # 2. Search DB using pgvector
    logger.info("Searching database...")
    engine = create_engine(DB_URL)
    
    # Cosine distance operator is <=>
    # We want closest distance => Order By distance ASC
    sql = text("""
        SELECT 
            arxiv_id, 
            title, 
            extracted_abstract,
            1 - (abstract_embedding <=> :embedding) as similarity
        FROM papers
        WHERE abstract_embedding IS NOT NULL
        ORDER BY abstract_embedding <=> :embedding ASC
        LIMIT :top_k
    """)
    
    with engine.connect() as conn:
        # Pass embedding string representation [0.1, 0.2, ...] works for pgvector python
        results = conn.execute(sql, {"embedding": str(query_embedding), "top_k": top_k}).fetchall()
        
    logger.info(f"--- Top {top_k} Results for '{query}' ---")
    for i, row in enumerate(results):
        print(f"\nResult #{i+1} (Score: {row.similarity:.4f})")
        print(f"ID: {row.arxiv_id}")
        print(f"Title: {row.title}")
        print(f"Snippet: {row.extracted_abstract[:200]}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Vector Search")
    parser.add_argument("query", type=str, help="Search query string")
    args = parser.parse_args()
    
    search_papers(args.query)
