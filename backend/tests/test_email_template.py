import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Paper
from services.email_service import email_service

# Connect to DB
DB_URL = "postgresql://user:password@localhost:5434/arxiv_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("Fetching latest 10 papers from DB...")
papers = db.query(Paper).order_by(Paper.published_date.desc()).limit(10).all()

if not papers:
    print("No papers found in DB!")
else:
    real_summary = """
**1. Core Problem:**

The paper addresses the limitations of existing sequence transduction models, which primarily rely on recurrent neural networks (RNNs) or convolutional neural networks (CNNs). These models often struggle with parallelization, particularly when dealing with long sequences, and can be computationally expensive. The fundamental issue is that RNNs process sequences sequentially, preventing efficient parallelization, while CNNs can be slow to learn long-range dependencies.

**2. Key Innovation:**

The central contribution is the **Transformer** architecture – a novel model that completely abandons recurrence and convolution layers, relying *solely* on a mechanism called **self-attention** to capture dependencies between elements in a sequence.  This allows for significantly better parallelization and potentially faster training, especially for longer sequences. The key idea is to directly relate any two positions in the sequence, regardless of their distance, using attention weights.

**3. Methodology:**

*   **Self-Attention Mechanism:** The core of the Transformer is the self-attention layer. This layer computes a weighted sum of the input sequence, where the weights are determined by how much each element in the sequence attends to every other element.
*   **Multi-Head Attention:**  Multiple independent attention mechanisms (heads) are used in parallel to capture different aspects of the relationships within the sequence.
*   **Feed-Forward Networks:**  After the attention layers, each position in the sequence is processed by a simple, position-wise feed-forward network.
*   **Residual Connections & Layer Normalization:**  Residual connections and layer normalization are used to improve training stability and performance.

**4. Key Results:**

*   **State-of-the-Art Translation:** The Transformer achieved a new state-of-the-art BLEU score on both the English-to-German and English-to-French translation tasks.
*   **Training Efficiency:** The Transformer could be trained in significantly less time (3.5 days on 8 P100 GPUs for the big model) compared to previous state-of-the-art models.
"""
    
    # Apply real summary to ALL papers to test density
    for p in papers:
        p.generated_summary = real_summary

    html = email_service._generate_html(papers)

    with open("backend/email_preview.html", "w") as f:
        f.write(html)

    print("Saved preview to backend/email_preview.html")
