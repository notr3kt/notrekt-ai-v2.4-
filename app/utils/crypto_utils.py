"""
crypto_utils.py - Cryptographic utilities for WORM logging and chain verification.
SOP-GOV-001
"""
import hashlib

def hash_entry(entry: str) -> str:
    return hashlib.sha256(entry.encode('utf-8')).hexdigest()


# --- Digital signature, anchoring, and verification methods ---
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.backends import default_backend
import os

def generate_rsa_keypair(private_key_path="private_key.pem", public_key_path="public_key.pem"):
    """Generate and save RSA keypair for digital signatures."""
    if os.path.exists(private_key_path) and os.path.exists(public_key_path):
        return
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    with open(private_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    public_key = private_key.public_key()
    with open(public_key_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def sign_data(data: str, private_key_path="private_key.pem") -> bytes:
    """Sign data with private key."""
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
    signature = private_key.sign(
        data.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(data: str, signature: bytes, public_key_path="public_key.pem") -> bool:
    """Verify digital signature with public key."""
    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
    try:
        public_key.verify(
            signature,
            data.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def anchor_audit_log(export_hash: str, anchor_file="audit_anchor.log"):
    """Anchor the audit log hash externally (append to anchor file)."""
    with open(anchor_file, "a", encoding="utf-8") as f:
        f.write(export_hash + "\n")

def verify_audit_anchor(export_hash: str, anchor_file="audit_anchor.log") -> bool:
    """Verify if the export_hash is anchored."""
    if not os.path.exists(anchor_file):
        return False
    with open(anchor_file, "r", encoding="utf-8") as f:
        anchors = f.read().splitlines()
    return export_hash in anchors
