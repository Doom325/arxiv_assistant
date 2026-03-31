
import os

INPUT_FILE = "gemini_summary.md"
OUTPUT_FILE = "gemini_summary_clean.md"

def clean_report():
    if not os.path.exists(INPUT_FILE):
        print(f"File {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r") as f:
        content = f.read()

    # Split by separator (assuming '---' is used)
    blocks = content.split("---")
    
    clean_blocks = []
    dropped_count = 0
    
    for block in blocks:
        if not block.strip():
            continue
            
        # Check for error keywords
        if "Error generating Gemini summary" in block:
            dropped_count += 1
            continue
            
        clean_blocks.append(block)
    
    # Write back
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n---\n".join(clean_blocks))
        # Add trailing separator
        f.write("\n---\n")

    print(f"Cleanup Complete.")
    print(f"Original Blocks: {len(blocks)}")
    print(f"Dropped Errors: {dropped_count}")
    print(f"Valid Summaries Kept: {len(clean_blocks)}")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    clean_report()
