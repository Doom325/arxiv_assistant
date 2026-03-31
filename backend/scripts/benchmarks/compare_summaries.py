import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
import os
import google.generativeai as genai
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from datetime import date
from config import settings

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiCompare")

# DB
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"

# Configure Gemini
from dotenv import load_dotenv, find_dotenv
# Explicitly look for .env in the current directory or parent
load_dotenv(find_dotenv())

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables!")
    # Try alternate name
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("No API Key found. Please set GEMINI_API_KEY in .env")

genai.configure(api_key=api_key)

# Using 1.5 Flash as standard efficient model (User said 2.5 Flash Lite but that's likely unavailable/typo)
import time

# Fallback to standard model
MODEL_NAME = "gemini-2.5-flash-lite-preview-09-2025" 

def generate_comparison():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    output_file = "gemini_summary.md"
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        target_dates = [date(2025, 12, 12), date(2025, 12, 11)]
        papers = db.query(Paper).filter(
            Paper.published_date.in_(target_dates),
            Paper.generated_summary.isnot(None) # Only those we already processed
        ).all()
        
        logger.info(f"Found {len(papers)} papers with existing summaries.")
        
        with open(output_file, "a") as f:
            for i, paper in enumerate(papers):
                logger.info(f"Processing ({i+1}/{len(papers)}): {paper.title[:50]}...")
                
                # Construct Prompt
                # Use extracted intro/abstract if available, else standard summary
                text_content = ""
                if paper.extracted_introduction:
                    text_content += f"Introduction: {paper.extracted_introduction[:4000]}\n"
                if paper.extracted_abstract:
                    text_content += f"Abstract: {paper.extracted_abstract}\n"
                
                if not text_content:
                    text_content = f"Abstract: {paper.summary}"

                prompt = f"""
                Please summarize the following academic paper content into a structured format:
                1. Core Problem
                2. Key Innovation
                3. Methodology
                4. Key Results
                
                Content:
                {text_content}
                """
                
                try:
                    response = model.generate_content(prompt)
                    gemini_summary = response.text
                    
                    # Write to markdown
                    f.write(f"\n\n# Paper: {paper.title}\n")
                    f.write(f"**Arxiv ID**: {paper.arxiv_id}\n\n")
                    
                    f.write("## 🤖 Gemma Summary (Local)\n")
                    f.write(f"{paper.generated_summary}\n\n")
                    
                    f.write(f"## ✨ Gemini Summary ({MODEL_NAME})\n")
                    f.write(f"{gemini_summary}\n\n")
                    f.write("---\n")
                    f.flush() # Ensure write
                    logger.info(f"✅ Generated summary for {paper.arxiv_id}. Sleeping to respect rate limit...")
                    
                except Exception as e:
                    logger.error(f"Gemini Error for {paper.arxiv_id}: {e}")
                    f.write(f"\n\n# Paper: {paper.title}\n")
                    f.write(f"**Error generating Gemini summary**: {e}\n\n---\n")
                
                # Rate Limit: 10 per minute = 1 every 6 seconds. Using 7s for safety.
                time.sleep(7) 

    except Exception as e:
        logger.error(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    generate_comparison()
