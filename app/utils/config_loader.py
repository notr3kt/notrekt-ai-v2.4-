"""
config_loader.py - Loads environment variables and config files securely.
SOP-ARC-001
"""
import os
import json
from pathlib import Path

def load_env():
    from dotenv import load_dotenv
    load_dotenv()

def load_rules(path: str):
    with open(path, 'r') as f:
        return json.load(f)
