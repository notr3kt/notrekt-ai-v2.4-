#!/usr/bin/env python3
"""
NOTREKT.AI v2.0 - WORM Storage System
Write-Once-Read-Many compliant storage with cryptographic integrity.
"""

import sqlite3
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .config_manager import Config, logger

@dataclass
class AuditEvent:
    """Immutable audit event structure for WORM storage."""
    timestamp: str
    event_id: str
    sequence_number: int
    action_name: str
    status: str  # SUCCESS, BREACH, DENIED, APPROVED, PENDING
    metadata: Dict[str, Any]
    risk_tier: str
    requires_approval: bool
    human_decision: Optional[str]
    sop_reference: str
    primary_hash: str
    chain_hash: str
    tamper_seal: str

class CryptoManager:
    """Handles all cryptographic operations for tamper-proof logging."""
    
    @staticmethod
    def generate_sha256(data: str) -> str:
        """Generate SHA-256 hash."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID v4."""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_chain_hash(current_event: str, previous_hash: str) -> str:
        """Create blockchain-style chain hash."""
        combined = f"{previous_hash}{current_event}"
        return CryptoManager.generate_sha256(combined)
    
    @staticmethod
    def create_tamper_seal(event_data: str, system_secret: str) -> str:
        """Create tamper-proof seal using system secret."""
        combined = f"{event_data}{system_secret}"
        return CryptoManager.generate_sha256(combined)

