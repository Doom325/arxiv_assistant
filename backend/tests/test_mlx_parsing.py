
import sys
import os
import logging
import json
import re

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from production_worker import PDFProcessorLite

logging.basicConfig(level=logging.INFO)

def test_mlx_worker_logic():
    mock_ref_text = """
    References
    [1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. In Advances in neural information processing systems (pp. 5998-6008). https://arxiv.org/abs/1706.03762
    [2] Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.
    [3] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. Advances in neural information processing systems, 33, 1877-1901.
    """
    
    processor = PDFProcessorLite()
    print("Parsing references using PDFProcessorLite._parse_citations_with_mlx...")
    try:
        results = processor._parse_citations_with_mlx(mock_ref_text)
        print(f"\nFinal Extracted {len(results)} citations:")
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_mlx_worker_logic()
