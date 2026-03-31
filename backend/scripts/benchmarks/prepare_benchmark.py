import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import os
import json
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BenchmarkPrep")

# Path to PDFs
PDF_DIR = settings.PDF_SAVE_DIR or "/Volumes/External/PDFs/Arxiv Assistant"

def prepare_benchmark():
    if not os.path.exists(PDF_DIR):
        logger.error(f"PDF Directory not found: {PDF_DIR}")
        return

    logger.info(f"Scanning {PDF_DIR} for PDFs...")
    
    # 1. Get all PDF files and sizes
    files = []
    
    # OPTIMIZATION: Try to read from pre-generated list to avoid high IO scan
    # Run: find "$PDF_DIR" -path "*/postgres*" -prune -o -name "*.pdf" -print > pdf_list.txt
    list_path = "/app/data/pdf_list.txt" 
    if os.path.exists(list_path):
        logger.info(f"Loading files from {list_path}...")
        with open(list_path, 'r') as f:
            for line in f:
                path = line.strip()
                if not path: continue
                # We need size. Checking stat might still be slow but let's try.
                # If stat is too slow, we can skip size sorting or estimate.
                # Let's try to stat, but if it fails, skip.
                try:
                    name = os.path.basename(path)
                    size = os.path.getsize(path)
                    files.append({"path": path, "size": size, "name": name})
                except OSError:
                    pass
    else:
        logger.info(f"Scanning {PDF_DIR} for PDFs (Fallback to os.walk)...")
        # Use os.walk so we can skip directories
        for root, dirs, filenames in os.walk(PDF_DIR):
            # SKIP postgres and hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'postgres']
            
            for name in filenames:
                if name.endswith(".pdf") and not name.startswith("._"):
                    full_path = os.path.join(root, name)
                    try:
                        stat = os.stat(full_path)
                        files.append({"path": full_path, "size": stat.st_size, "name": name})
                    except OSError:
                        pass
    
    if not files:
        logger.error("No PDFs found.")
        return

    logger.info(f"Found {len(files)} PDFs. Sorting...")
    
    # 2. Sort by size
    files.sort(key=lambda x: x['size'])
    
    # 3. Create Deciles
    total_files = len(files)
    decile_size = total_files // 10
    
    chunks = []
    
    logger.info(f"Total Files: {total_files}. Decile Size: ~{decile_size}")
    
    for i in range(10):
        start_idx = i * decile_size
        end_idx = (i + 1) * decile_size if i < 9 else total_files
        
        decile_files = files[start_idx:end_idx]
        
        # Pick 10 files evenly distributed
        # If decile has < 10 files, take all
        # Indices: 0, 10%, 20%... 90% of the chunk
        
        sample_size = 10
        if len(decile_files) <= sample_size:
             samples = decile_files
        else:
             step = len(decile_files) / sample_size
             indices = [int(j * step) for j in range(sample_size)]
             samples = [decile_files[idx] for idx in indices]
             
        chunk_data = {
            "decile": i + 1,
            "range_start": start_idx,
            "range_end": end_idx,
            "min_size": decile_files[0]['size'],
            "max_size": decile_files[-1]['size'],
            "samples": [f['name'].replace('.pdf', '') for f in samples] # arxvid
        }
        chunks.append(chunk_data)
        logger.info(f"Decile {i+1}: {len(samples)} samples ({chunk_data['min_size']} - {chunk_data['max_size']} bytes)")

    # 4. Save to JSON
    output_path = "benchmark_queue.json"
    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
        
    logger.info(f"Benchmark queue saved to {output_path}")

if __name__ == "__main__":
    prepare_benchmark()
