
import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.gdrive import GoogleDriveService
from routers.integrations import run_gdrive_export
from models import Paper, UserLibrary

class TestDeduplicationLogic(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.gdrive = MagicMock()
        
    @patch("routers.integrations.GoogleDriveService")
    @patch("routers.integrations._download_pdf_for_export")
    def test_run_gdrive_export_skips_if_db_marked(self, mock_download, mock_gdrive_class):
        # Setup
        mock_gdrive_class.return_value = self.gdrive
        self.gdrive.get_or_create_folder.return_value = "folder_id"
        
        # Mock paper that IS already in drive
        paper = Paper(id=1, arxiv_id="1234.5678", in_drive_details={"Bookmarks": True})
        bookmark = UserLibrary(paper_id=1, list_name="Bookmarks")
        
        self.db.query().filter().filter().all.return_value = [bookmark]
        self.db.query().filter().first.return_value = paper
        
        # Execute
        run_gdrive_export("Bookmarks", "Bookmarks", self.db)
        
        # Verify: download_pdf should NOT be called
        mock_download.assert_not_called()
        self.gdrive.upload_file.assert_not_called()

    @patch("routers.integrations.GoogleDriveService")
    @patch("routers.integrations._download_pdf_for_export")
    def test_run_gdrive_export_syncs_if_not_in_db(self, mock_download, mock_gdrive_class):
        # Setup
        mock_gdrive_class.return_value = self.gdrive
        self.gdrive.get_or_create_folder.return_value = "folder_id"
        mock_download.return_value = "/tmp/test.pdf"
        self.gdrive.upload_file.return_value = "file_id_on_drive"
        
        # Mock paper that is NOT in drive
        paper = Paper(id=2, arxiv_id="8765.4321", in_drive_details={})
        bookmark = UserLibrary(paper_id=2, list_name="Bookmarks")
        
        self.db.query().filter().filter().all.return_value = [bookmark]
        self.db.query().filter().first.return_value = paper
        
        # Execute
        run_gdrive_export("Bookmarks", "Bookmarks", self.db)
        
        # Verify: download and upload SHOULD be called
        mock_download.assert_called_once()
        self.gdrive.upload_file.assert_called_once()
        
        # Verify status update in DB
        self.assertTrue(paper.in_drive_details["Bookmarks"])
        self.db.commit.assert_called()

    @patch("services.gdrive.hashlib.md5")
    @patch("services.gdrive.MediaFileUpload")
    def test_gdrive_service_md5_deduplication(self, mock_media, mock_md5):
        # Setup
        service = GoogleDriveService(catch_auth=False)
        service.service = MagicMock()
        
        # Mock local MD5
        mock_md5_instance = MagicMock()
        mock_md5.return_value = mock_md5_instance
        mock_md5_instance.hexdigest.return_value = "target_hash"
        
        # Mock finding existing file with SAME MD5
        with patch.object(service, "find_file_in_folder", return_value=("existing_id", "target_hash")):
            # Mock file reading
            m = mock_open(read_data=b"content")
            with patch("builtins.open", m):
                # Execute
                result = service.upload_file("/path/to/local.pdf", "folder_id")
                
                # Verify: skip update
                service.service.files().update.assert_not_called()
                self.assertEqual(result, "existing_id")

        # Mock finding existing file with DIFFERENT MD5
        service.service.reset_mock()
        with patch.object(service, "find_file_in_folder", return_value=("existing_id", "different_hash")):
            m = mock_open(read_data=b"content")
            with patch("builtins.open", m):
                # Execute
                service.upload_file("/path/to/local.pdf", "folder_id")
                
                # Verify: update SHOULD be called
                service.service.files().update.assert_called_once()

if __name__ == "__main__":
    unittest.main()
