import sys
import os

def split_jsonl(input_path, chunk_size=1000):
    print(f"Splitting {input_path} into chunks of {chunk_size}...")
    base, ext = os.path.splitext(input_path)
    
    count = 0
    file_num = 1
    f_out = None
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                if count % chunk_size == 0:
                    if f_out:
                        f_out.close()
                    out_path = f"{base}_part{file_num}{ext}"
                    f_out = open(out_path, 'w', encoding='utf-8')
                    print(f"  Creating {out_path}...")
                    file_num += 1
                
                f_out.write(line)
                count += 1
        
        if f_out:
            f_out.close()
            
        print(f"✅ Successfully split into {file_num-1} parts. Total lines: {count}")
    except Exception as e:
        print(f"❌ Error splitting file: {e}")
        if f_out:
            f_out.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 split_jsonl.py input.jsonl [chunk_size]")
        sys.exit(1)
    
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    split_jsonl(sys.argv[1], chunk_size)
