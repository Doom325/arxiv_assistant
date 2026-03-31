import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import os
import logging
from services.arxiv_service import arxiv_service
from mlx_lm import load, generate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PDF_DIR = "data/pdfs"
MODEL_REPO = "mlx-community/gemma-3-4b-it-4bit"

def test_summarization_mlx():
    # 1. Find a PDF
    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF directory not found: {PDF_DIR}")
        return

    # Target specific paper
    pdf_filename = "2511.21686v1.pdf"
    pdf_path = os.path.join(PDF_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found: {pdf_path}")
        return
    logger.info(f"Selected PDF: {pdf_filename}")

    # 2. Extract Text
    logger.info("Extracting text...")
    text = arxiv_service.extract_text(pdf_path)
    if not text:
        logger.error("Failed to extract text.")
        return
    
    logger.info(f"Extracted {len(text)} characters.")
    est_tokens = len(text) / 4
    logger.info(f"Estimated token count: ~{int(est_tokens)}")

    # 3. Load Model (MLX)
    logger.info(f"Loading model {MODEL_REPO} with MLX...")
    model, tokenizer = load(MODEL_REPO)

    # 4. Prepare Prompt
    # Sandwich the text with instructions to ensure the model doesn't get lost
    prompt = f"""<start_of_turn>user
You are an expert researcher and teacher.
Please provide a comprehensive summary of the research paper provided below.
The summary should be educational and explain the core concepts, methodology, and results to a graduate student.

--- BEGIN PAPER ---
{text}
--- END PAPER ---

**Instruction:**
Based on the paper content above, write a detailed summary. Start with a high-level overview, then explain the methodology, and finally the key results.
<end_of_turn>
<start_of_turn>model
"""

    # 5. Generate Summary
    logger.info("Generating summary...")
    print("\n" + "="*50)
    print(f"SUMMARY for {pdf_filename}")
    print("="*50 + "\n")

    response = generate(
        model, 
        tokenizer, 
        prompt=prompt, 
        max_tokens=512, 
        verbose=True
    )
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_summarization_mlx()
