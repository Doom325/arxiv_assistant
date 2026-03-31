
import re
from pypdf import PdfReader

def extract_sections(pdf_path):
    print(f"Processing {pdf_path}...")
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Normalize whitespace
    # Replace multiple spaces with single space, keep newlines for structure initially?
    # Actually, pypdf extraction can be messy. Let's try to match headers.
    
    # Flexible regex for headers
    # Case insensitive, optional numbering (1. Introduction), optional bold markers (if any text residue)
    # This is a naive first pass.
    
    # Strategy: Find "Abstract" and "Introduction" positions.
    # Abstract is usually near the top.
    # Introduction usually follows Abstract.
    
    lower_text = full_text.lower()
    
    abstract_start = lower_text.find("abstract")
    intro_start = lower_text.find("introduction")
    
    if abstract_start == -1:
        print("Abstract not found.")
        abstract_text = ""
    else:
        # End of abstract is usually start of Introduction OR the start of the first section
        # We assume Intro follows Abstract.
        if intro_start != -1:
            abstract_end = intro_start
        else:
            # Fallback: look for "1. Introduction" or similar
            # Or just take first 2000 chars after abstract?
            abstract_end = abstract_start + 2000
        
        abstract_text = full_text[abstract_start:abstract_end].strip()
        # Clean up the word "Abstract" itself from the start
        abstract_text = re.sub(r'^abstract[:.]?\s*', '', abstract_text, flags=re.IGNORECASE)

    if intro_start == -1:
         print("Introduction not found.")
         intro_text = ""
    else:
        # Introduction ends at the next section "2. " or "Related Work"
        # Common next sections: "Related Work", "Background", "Method", "Model"
        
        # Regex to find next section header: Number + Word starting with Capital
        # e.g. "2. Related Work"
        # or "\nRelated Work" (less reliable)
        
        # Limit search to next 5k chars to avoid scanning whole doc
        intro_region = full_text[intro_start:]
        
        # Look for "2. " or "II. "
        # Or look for known next section titles
        next_section_pattern = r'\n\s*(2\.|II\.|Related Work|Background|Method)'
        match = re.search(next_section_pattern, intro_region, re.IGNORECASE)
        
        if match:
            intro_end = match.start()
            intro_text = intro_region[:intro_end].strip()
        else:
            # Fallback: take next 3000 chars
            intro_text = intro_region[:3000].strip()

        # Clean "Introduction" header
        intro_text = re.sub(r'^\d*\.?\s*introduction[:.]?\s*', '', intro_text, flags=re.IGNORECASE)

    return {
        "abstract": abstract_text[:1000] + "..." if len(abstract_text)>1000 else abstract_text,
        "introduction": intro_text[:1000] + "..." if len(intro_text)>1000 else intro_text
    }

if __name__ == "__main__":
    result = extract_sections("backend/sample.pdf")
    print("--- ABSTRACT ---")
    print(result["abstract"])
    print("\n--- INTRODUCTION ---")
    print(result["introduction"])
