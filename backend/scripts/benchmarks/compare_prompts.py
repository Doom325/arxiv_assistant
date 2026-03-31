
import os
import requests
from pypdf import PdfReader
from mlx_lm import load, generate

# Setup
MODEL_REPO = "mlx-community/gemma-3-4b-it-4bit"
print(f"Loading {MODEL_REPO}...")
model, tokenizer = load(MODEL_REPO)

ARXIV_ID = "1706.03762"
PDF_URL = f"https://arxiv.org/pdf/{ARXIV_ID}.pdf"
PDF_PATH = "backend/attention.pdf"

def download_and_extract():
    if not os.path.exists(PDF_PATH):
        print(f"Downloading {ARXIV_ID}...")
        response = requests.get(PDF_URL)
        with open(PDF_PATH, "wb") as f:
            f.write(response.content)
    
    print("Extracting text...")
    reader = PdfReader(PDF_PATH)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text[:25000] # Truncate for safety

# Using Gemma chat template manually
OLD_PROMPT_TEMPLATE = """<start_of_turn>user
You are an expert researcher.
Please provide a comprehensive yet concise summary of the following research paper. 
Focus on the problem being solved, the methodology, and the key results.

Text:
{text}
<end_of_turn>
<start_of_turn>model
"""

NEW_PROMPT_TEMPLATE = """<start_of_turn>user
You are an expert researcher.
Please provide a structured and detailed summary of the following research paper.
Format the response with the following clearly labeled sections:

1. **Core Problem**: What specific problem is this paper trying to solve?
2. **Key Innovation**: What is the main novelty or contribution (the "aha!" moment)?
3. **Methodology**: Briefly explain the technical approach.
4. **Key Results**: What were the quantitative or qualitative findings?

Text:
{text}
<end_of_turn>
<start_of_turn>model
"""

def generate_summary(text, prompt_template, filename):
    prompt = prompt_template.format(text=text)
    print(f"Generating summary for {filename}...")
    response = generate(
        model, 
        tokenizer, 
        prompt=prompt, 
        max_tokens=1024, 
        verbose=True
    )
    
    with open(f"backend/{filename}", "w") as f:
        f.write(response)

def run_compare():
    text = download_and_extract()
    
    generate_summary(text, OLD_PROMPT_TEMPLATE, "old_prompt.md")
    generate_summary(text, NEW_PROMPT_TEMPLATE, "new_prompt.md")
        
    print("Done! Check backend/old_prompt.md and backend/new_prompt.md")

if __name__ == "__main__":
    run_compare()
