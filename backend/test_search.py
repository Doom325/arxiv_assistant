import sys
import json
from database import SessionLocal
from routers.search import parse_query
from services.query_embedding_cache import query_cache
from models import Paper, PaperEmbedding
from sqlalchemy import func, Text

def run_search(query):
    db = SessionLocal()
    clean_query, metadata_filters = parse_query(query)
    print(f"Query: '{clean_query}'")
    
    query_embedding = query_cache.get_or_generate(
        clean_query, task_type="retrieval_query", db=db,
    )
    
    # Semantic Search with Distance
    semantic_query = db.query(
        Paper.id, 
        Paper.title, 
        PaperEmbedding.embedding.l2_distance(query_embedding).label('distance')
    ).join(PaperEmbedding, Paper.id == PaperEmbedding.paper_id)\
     .order_by('distance').limit(20)
    
    semantic_results = semantic_query.all()
    
    print("\n--- Semantic Search Results (L2 Distance, lower is better) ---")
    for i, res in enumerate(semantic_results):
        print(f"{i+1}. [Dist: {res.distance:.4f}] {res.title}")
        
    # Full Text Search with Rank
    ts_query = func.plainto_tsquery('english', clean_query)
    keyword_query = db.query(
        Paper.id,
        Paper.title,
        func.ts_rank_cd(Paper.search_vector, ts_query).label('rank')
    ).filter(
        Paper.search_vector.op('@@')(ts_query)
    ).order_by(func.ts_rank_cd(Paper.search_vector, ts_query).desc()).limit(20)
    
    keyword_results = keyword_query.all()
    
    print("\n--- Full-Text Search Results (Rank, higher is better) ---")
    for i, res in enumerate(keyword_results):
        print(f"{i+1}. [Rank: {res.rank:.4f}] {res.title}")
        
    # RRF (K=60)
    k = 60
    rrf_scores = {}
    titles = {}
    
    for i, res in enumerate(semantic_results):
        rrf_scores[res.id] = rrf_scores.get(res.id, 0) + 1.0 / (k + i + 1)
        titles[res.id] = res.title
        
    for i, res in enumerate(keyword_results):
        rrf_scores[res.id] = rrf_scores.get(res.id, 0) + 1.0 / (k + i + 1)
        titles[res.id] = res.title
        
    sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    print("\n--- Final RRF Ranked Results ---")
    for i, (pid, score) in enumerate(sorted_rrf[:20]):
        print(f"{i+1}. [Score: {score:.4f}] {titles[pid]}")

if __name__ == "__main__":
    run_search("Prompt recipes")
