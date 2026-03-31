
import re
import logging
from pypdf import PdfReader
from typing import Dict, Optional, List
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# Configure logger
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, model_id="google/embeddinggemma-300m"):
        self.model_id = model_id
        self.tokenizer = None
        self.model = None

    def load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_id}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(self.model_id, trust_remote_code=True)
            self.model.eval()

    def generate_embedding(self, text: str) -> List[float]:
        self.load_model()
        if not text or not text.strip():
            return []
            
        # Gemma has large context window, but let's be safe with truncation
        inputs = self.tokenizer([text], padding=True, truncation=True, return_tensors='pt')
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Mean Pooling logic for GemmaEmbed
        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        sentence_embeddings = sum_embeddings / sum_mask
        
        # Normalize
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        
        return sentence_embeddings[0].tolist()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts full text from a PDF file."""
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            return full_text
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def extract_sections(self, full_text: str) -> Dict[str, str]:
        """
        Extracts 'Abstract' and 'Introduction' sections from the full text.
        Returns a dictionary with keys 'abstract' and 'introduction'.
        """
        lower_text = full_text.lower()
        
        # --- ABSTRACT EXTRACTION ---
        abstract_start_match = re.search(r'(^|\n)\s*abstract[:.]?\s*', lower_text)
        
        if not abstract_start_match:
            logger.warning("Abstract header not found.")
            abstract_text = ""
        else:
            abstract_start_idx = abstract_start_match.start()
            intro_start_match = re.search(r'(^|\n)\s*(1\.?|i\.?|I\.?)?\s*introduction[:.]?\s*', lower_text[abstract_start_idx:])
            
            if intro_start_match:
                abstract_end_idx = abstract_start_idx + intro_start_match.start()
                abstract_text = full_text[abstract_start_idx:abstract_end_idx]
            else:
                abstract_text = full_text[abstract_start_idx:abstract_start_idx+2000]
            
            abstract_text = re.sub(r'^\s*abstract[:.]?\s*', '', abstract_text.strip(), flags=re.IGNORECASE)

        # --- INTRODUCTION EXTRACTION ---
        intro_text = ""
        intro_start_match = re.search(r'(^|\n)\s*(1\.?|i\.?|I\.?)?\s*introduction[:.]?\s*', lower_text)
        
        if intro_start_match:
            intro_start_idx = intro_start_match.end()
            
            search_region = lower_text[intro_start_idx:intro_start_idx+5000]
            next_section_pattern = r'(^|\n)\s*(2\.?|ii\.?|II\.?|related work|background|method|model|preliminaries)'
            next_section_match = re.search(next_section_pattern, search_region)
            
            if next_section_match:
                intro_end_idx = intro_start_idx + next_section_match.start()
                intro_text = full_text[intro_start_idx:intro_end_idx]
            else:
                intro_text = full_text[intro_start_idx:intro_start_idx+3000]
            
            intro_text = intro_text.strip()
        else:
             logger.warning("Introduction header not found.")

        return {
            "abstract": abstract_text,
            "introduction": intro_text
        }

    def process_pdf(self, pdf_path: str):
        """High-level function to process a PDF and return structured data with embeddings."""
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None
            
        sections = self.extract_sections(text)
        
        # Generate Embeddings
        logger.info(f"Generating embeddings for {pdf_path}...")
        abstract_emb = self.generate_embedding(sections['abstract'])
        intro_emb = self.generate_embedding(sections['introduction'])
        
        return {
            "file": pdf_path,
            "sections": sections,
            "embeddings": {
                "abstract": abstract_emb,
                "introduction": intro_emb
            }
        }

if __name__ == "__main__":
    # Test Block
    logging.basicConfig(level=logging.INFO)
    processor = PDFProcessor()
    result = processor.process_pdf("backend/sample.pdf")
    
    if result:
        print(f"--- Processed {result['file']} ---")
        print(f"Abstract Length: {len(result['sections']['abstract'])} chars")
        print(f"Intro Length: {len(result['sections']['introduction'])} chars")
        
        abs_emb_len = len(result['embeddings']['abstract']) if result['embeddings']['abstract'] else 0
        intro_emb_len = len(result['embeddings']['introduction']) if result['embeddings']['introduction'] else 0
        
        print(f"Abstract Embedding Dim: {abs_emb_len}")
        print(f"Intro Embedding Dim: {intro_emb_len}")
        
        if abs_emb_len > 0:
            print(f"Abstract Veector (first 5): {result['embeddings']['abstract'][:5]}")
    else:
        print("Failed to process PDF")
