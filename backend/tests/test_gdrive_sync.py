import os
import sys
import logging

# Add the backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_dir)

from services.gdrive import GoogleDriveService, NeedAuthException

logging.basicConfig(level=logging.INFO)

def test_sync():
    try:
        gdrive = GoogleDriveService(
            credentials_path=os.path.join(backend_dir, "credentials.json"),
            token_path=os.path.join(backend_dir, "token.json")
        )
        
        folder_name = "Test Sync"
        folder_id = gdrive.get_or_create_folder(folder_name)
        print(f"Using folder: {folder_name} (ID: {folder_id})")
        
        # Create a dummy PDF
        test_file = "test_sync.pdf"
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<< /Title (Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
            
        print(f"Uploading {test_file} for the second time (should be skipped due to MD5)...")
        file_id2 = gdrive.upload_file(test_file, folder_id)
        print(f"Second upload ID: {file_id2}")
        
        if file_id1 == file_id2:
            print("SUCCESS: File ID is the same. Deduplication works for identical content.")
        else:
            print("FAILURE: File ID is different. A duplicate was created.")

        # Test content change
        print(f"Updating {test_file} with new content...")
        with open(test_file, "ab") as f:
            f.write(b"\n% Changed content")
        
        print(f"Uploading {test_file} after content change (should be updated)...")
        file_id3 = gdrive.upload_file(test_file, folder_id)
        print(f"Third upload ID: {file_id3}")

        if file_id1 == file_id3:
            print("SUCCESS: File ID is the same after update. The file was updated correctly.")
        else:
            print("FAILURE: File ID changed after update.")
            
        # Cleanup dummy file
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except NeedAuthException as e:
        print(f"Authentication needed: {e.auth_url}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_sync()
