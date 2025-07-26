import os
import shutil
import tempfile
import pytest

# Test for Service Account ingestion
@pytest.mark.skipif(
    not os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') or not os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
    reason="Service Account or Drive Folder ID not set"
)
def test_google_drive_ingest_service_account():
    from google_drive_ingest import sync_drive_folder
    temp_dir = tempfile.mkdtemp()
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    try:
        sync_drive_folder(folder_id, temp_dir)
        assert os.listdir(temp_dir), "No files downloaded from Google Drive (Service Account)"
    finally:
        shutil.rmtree(temp_dir)

# Test for OAuth ingestion
@pytest.mark.skipif(
    not os.getenv('GOOGLE_OAUTH_CLIENT_SECRET_FILE') or not os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
    reason="OAuth client secret or Drive Folder ID not set"
)
def test_google_drive_ingest_oauth(monkeypatch):
    import pickle
    from google_drive_oauth_ingest import sync_drive_folder, TOKEN_PICKLE
    temp_dir = tempfile.mkdtemp()
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    # Remove token.pickle to force fresh OAuth if needed
    if os.path.exists(TOKEN_PICKLE):
        os.remove(TOKEN_PICKLE)
    try:
        # Monkeypatch input to auto-accept browser consent if needed
        monkeypatch.setattr('builtins.input', lambda _: '\n')
        sync_drive_folder(folder_id, temp_dir)
        assert os.listdir(temp_dir), "No files downloaded from Google Drive (OAuth)"
    finally:
        shutil.rmtree(temp_dir)
        if os.path.exists(TOKEN_PICKLE):
            os.remove(TOKEN_PICKLE)
