
import os
import json
import logging
import sys

# Configure Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("BenchmarkPrepHost")

def prepare_benchmark_host(data_dir):
    pdf_list_path = os.path.join(data_dir, "pdf_list.txt")
    output_path = os.path.join(data_dir, "benchmark_queue.json")
    
    if not os.path.exists(pdf_list_path):
        logger.error(f"List not found: {pdf_list_path}")
        return

    logger.info(f"Reading from {pdf_list_path}...")
    
    files = []
    with open(pdf_list_path, 'r') as f:
        for line in f:
            path = line.strip()
            if not path: continue
            
            # Skip ghost files just in case
            if "/._" in path: continue
            
            # The path in pdf_list.txt currently has '/app/data/' prefix (from previous sed command) 
            # e.g. /app/data/2201.00006.pdf
            # We need to CONVERT this to host path to verify size
            # /app/data -> data_dir
            
            # Remove /app/data if present
            if path.startswith("/app/data"):
                 rel_path = path.replace("/app/data/", "").replace("/app/data", "")
                 host_path = os.path.join(data_dir, rel_path)
            else:
                 # Assume it's already relative or absolute??
                 host_path = os.path.join(data_dir, os.path.basename(path))

            # The Container Path we want in JSON is exactly what is in the text file
            container_path = path 
            
            try:
                name = os.path.basename(host_path)
                size = os.path.getsize(host_path)
                files.append({"path": container_path, "size": size, "name": name}) 
            except OSError:
                pass
                
    if not files:
        logger.error("No valid files found.")
        return

    logger.info(f"Found {len(files)} valid PDFs. Sorting...")
    files.sort(key=lambda x: x['size'])
    
    total_files = len(files)
    if total_files == 0: return

    # Decile Logic
    chunks = []
    logger.info(f"Total: {total_files}")
    
    # Simple deciles
    decile_size = max(1, total_files // 10)
    
    for i in range(10):
        start_idx = i * decile_size
        end_idx = (i + 1) * decile_size if i < 9 else total_files
        
        chunk_files = files[start_idx:end_idx]
        if not chunk_files: continue
        
        # Sample 10
        sample_size = 10
        if len(chunk_files) <= sample_size:
            samples = chunk_files
        else:
            step = len(chunk_files) / sample_size
            indices = [int(j * step) for j in range(sample_size)]
            samples = [chunk_files[idx] for idx in indices]
            
        chunk_data = {
            "decile": i + 1,
            "range_start": start_idx,
            "range_end": end_idx,
            "min_size": chunk_files[0]['size'],
            "max_size": chunk_files[-1]['size'],
            "samples": [f['name'].replace('.pdf', '') for f in samples]
        }
        chunks.append(chunk_data)
        logger.info(f"Decile {i+1}: {len(samples)} samples")

    with open(output_path, "w") as f:
        json.dump(chunks, f, indent=2)
        
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 prepare_benchmark_host.py <HOST_DATA_DIR>")
        sys.exit(1)
    prepare_benchmark_host(sys.argv[1])
