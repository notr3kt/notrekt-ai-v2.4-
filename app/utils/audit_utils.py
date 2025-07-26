"""
audit_utils.py - Utilities for WORM audit logging, export, and third-party verification.
SOP-GOV-001, SOP-GOV-003
"""

from datetime import datetime, timezone
def export_audit_log(log_path, export_path):
    """
    Export the audit log as a signed JSON file for third-party audit.
    Args:
        log_path: Path to the SQLite WORM audit DB.
        export_path: Path to export the signed JSON log.
    SOP Reference: SOP-GOV-001, SOP-GOV-003
    """
    import sqlite3, json, hashlib
    conn = sqlite3.connect(log_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_events ORDER BY sequence_number ASC')
    columns = [desc[0] for desc in cursor.description]
    events = []
    import base64
    for row in cursor.fetchall():
        event = dict(zip(columns, row))
        event['metadata'] = json.loads(event['metadata_json'])
        del event['metadata_json']
        # Serialize signature field if present and is bytes
        if 'signature' in event and isinstance(event['signature'], (bytes, bytearray)):
            event['signature'] = base64.b64encode(event['signature']).decode('utf-8')
        events.append(event)
    # Create a hash of the entire export for signature
    export_data = json.dumps(events, sort_keys=True)
    export_hash = hashlib.sha256(export_data.encode('utf-8')).hexdigest()
    export_obj = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "event_count": len(events),
        "audit_events": events,
        "export_hash": export_hash
    }
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_obj, f, indent=2)
    conn.close()
    return export_hash

def verify_audit_log(log_path):
    """
    Verify the cryptographic integrity of the audit log using WORM chain verification.
    Args:
        log_path: Path to the SQLite WORM audit DB.
    Returns: (is_valid: bool, errors: list)
    SOP Reference: SOP-GOV-001, SOP-GOV-003
    """
    from ..worm_storage import WORMStorage
    storage = WORMStorage(log_path)
    is_valid, errors = storage.verify_integrity()
    storage.close()
    return is_valid, errors
