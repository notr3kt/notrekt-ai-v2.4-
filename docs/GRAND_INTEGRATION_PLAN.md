#### Local LLM Model Download & License Acceptance
- Before running locally, you must accept the license for each model on Hugging Face:
  - [google/gemma-7b-it](https://huggingface.co/google/gemma-7b-it)
  - [meta-llama/Meta-Llama-3-8B-Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
  - [mistralai/Mistral-7B-Instruct-v0.2](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2)
- Log in with your Hugging Face token (set `HF_TOKEN` in `.env`).
- The pipeline will automatically download and cache all required models for offline use.
# NOTREKT.AI v2.4 Grand Integration Plan

## Overview
This document details the systematic, actionable plan for upgrading NOTREKT.AI to v2.4, integrating robust open-source tools and best practices for a governed, auditable, and production-ready AI system. This plan merges all previous roadmaps and the best free/open-source tools for execution in VS Code.

---

## 1. Environment & Tooling Setup
- **VS Code Extensions:** Python, GitLens, DVC, Jupyter, Docker, REST Client, Markdown All in One.
- **Terminal Commands:**
  ```sh
  python -m venv venv
  .\venv\Scripts\activate
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install dvc gradio transformers sentence-transformers faiss-cpu google-generativeai pytest pytest-asyncio
  # (Optional) Docker for Airbyte/LocalAI
  ```

---

## 2. Data & Model Versioning (DVC)
- `dvc init`
- `dvc add trusted_knowledge_corpus/`
- `dvc add app/rag_index.faiss`
- Automate DVC in `_rebuild_index` (rag_system.py):
  ```python
  import subprocess
  subprocess.run(["dvc", "add", "trusted_knowledge_corpus/"])
  subprocess.run(["dvc", "add", "app/rag_index.faiss"])
  ```

---

## 3. RAG, LLM, and Verifier Integration
- Update `llm_provider.py` to support Gemini, Gemma-3-27b-it (Hugging Face/local), LocalAI.
- Update VerifierAgent for redundant checks (Gemini + Gemma).

---



## 4. Automated Data Ingestion (Airbyte, Google Drive, Optional)
- Run Airbyte via Docker Compose.
- Configure Google Drive → local markdown sync for trusted_knowledge_corpus.

### Google Drive Integration: Service Account and OAuth 2.0

#### Service Account (Automated RAG Ingestion)
- Use `google_drive_ingest.py` for server-to-server access to Google Drive.
- Grant the Service Account access to the specific Drive folder containing your "trusted knowledge corpus".
- Run: `python google_drive_ingest.py`

#### OAuth 2.0 (User-Specific Access)
- Use `google_drive_oauth_ingest.py` for user-driven flows (Desktop/Web OAuth).
- Place your OAuth client_secret JSON in the project directory.
- Run: `python google_drive_oauth_ingest.py` (browser consent required on first run)

#### Pipeline Integration
- Add either or both scripts to your ingestion pipeline as needed.
- Both scripts sync Google Drive files to `trusted_knowledge_corpus/`.

#### Testing
- Tests for both Service Account and OAuth ingestion are in `tests/test_google_drive_ingest.py`.
- Run: `pytest tests/test_google_drive_ingest.py`

**Tip:** Store your credential JSON files securely and never commit them to version control.

---

## 5. UI & API Integration
- Continue using FastAPI for backend endpoints.
- Prototype Gradio UI for `/action` endpoint and audit log viewer.

---

## 6. Testing & Audit
- Run all tests with `pytest`.
- Expand tests for LLMProvider, VerifierAgent, agent orchestration, and persistence.

---

## 7. Documentation & Governance
- Keep `docs/`, `AUDIT_LOG.md`, and SOPs up to date.
- Document every major change, especially LLM integration and audit logic.

---

## 8. (Optional) LocalAI for Full Local LLMs
- Run LocalAI via Docker.
- Update `llm_provider.py` to call LocalAI endpoint.

---

## 9. VS Code Workflow Tips
- Use the built-in terminal for all commands.
- Use the DVC extension for data/model versioning.
- Use the Python Test Explorer for running/debugging tests.
- Use GitLens for code/audit history.
- Use REST Client or Thunder Client for API testing.

---

## Summary Table
| Tool/Step         | Command/Action                                                                 |
|-------------------|-------------------------------------------------------------------------------|
| Python venv       | `python -m venv venv` + activate                                              |
| Install deps      | `pip install -r requirements.txt` + all above pip installs                    |
| DVC               | `dvc init`, `dvc add ...`                                                     |
| Gradio            | `pip install gradio`                                                          |
| Transformers      | `pip install transformers`                                                    |
| sentence-transformers | `pip install sentence-transformers faiss-cpu`                             |
| google-generativeai | `pip install google-generativeai`                                           |
| pytest            | `pip install pytest pytest-asyncio`                                           |
| Airbyte           | `docker compose up -d`                                                        |
| LocalAI           | `docker run -d -p 8080:8080 localai/localai:latest`                           |
| Run tests         | `pytest`                                                                      |
| Run FastAPI       | `uvicorn app.main:app --reload`                                               |
| Run Gradio demo   | `python gradio_demo.py`                                                       |

---

**Follow this plan step by step in VS Code. For any code, config, or test you need, ask Copilot for the exact implementation.**
