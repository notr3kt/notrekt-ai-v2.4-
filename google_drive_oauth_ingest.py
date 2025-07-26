"""
google_drive_oauth_ingest.py - User OAuth 2.0 Google Drive → local sync for NOTREKT.AI (Desktop/Web)

Usage:
1. Place your OAuth client_secret JSON (Desktop or Web) in the project directory.
2. Set the following environment variables or edit the config below:
   - GOOGLE_OAUTH_CLIENT_SECRET_FILE: Path to your OAuth client_secret.json
   - GOOGLE_DRIVE_FOLDER_ID: The folder ID to sync from (user must have access)
   - LOCAL_CORPUS_DIR: Local directory to sync files into (default: trusted_knowledge_corpus/)
3. Run: python google_drive_oauth_ingest.py
   - The first run will open a browser for user consent. Token is cached for reuse.

This script will download all files from the specified Google Drive folder into your local corpus directory, using the user's credentials.
"""
import os
from pathlib import Path
import io
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
import pickle

# --- Config ---
CLIENT_SECRET_FILE = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET_FILE', 'client_secret.json')
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'your-folder-id')
LOCAL_CORPUS_DIR = os.getenv('LOCAL_CORPUS_DIR', 'trusted_knowledge_corpus')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_PICKLE = 'token.pickle'

# --- Auth (OAuth 2.0) ---
creds = None
if os.path.exists(TOKEN_PICKLE):
    with open(TOKEN_PICKLE, 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(TOKEN_PICKLE, 'wb') as token:
        pickle.dump(creds, token)
drive_service = build('drive', 'v3', credentials=creds)

# --- Ensure local directory exists ---
Path(LOCAL_CORPUS_DIR).mkdir(parents=True, exist_ok=True)

def list_files_in_folder(folder_id):
    files = []
    page_token = None
    while True:
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
            pageToken=page_token
        ).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files

def download_file(file_id, file_name, dest_dir):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    out_path = Path(dest_dir) / file_name
    with open(out_path, 'wb') as f:
        f.write(fh.getvalue())
    print(f"Downloaded: {file_name}")

def sync_drive_folder(folder_id, dest_dir):
    files = list_files_in_folder(folder_id)
    print(f"Found {len(files)} files in Google Drive folder.")
    for file in files:
        local_path = Path(dest_dir) / file['name']
        # Download if not present or modified
        if not local_path.exists() or True:  # (Optionally: check modifiedTime for smarter sync)
            download_file(file['id'], file['name'], dest_dir)
        else:
            print(f"Up-to-date: {file['name']}")

if __name__ == "__main__":
    sync_drive_folder(DRIVE_FOLDER_ID, LOCAL_CORPUS_DIR)
    print("Sync complete.")
