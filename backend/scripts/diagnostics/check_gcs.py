from google.cloud import storage

def check_gcs():
    try:
        print("Attempting to access gs://arxiv-dataset anonymously...")
        client = storage.Client.create_anonymous_client()
        bucket = client.bucket("arxiv-dataset")
        blobs = bucket.list_blobs(prefix="metadata", max_results=10)
        
        print("Success! Found blobs:")
        for blob in blobs:
            print(f"- {blob.name}")
            
    except Exception as e:
        print(f"Error accessing GCS: {e}")

if __name__ == "__main__":
    check_gcs()
