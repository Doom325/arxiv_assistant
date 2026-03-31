from google.cloud import storage

def debug_metadata():
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket("arxiv-dataset")
    blob = bucket.blob("metadata-v5/arxiv-metadata-oai.json")
    
    print("Reading first 5 lines of metadata...")
    with blob.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            import json
            data = json.loads(line)
            print(f"Line {i}: ID={data.get('id')}, Cats={data.get('categories')}, Date={data.get('update_date')}")

if __name__ == "__main__":
    debug_metadata()