class WORMStorage:
    """
    Write-Once-Read-Many compliant storage using SQLite with cryptographic chaining.
    Provides true immutability and tamper detection for audit logs.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.WORM_DB_PATH
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_database()
        
        logger.info(f"WORM Storage initialized: {self.db_path}")
        
    def _initialize_database(self):
        """Initialize the WORM database with proper constraints."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_id TEXT UNIQUE NOT NULL,
                action_name TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                risk_tier TEXT NOT NULL,
                requires_approval BOOLEAN NOT NULL,
                human_decision TEXT,
                sop_reference TEXT NOT NULL,
                primary_hash TEXT,
                chain_hash TEXT,
                tamper_seal TEXT,
                signature BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create indexes for performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_event_id ON audit_events(event_id)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON audit_events(status)
        ''')
        # Create the genesis block if this is a new database
        self.cursor.execute('SELECT COUNT(*) FROM audit_events')
        count = self.cursor.fetchone()[0]
        if count == 0:
            self._create_genesis_block()
        self.conn.commit()
    
    def _create_genesis_block(self):
        """Create the initial genesis block for the audit chain."""
        genesis_event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_id=CryptoManager.generate_uuid(),
            sequence_number=0,
            action_name="SYSTEM_INIT",
            status="SUCCESS",
            metadata={"initialization": "NOTREKT.AI v2.0 WORM Storage Initialized"},
            risk_tier="MINIMAL",
            requires_approval=False,
            human_decision=None,
            sop_reference="SOP-MEM-001",
            primary_hash="",
            chain_hash="",
            tamper_seal=""
        )
        
        # Calculate hashes for genesis block
        event_data_for_hash = {
            "timestamp": genesis_event.timestamp,
            "event_id": genesis_event.event_id,
            "sequence_number": genesis_event.sequence_number,
            "action_name": genesis_event.action_name,
            "status": genesis_event.status,
            "metadata": genesis_event.metadata,
            "risk_tier": genesis_event.risk_tier,
            "requires_approval": genesis_event.requires_approval,
            "human_decision": genesis_event.human_decision,
            "sop_reference": genesis_event.sop_reference
        }
        event_data = json.dumps(event_data_for_hash, sort_keys=True)
        genesis_event.primary_hash = CryptoManager.generate_sha256(event_data)
        genesis_event.chain_hash = CryptoManager.create_chain_hash(event_data, "GENESIS")
        genesis_event.tamper_seal = CryptoManager.create_tamper_seal(event_data, Config.SECRET_KEY)
        
        # Insert genesis block directly into the database, including signature column
        self.cursor.execute('''
            INSERT INTO audit_events (
                sequence_number, timestamp, event_id, action_name, status, metadata_json, risk_tier, requires_approval, human_decision, sop_reference, primary_hash, chain_hash, tamper_seal, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            genesis_event.sequence_number,
            genesis_event.timestamp,
            genesis_event.event_id,
            genesis_event.action_name,
            genesis_event.status,
            json.dumps(genesis_event.metadata),
            genesis_event.risk_tier,
            genesis_event.requires_approval,
            genesis_event.human_decision,
            genesis_event.sop_reference,
            genesis_event.primary_hash,
            genesis_event.chain_hash,
            genesis_event.tamper_seal,
            b''  # No signature for genesis block
        ))
        logger.info("WORM Storage initialized with genesis block")
    
    def _get_last_chain_hash(self) -> str:
        """Get the hash of the last event in the chain."""
        self.cursor.execute('SELECT primary_hash FROM audit_events ORDER BY sequence_number DESC LIMIT 1')
        result = self.cursor.fetchone()
        return result[0] if result else "GENESIS"
    
    # No longer needed: sequence_number is now AUTOINCREMENT
    
    def log_event(self, action_name: str, status: str, metadata: Dict[str, Any], 
                  risk_tier: str, requires_approval: bool, human_decision: Optional[str] = None,
                  action_id: Optional[str] = None) -> str:
        """Log an event to the WORM storage and return the event ID. Uses DB atomicity for sequence_number. Digitally signs the event."""
        import time
        from .utils import crypto_utils
        max_retries = 7
        for attempt in range(max_retries):
            try:
                self.conn.execute('BEGIN IMMEDIATE')
                event_id = action_id or CryptoManager.generate_uuid()
                timestamp = datetime.now(timezone.utc).isoformat()
                # Insert a placeholder row to get the next sequence_number
                self.cursor.execute('''
                    INSERT INTO audit_events (
                        timestamp, event_id, action_name, status, metadata_json, risk_tier, requires_approval, human_decision, sop_reference
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, event_id, action_name, status, json.dumps(metadata), risk_tier, requires_approval, human_decision, f"SOP-GOV-001-{risk_tier}"
                ))
                # Get the sequence_number just assigned
                self.cursor.execute('SELECT sequence_number FROM audit_events WHERE event_id = ?', (event_id,))
                row = self.cursor.fetchone()
                sequence_number = row[0]
                # Now build the hashes
                event_data_for_hash = {
                    "timestamp": timestamp,
                    "event_id": event_id,
                    "sequence_number": sequence_number,
                    "action_name": action_name,
                    "status": status,
                    "metadata": metadata,
                    "risk_tier": risk_tier,
                    "requires_approval": requires_approval,
                    "human_decision": human_decision,
                    "sop_reference": f"SOP-GOV-001-{risk_tier}"
                }
                event_data = json.dumps(event_data_for_hash, sort_keys=True)
                primary_hash = CryptoManager.generate_sha256(event_data)
                # Always use the primary_hash of the immediately preceding event as previous_hash
                self.cursor.execute('SELECT primary_hash FROM audit_events WHERE sequence_number = (SELECT MAX(sequence_number) FROM audit_events WHERE event_id != ?)', (event_id,))
                prev = self.cursor.fetchone()
                if prev and prev[0]:
                    previous_hash = prev[0]
                else:
                    previous_hash = "GENESIS"
                chain_hash = CryptoManager.create_chain_hash(event_data, previous_hash)
                tamper_seal = CryptoManager.create_tamper_seal(event_data, Config.SECRET_KEY)
                # Digitally sign the event hash
                crypto_utils.generate_rsa_keypair()  # Ensure keys exist
                signature = crypto_utils.sign_data(primary_hash)
                # Update the row with hashes and signature
                self.cursor.execute('''
                    UPDATE audit_events SET primary_hash=?, chain_hash=?, tamper_seal=?, signature=? WHERE event_id=?
                ''', (primary_hash, chain_hash, tamper_seal, signature, event_id))
                self.conn.commit()
                logger.info(f"Event logged: {action_name} - {status} - {event_id}")
                return event_id
            except sqlite3.IntegrityError as e:
                self.conn.rollback()
                logger.warning(f"WORM storage integrity violation (attempt {attempt+1}): {e}")
                time.sleep(0.1 * (attempt + 1))
                continue
            except Exception as e:
                self.conn.rollback()
                logger.error(f"Unexpected error during WORM event logging: {e}")
                raise
        raise RuntimeError("Failed to log event after multiple retries due to concurrency/integrity errors.")
    
    # No longer needed: event writing is now handled in log_event with atomic sequence assignment
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an event by its ID."""
        self.cursor.execute('SELECT * FROM audit_events WHERE event_id = ?', (event_id,))
        result = self.cursor.fetchone()
        
        if not result:
            return None
        
        columns = [desc[0] for desc in self.cursor.description]
        event_dict = dict(zip(columns, result))
        event_dict['metadata'] = json.loads(event_dict['metadata_json'])
        del event_dict['metadata_json']
        
        return event_dict
    
    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verify the complete integrity of the audit chain, including digital signatures."""
        logger.info("Verifying WORM storage integrity...")
        from .utils import crypto_utils
        self.cursor.execute('SELECT * FROM audit_events ORDER BY sequence_number ASC')
        events = self.cursor.fetchall()
        errors = []
        previous_hash = "GENESIS"
        for event_row in events:
            (seq_num, timestamp, event_id, action_name, status, metadata_json, 
             risk_tier, requires_approval, human_decision, sop_reference, 
             primary_hash, chain_hash, tamper_seal, signature, created_at) = event_row
            # Verify primary hash
            event_data_for_hash = {
                "timestamp": timestamp,
                "event_id": event_id,
                "sequence_number": seq_num,
                "action_name": action_name,
                "status": status,
                "metadata": json.loads(metadata_json),
                "risk_tier": risk_tier,
                "requires_approval": bool(requires_approval),
                "human_decision": human_decision,
                "sop_reference": sop_reference
            }
            event_data = json.dumps(event_data_for_hash, sort_keys=True)
            calculated_primary_hash = CryptoManager.generate_sha256(event_data)
            if calculated_primary_hash != primary_hash:
                errors.append(f"Primary hash mismatch for event {event_id}")
            # Skip chain hash and signature checks for genesis block
            if seq_num == 0:
                previous_hash = primary_hash
                continue
            # Verify chain hash
            calculated_chain_hash = CryptoManager.create_chain_hash(event_data, previous_hash)
            if calculated_chain_hash != chain_hash:
                errors.append(f"Chain hash break at event {event_id}")
            # Verify tamper seal
            calculated_tamper_seal = CryptoManager.create_tamper_seal(event_data, Config.SECRET_KEY)
            if calculated_tamper_seal != tamper_seal:
                errors.append(f"Tamper seal violation for event {event_id}")
            # Verify digital signature
            if signature is not None:
                if not crypto_utils.verify_signature(primary_hash, signature):
                    errors.append(f"Signature verification failed for event {event_id}")
            else:
                errors.append(f"Missing signature for event {event_id}")
            previous_hash = primary_hash
        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"Integrity verified: {len(events)} events checked. Chain is tamper-proof and signatures valid.")
        else:
            logger.error(f"Integrity compromised: {len(errors)} violations detected!")
            for error in errors:
                logger.error(f"  - {error}")
        return is_valid, errors
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get a summary of all audit events."""
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_actions,
                COUNT(CASE WHEN status = 'BREACH' THEN 1 END) as breaches,
                COUNT(CASE WHEN status = 'DENIED' THEN 1 END) as denials,
                COUNT(CASE WHEN status = 'APPROVED' THEN 1 END) as approvals,
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_actions,
                COUNT(CASE WHEN requires_approval = 1 THEN 1 END) as approval_required_actions
            FROM audit_events
        ''')
        
        result = self.cursor.fetchone()
        return {
            "total_events": result[0],
            "successful_actions": result[1],
            "breaches": result[2],
            "denials": result[3],
            "approvals": result[4],
            "pending_actions": result[5],
            "approval_required_actions": result[6]
        }
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all pending actions that require human approval from persistent storage."""
        self.cursor.execute('''
            SELECT event_id, action_name, metadata_json, risk_tier, timestamp
            FROM audit_events 
            WHERE status = 'PENDING'
            ORDER BY timestamp ASC
        ''')
        pending = []
        for row in self.cursor.fetchall():
            pending.append({
                "event_id": row[0],
                "action_name": row[1],
                "metadata": json.loads(row[2]),
                "risk_tier": row[3],
                "timestamp": row[4]
            })
        return pending
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
        logger.info("WORM Storage connection closed")
