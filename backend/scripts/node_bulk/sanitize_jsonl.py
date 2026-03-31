import sys
import json
import re

def sanitize_jsonl(input_path, output_path):
    print(f"Aggressively Sanitizing {input_path} -> {output_path}...")
    count = 0
    errors = 0
    
    # Regex to find unpaired surrogates in a string
    # This matches \uD800-\uDBFF not followed by \uDC00-\uDFFF, 
    # or \uDC00-\uDFFF not preceded by \uD800-\uDBFF.
    # However, Python's re doesn't support this easily for encoded strings.
    # Better approach: use json.loads and then a custom string cleaner.

    def clean_string(obj):
        if isinstance(obj, str):
            # Encode and decode with 'ignore' to drop invalid surrogates
            return obj.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
        if isinstance(obj, list):
            return [clean_string(i) for i in obj]
        if isinstance(obj, dict):
            return {k: clean_string(v) for k, v in obj.items()}
        return obj

    with open(input_path, 'r', encoding='utf-8', errors='replace') as f_in:
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                count += 1
                try:
                    data = json.loads(line)
                    clean_data = clean_string(data)
                    f_out.write(json.dumps(clean_data, ensure_ascii=False) + '\n')
                except Exception as e:
                    errors += 1
                    if errors < 5:
                        print(f"Line {count} error: {e}")
                    continue
    
    print(f"✅ Finished. Total lines: {count}, Errors skipped: {errors}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sanitize.py input.jsonl output.jsonl")
        sys.exit(1)
    sanitize_jsonl(sys.argv[1], sys.argv[2])
