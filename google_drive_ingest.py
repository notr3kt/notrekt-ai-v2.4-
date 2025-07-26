"""
google_drive_ingest.py - Automated Google Drive → local sync for NOTREKT.AI RAG ingestion

Usage:
1. Place your Service Account JSON key in a secure location (never commit to git).
2. Set the following environment variables or edit the config below:
   - GOOGLE_SERVICE_ACCOUNT_FILE: Path to your service account JSON
   - GOOGLE_DRIVE_FOLDER_ID: The folder ID to sync from
   - LOCAL_CORPUS_DIR: Local directory to sync files into (default: trusted_knowledge_corpus/)
3. Run: python google_drive_ingest.py

This script will download all files from the specified Google Drive folder into your local corpus directory, skipping files that are unchanged.
"""

import os
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- Load .env if present ---
load_dotenv()


# --- Config ---
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'your-folder-id')
LOCAL_CORPUS_DIR = os.getenv('LOCAL_CORPUS_DIR', 'trusted_knowledge_corpus')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("google_drive_ingest")


# --- Auth ---
try:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
except Exception as e:
    logger.error(f"Failed to authenticate with Google Service Account: {e}")
    raise SystemExit(1)

# --- Ensure local directory exists ---
Path(LOCAL_CORPUS_DIR).mkdir(parents=True, exist_ok=True)

def list_files_in_folder(folder_id):
    files = []
    page_token = None
    while True:
        try:
            response = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
                pageToken=page_token
            ).execute()
        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_id}: {e}")
            break
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
    try:
        while not done:
            status, done = downloader.next_chunk()
    except Exception as e:
        logger.error(f"Failed to download {file_name}: {e}")
        return False
    out_path = Path(dest_dir) / file_name
    try:
        with open(out_path, 'wb') as f:
            f.write(fh.getvalue())
        logger.info(f"Downloaded: {file_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to write file {file_name}: {e}")
        return False

def parse_gdrive_time(timestr):
    # Google Drive returns RFC3339 UTC "2023-07-27T12:34:56.789Z"
    try:
        return datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def sync_drive_folder(folder_id, dest_dir):
    files = list_files_in_folder(folder_id)
    logger.info(f"Found {len(files)} files in Google Drive folder.")
    for file in files:
        local_path = Path(dest_dir) / file['name']
        gdrive_mtime = parse_gdrive_time(file['modifiedTime'])
        # Download if not present or remote is newer
        if not local_path.exists() or (
            gdrive_mtime > datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
        ):
            logger.info(f"Syncing: {file['name']}")
            download_file(file['id'], file['name'], dest_dir)
        else:
            logger.info(f"Up-to-date: {file['name']}")

if __name__ == "__main__":
    logger.info("Starting Google Drive → local sync...")
    sync_drive_folder(DRIVE_FOLDER_ID, LOCAL_CORPUS_DIR)
    logger.info("Sync complete.")
