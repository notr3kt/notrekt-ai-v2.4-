"""
crypto_utils.py - Cryptographic utilities for WORM logging and chain verification.
SOP-GOV-001
"""
import hashlib

def hash_entry(entry: str) -> str:
    return hashlib.sha256(entry.encode('utf-8')).hexdigest()

# [GAP: Add digital signature, anchoring, and verification methods]
