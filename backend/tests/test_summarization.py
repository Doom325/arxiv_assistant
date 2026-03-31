import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import os
import logging
from services.arxiv_service import arxiv_service
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PDF_DIR = "data/pdfs"
MODEL_NAME = "gemma3:12b"

def test_summarization():
    # 1. Find a PDF
    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF directory not found: {PDF_DIR}")
        return

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        logger.error("No PDFs found in data/pdfs")
        return

    # Pick the first one
    pdf_filename = pdf_files[0]
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    logger.info(f"Selected PDF: {pdf_filename}")

    # 2. Extract Text
    logger.info("Extracting text...")
    text = arxiv_service.extract_text(pdf_path)
    if not text:
        logger.error("Failed to extract text.")
        return
    
    logger.info(f"Extracted {len(text)} characters.")
    
    # Truncate text if too long (Gemma context window)
    # Estimate token count (rough approximation: 4 chars per token)
    est_tokens = len(text) / 4
    logger.info(f"Estimated token count: ~{int(est_tokens)}")
    
    # User requested full text
    truncated_text = text

    # 3. Summarize with Gemma
    logger.info(f"Summarizing with {MODEL_NAME}...")
    
    prompt = f"""**Your Role:** Teacher of computer science and mathematics at a University teaching Graduate students.

**Your Goal:** Create summaries of research documents with the goal of educating and teaching the user the research presented in the document

Below is the document content:
{truncated_text}"""
    
    try:
        print("\n" + "="*50)
        print(f"SUMMARY for {pdf_filename}")
        print("="*50 + "\n")
        
        # Use streaming to show progress immediately
        stream = ollama.generate(
            model=MODEL_NAME, 
            prompt=prompt, 
            stream=True,
            options={
                "num_ctx": 32768,    # Context window (Model supports 128k)
                "num_predict": 512,  # Max output tokens
                "temperature": 0.7
            }
        )
        
        for chunk in stream:
            print(chunk['response'], end='', flush=True)
            
        print("\n" + "="*50)
        
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")

if __name__ == "__main__":
    test_summarization()
