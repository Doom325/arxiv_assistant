import requests

def test_pdf_url():
    # Example recent paper: 2301.00001
    arxiv_id = "2301.00001"
    yymm = "2301"
    url = f"https://storage.googleapis.com/arxiv-dataset/arxiv/pdf/{yymm}/{arxiv_id}v1.pdf"
    
    print(f"Testing URL: {url}")
    try:
        response = requests.head(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success! PDF is accessible.")
        else:
            print("Failed to access PDF.")
            # Try alternate structure?
            # Maybe gs://arxiv-dataset/arxiv/pdf/2301/2301.00001v1.pdf?
            # The metadata usually has versions.
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pdf_url()
