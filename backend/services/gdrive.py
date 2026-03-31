import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging
import hashlib

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

class NeedAuthException(Exception):
    def __init__(self, auth_url, code_verifier=None):
        self.auth_url = auth_url
        self.code_verifier = code_verifier

class GoogleDriveService:
    def __init__(self, credentials_path="credentials.json", token_path = "token.json", catch_auth=True):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None
        if catch_auth:
            self.authenticate()

    def authenticate(self):
        """Authenticates the user and returns the Drive service."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # If there are no (valid) credentials available, we need to auth.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    # Save refreshed credentials
                    with open(self.token_path, "w") as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    logging.error(f"Failed to refresh token: {e}")
                    self.creds = None # Trigger re-auth
            
            if not self.creds:
                if not os.path.exists(self.credentials_path):
                    logging.error(f"Credentials file not found at {self.credentials_path}")
                    raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}")
                
                flow = Flow.from_client_secrets_file(
                    self.credentials_path,
                    scopes=SCOPES,
                    redirect_uri="http://localhost:8085"
                )
                auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                raise NeedAuthException(auth_url, flow.code_verifier)

        try:
            self.service = build("drive", "v3", credentials=self.creds)
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            raise error

    def finish_auth(self, code, code_verifier=None):
        """Exchange the auth code for a token and initialize service."""
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=SCOPES,
            redirect_uri="http://localhost:8085"
        )
        flow.fetch_token(code=code, code_verifier=code_verifier)
        self.creds = flow.credentials
        with open(self.token_path, "w") as token:
            token.write(self.creds.to_json())
        self.service = build("drive", "v3", credentials=self.creds)
        return True

    def get_or_create_folder(self, folder_name):
        """Finds or creates a folder with the given name."""
        if not self.service:
            raise Exception("Service not initialized. Call authenticate() or finish_auth() first.")
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])

            if items:
                return items[0]['id']
            else:
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                return file.get('id')
        except HttpError as error:
            logging.error(f"An error occurred while getting/creating folder: {error}")
            return None

    def find_file_in_folder(self, file_name, folder_id=None):
        """Finds a file with the given name in a specific folder.
        
        Returns a tuple (file_id, md5_checksum) or (None, None)
        """
        if not self.service:
            raise Exception("Service not initialized. Call authenticate() or finish_auth() first.")
        try:
            query = f"name = '{file_name}' and trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name, md5Checksum)').execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id'], items[0].get('md5Checksum')
            return None, None
        except HttpError as error:
            logging.error(f"An error occurred while searching for file: {error}")
            return None, None

    def _calculate_md5(self, file_path):
        """Calculates the MD5 hash of a local file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def upload_file(self, file_path, folder_id=None):
        """Uploads a file to the specified folder, or updates it if it already exists."""
        if not self.service:
            raise Exception("Service not initialized. Call authenticate() or finish_auth() first.")
        try:
            file_name = os.path.basename(file_path)
            
            # Check if file already exists
            existing_file_id, drive_md5 = self.find_file_in_folder(file_name, folder_id)
            
            # Calculate local MD5
            local_md5 = self._calculate_md5(file_path)
            
            if drive_md5 == local_md5:
                logging.info(f"Skipping upload for {file_name}, content is identical (MD5: {local_md5})")
                return existing_file_id

            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
            
            if existing_file_id:
                # Update existing file
                logging.info(f"File {file_name} exists but content differs (Drive MD5: {drive_md5}, Local MD5: {local_md5}). Updating...")
                file = self.service.files().update(fileId=existing_file_id, media_body=media, fields='id').execute()
                return file.get('id')
            else:
                # Create new file
                file_metadata = {'name': file_name}
                if folder_id:
                    file_metadata['parents'] = [folder_id]
                
                file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                return file.get('id')
        except HttpError as error:
            logging.error(f"An error occurred while uploading/updating file: {error}")
            return None
