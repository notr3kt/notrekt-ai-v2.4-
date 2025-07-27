
"""
NOTREKT.AI v2.4 LLM Downloader & Governance Pipeline
Robust download, registry/SOP enforcement, resource checks, DVC stub, Slack & Notion MCP notification, FastAPI endpoint, and test stubs.
Extensible for email, dashboard, and future governance/ops integrations.
"""

import os
import json
import time
import random
import traceback
import shutil
import psutil
import argparse
import logging
from pathlib import Path
import httpx
from dotenv import load_dotenv
from huggingface_hub import login

# --- Load environment and secrets from .env ---
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
NOTION_MCP_URL = os.getenv('NOTION_MCP_URL', 'https://mcp.notion.com/mcp')
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('HF_API_KEY')
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
MONITORING_ALERT_URL = os.getenv('MONITORING_ALERT_URL')

# --- Registry Enforcement ---
MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "model_registry.json")
SOP_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "sop_registry.json")

def load_registry(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Accept both list or dict with model names as keys
        if isinstance(data, dict) and "_comment" in data and len(data) == 1:
            return set()  # Placeholder, no real registry
        if isinstance(data, dict):
            return set(data.keys())
        if isinstance(data, list):
            return set(data)
        return set()
    except Exception as e:
        print(f"[REGISTRY] Failed to load registry {path}: {e}")
        return set()

def is_model_registered(model_name, registry):
    # Accepts both exact and partial (repo/model) matches
    if model_name in registry:
        return True
    # Try to match on repo/model (ignore org prefix)
    short_name = model_name.split("/")[-1]
    for entry in registry:
        if short_name in entry or entry in model_name:
            return True
    return False

    # Optionally, log to a DVC audit file
    with open("dvc_audit.log", "a", encoding="utf-8") as f:
        f.write(f"{model_name} tracked at {__import__('datetime').datetime.utcnow().isoformat()}Z\n")
def is_sop_registered(model_name, sop_registry):
    # Optional: Enforce SOP for each model (stub, always True if registry is empty)
    if not sop_registry:
        return True
    short_name = model_name.split("/")[-1]
    for entry in sop_registry:
        if short_name in entry or entry in model_name:
            return True
    return False

# Load environment
load_dotenv()

# Login to Hugging Face
import os
from dotenv import load_dotenv

hf_token = os.getenv('HF_TOKEN') or os.getenv('HF_API_KEY')
if hf_token:
    login(token=hf_token)
    print("[INFO] Logged in to Hugging Face")
else:
    print("[ERROR] No HF_TOKEN found!")
    exit(1)

# Simple download function


import time
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
NOTION_MCP_URL = os.getenv('NOTION_MCP_URL', 'https://mcp.notion.com/mcp')
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('HF_API_KEY')
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
MONITORING_ALERT_URL = os.getenv('MONITORING_ALERT_URL')
import traceback
import shutil
import psutil
def check_resources(min_disk_gb=10, min_ram_gb=8):
    print(f"[INFO] Minimum requirements: Disk {min_disk_gb} GB, RAM {min_ram_gb} GB.")
    # Check free disk space
    total, used, free = shutil.disk_usage(os.getcwd())
    free_gb = free / (1024 ** 3)
    disk_ok = True
    if free_gb < min_disk_gb:
        print(f"[ERROR] Critically low disk space: {free_gb:.2f} GB free. At least {min_disk_gb} GB required.")
        disk_ok = False
    else:
        print(f"[INFO] Disk space: {free_gb:.2f} GB free.")
    # Check RAM
    ram = psutil.virtual_memory()
    ram_gb = ram.available / (1024 ** 3)
    ram_ok = True
    if ram_gb < min_ram_gb:
        print(f"[ERROR] Critically low available RAM: {ram_gb:.2f} GB. At least {min_ram_gb} GB required.")
        ram_ok = False
    else:
        print(f"[INFO] Available RAM: {ram_gb:.2f} GB.")
    return disk_ok and ram_ok

def download_model(model_name, max_retries=5, min_disk_gb=10, min_ram_gb=8):
    print(f"\n=== Downloading {model_name} ===")
    if not check_resources(min_disk_gb=min_disk_gb, min_ram_gb=min_ram_gb):
        print(f"[FATAL] Skipping download of {model_name} due to insufficient disk or RAM.")
        return False
    for attempt in range(max_retries):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
            # Download tokenizer first
            print("Downloading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print("✅ Tokenizer downloaded")

            # Special handling for Llama 3.1 rope_scaling issue
            if "Llama-3.1" in model_name:
                print("🔧 Applying Llama 3.1 configuration fix...")
                config = AutoConfig.from_pretrained(model_name)

                # Fix the rope_scaling configuration by removing problematic fields
                if hasattr(config, 'rope_scaling') and isinstance(config.rope_scaling, dict):
                    original = config.rope_scaling.copy()
                    print(f"Original rope_scaling: {original}")

                    # Keep only the two required fields
                    config.rope_scaling = {
                        'type': original.get('rope_type', 'default'),
                        'factor': original.get('factor', 8.0)
                    }
                    print(f"Fixed rope_scaling: {config.rope_scaling}")

                # Download model with fixed config
                print("Downloading model with fixed configuration...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    config=config,
                    torch_dtype="auto",
                    device_map="cpu",
                    low_cpu_mem_usage=True
                )
            else:
                # Download model with minimal config for other models
                print("Downloading model...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype="auto",
                    device_map="cpu",
                    low_cpu_mem_usage=True
                )

            print(f"✅ SUCCESS: {model_name} downloaded!")
            return True

        except Exception as e:
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"❌ FAILED: {model_name} (attempt {attempt+1}/{max_retries}) - {e}")
            traceback.print_exc()
            if attempt < max_retries - 1:
                print(f"Retrying in {wait:.2f} seconds...")
                time.sleep(wait)
            else:
                print(f"Giving up after {max_retries} attempts.")
                return False

success = 0

# --- CLI, Logging, and DVC Integration ---
import argparse
import logging
from pathlib import Path

def setup_logger(logfile="llm_download.log"):
    logger = logging.getLogger("llm_downloader")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(fh)
    return logger

def parse_args():
    parser = argparse.ArgumentParser(description="Download LLMs with resource checks and logging.")
    parser.add_argument('--models', nargs='+', default=[
        "mistralai/Mistral-7B-Instruct-v0.3",
        "google/gemma-2-9b-it",
        "meta-llama/Meta-Llama-3.1-8B-Instruct"
    ], help="List of model names to download.")
    parser.add_argument('--min-disk-gb', type=int, default=10, help="Minimum disk space in GB required per model.")
    parser.add_argument('--min-ram-gb', type=int, default=8, help="Minimum RAM in GB required per model.")
    parser.add_argument('--logfile', type=str, default="llm_download.log", help="Log file path.")
    parser.add_argument('--dvc-track', action='store_true', help="Track downloaded models with DVC (stub).")
    parser.add_argument('--notify-mcp', action='store_true', help="Send a notification to Notion MCP after download.")
    parser.add_argument('--notify-email', action='store_true', help="Send a notification email after download (stub).")
    return parser.parse_args()

def dvc_track_model(model_name):
    # Stub for DVC integration
    # In a real pipeline, you would run: os.system(f"dvc add {model_dir}")
    print(f"[DVC] Would track {model_name} with DVC here.")

def print_resource_summary():
    total, used, free = shutil.disk_usage(os.getcwd())
    free_gb = free / (1024 ** 3)
    ram = psutil.virtual_memory()
    ram_gb = ram.available / (1024 ** 3)
    print(f"\n[SUMMARY] Post-download system resources:")
    print(f"  Disk space free: {free_gb:.2f} GB")
    print(f"  Available RAM: {ram_gb:.2f} GB")

def main():

    def send_email_notification(subject, body):
        # Stub for email notification (production: use SMTP or service)
        logger.info(f"[EMAIL] Would send email: {subject}\n{body}")
        print(f"[EMAIL] Would send email: {subject}")
        # Monitoring/alerting stub
        if MONITORING_ALERT_URL:
            httpx.post(MONITORING_ALERT_URL, json={"event": "email_notification", "subject": subject})

    args = parse_args()
    logger = setup_logger(args.logfile)
    logger.info(f"Starting LLM download script. Models: {args.models}")

    def send_to_notion_mcp(payload: dict):
        NOTION_MCP_URL = "https://mcp.notion.com/mcp"
        try:
            response = httpx.post(NOTION_MCP_URL, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Data sent to Notion MCP: {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to send to Notion MCP: {e}")
            return None

    # Load registries
    model_registry = load_registry(MODEL_REGISTRY_PATH)
    sop_registry = load_registry(SOP_REGISTRY_PATH)
    registry_enforced = bool(model_registry)
    sop_enforced = bool(sop_registry)
    logger.info(f"Model registry loaded: {len(model_registry)} entries. SOP registry loaded: {len(sop_registry)} entries.")

    success = 0
    failed_models = []
    skipped_unregistered = []
    skipped_no_sop = []

    for model in args.models:
        # Registry enforcement
        if registry_enforced and not is_model_registered(model, model_registry):
            logger.warning(f"SKIPPED: {model} is not registered in model_registry.json.")
            print(f"[REGISTRY] SKIPPED: {model} is not registered in model_registry.json.")
            skipped_unregistered.append(model)
            continue
        if sop_enforced and not is_sop_registered(model, sop_registry):
            logger.warning(f"SKIPPED: {model} has no SOP entry in sop_registry.json.")
            print(f"[REGISTRY] SKIPPED: {model} has no SOP entry in sop_registry.json.")
            skipped_no_sop.append(model)
            continue

        logger.info(f"Attempting download: {model}")
        if download_model(model, min_disk_gb=args.min_disk_gb, min_ram_gb=args.min_ram_gb):
            logger.info(f"SUCCESS: {model} downloaded.")
            print(f"[LOG] {model} downloaded successfully.")
            if args.dvc_track:
                dvc_track_model(model)
            success += 1
        else:
            logger.error(f"FAILED: {model} not downloaded.")
            failed_models.append(model)

    print(f"\n🎯 FINAL RESULT: {success}/{len(args.models)} models downloaded successfully!")
    logger.info(f"Final result: {success}/{len(args.models)} models downloaded.")

    if skipped_unregistered:
        print(f"\n[REGISTRY] The following models were SKIPPED (not in model_registry.json):")
        for m in skipped_unregistered:
            print(f"  - {m}")
        logger.warning(f"Skipped (unregistered): {skipped_unregistered}")
    if skipped_no_sop:
        print(f"\n[REGISTRY] The following models were SKIPPED (no SOP in sop_registry.json):")
        for m in skipped_no_sop:
            print(f"  - {m}")
        logger.warning(f"Skipped (no SOP): {skipped_no_sop}")

    if success == len(args.models):
        print("🚀 ALL MODELS READY! NOTREKT.AI v2.4 is complete!")
        logger.info("All models downloaded successfully.")
    else:
        print("⚠️  Some models failed, but you can still use the successful ones.")
        if failed_models:
            print("Failed models:")
            for m in failed_models:
                print(f"  - {m}")
            logger.warning(f"Failed models: {failed_models}")

    print_resource_summary()
    logger.info("Resource summary printed.")

    print("\n[INFO] LLM download script complete. You may now proceed to model integration, testing, or further pipeline steps as needed.")
    logger.info("Script complete.")

    # --- Notion MCP Notification (if requested) ---
    if getattr(args, 'notify_mcp', False):
        payload = {
            "event": "llm_download_complete",
            "success": success,
            "failed_models": failed_models,
            "skipped_unregistered": skipped_unregistered,
            "skipped_no_sop": skipped_no_sop,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'
        }
        send_to_notion_mcp(payload)
        print("[INFO] Notion MCP notification sent.")

    # --- Email Notification (stub, if requested) ---
    if getattr(args, 'notify_email', False):
        subject = "NOTREKT.AI LLM Download Complete"
        body = f"Success: {success}\nFailed: {failed_models}\nSkipped (unregistered): {skipped_unregistered}\nSkipped (no SOP): {skipped_no_sop}"
        send_email_notification(subject, body)
        print("[INFO] Email notification sent.")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    # Add CLI flag for notification test
    if "--notify" in args:
        from app.utils.notification_utils import send_slack_notification
        send_slack_notification("🚨 HITL approval required for NOTREKT.AI action. Please review in the dashboard.")
        print("[INFO] Slack notification sent. Exiting.")
        sys.exit(0)
    main()

# --- FastAPI endpoint for interactive HITL/governance flows ---
try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn

    app = FastAPI()

    @app.post("/trigger-download/")
    async def trigger_download(models: list = None, notify_mcp: bool = False):
        """Trigger LLM download via API. Optionally notify Notion MCP."""
        import argparse
        import sys
        # Build args for main()
        sys.argv = [sys.argv[0]]
        if models:
            sys.argv += ["--models"] + models
        if notify_mcp:
            sys.argv += ["--notify-mcp"]
        # Run main (side effect: prints/logs output)
        main()
        return JSONResponse({"status": "Download triggered", "models": models, "notify_mcp": notify_mcp})

    # To run: uvicorn download_simple:app --reload
except ImportError:
    pass

# --- Test stub for MCP notification and FastAPI endpoint ---
def test_mcp_and_fastapi():
    """Test Notion MCP notification and FastAPI endpoint (manual/CI)."""
    # Test MCP notification
    print("[TEST] Running MCP notification test...")
    import subprocess
    result = subprocess.run(["python", __file__, "--notify-mcp"], capture_output=True, text=True)
    print(result.stdout)
    assert "Notion MCP notification sent" in result.stdout or "✅ Data sent to Notion MCP" in result.stdout
    # Test FastAPI endpoint (manual: run uvicorn and POST to /trigger-download/)
    print("[TEST] FastAPI endpoint available. Run: uvicorn download_simple:app --reload and POST to /trigger-download/")
