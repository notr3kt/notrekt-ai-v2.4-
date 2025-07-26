# 3. Download and cache all local LLMs (Gemma, Llama, Mistral)
if [ -f "download_local_llms.py" ]; then
  python download_local_llms.py
fi
#!/bin/bash
# run_full_pipeline.sh - Full NOTREKT.AI v2.4 integration pipeline
# Usage: bash run_full_pipeline.sh

# 1. Activate Python venv
source venv/Scripts/activate

# 2. Install/upgrade dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install dvc gradio transformers sentence-transformers faiss-cpu google-generativeai pytest pytest-asyncio google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

# 3. DVC setup
if [ ! -d ".dvc" ]; then
  dvc init
fi
dvc add trusted_knowledge_corpus/
dvc add app/rag_index.faiss

# 4. Google Drive ingestion (Service Account)
if [ -f "google_drive_ingest.py" ]; then
  python google_drive_ingest.py
fi
if [ -f "google_drive_oauth_ingest.py" ]; then
  python google_drive_oauth_ingest.py
fi

# 5. (Optional) Airbyte via Docker Compose
# docker compose up -d

# 6. Run all tests
pytest

# 7. Run FastAPI backend
# uvicorn app.main:app --reload

# 8. Run Gradio demo
# python gradio_demo.py

echo "Full NOTREKT.AI v2.4 pipeline complete."
