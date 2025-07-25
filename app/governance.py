# ---
# governance.py - Governance logic for NOTREKT.AI v2.0
# Refactor Summary (2025-07-25):
# - Handles WORM logging, HITL decision logging, and compliance enforcement (SOP-GOV-001, SOP-EXE-002)
# - All logs are cryptographically chained and immutable
# ---

import json
from pathlib import Path

class GovernanceCore:
    """
    Loads and caches rules.json in memory for fast access.
    Provides rule lookup and validation for actions.
    """
    def __init__(self, rules_path):
        with open(rules_path, 'r') as f:
            self.rules_data = json.load(f)
        self.rules_by_action = {r['action_name']: r for r in self.rules_data['rules']}

    def get_rule_for_action(self, action_name):
        return self.rules_by_action.get(action_name)

# [GAP: Implement WORM logging, HITL decision logging, compliance checks]
def log_hitl_decision(action_id, decision, reason, approver_id, timestamp):
    """
    Log a HITL (Human-in-the-Loop) decision to the WORM audit log with cryptographic chaining.
    Args:
        action_id: The ID of the action being decided on.
        decision: The decision made (APPROVE/DENY).
        reason: Reason for the decision.
        approver_id: ID of the human approver.
        timestamp: Decision timestamp.
    SOP Reference: SOP-GOV-001, SOP-EXE-002
    """
    try:
        from worm_storage import WORMStorage
    except ImportError:
        import sys, os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../core_ip')))
        from worm_storage import WORMStorage
    from config_manager import Config
    storage = WORMStorage(Config.WORM_DB_PATH)
    storage.log_event(
        action_name="HITL_DECISION",
        status=decision.upper(),
        metadata={
            "reason": reason,
            "approver_id": approver_id,
            "timestamp": timestamp,
            "action_id": action_id
        },
        risk_tier="HITL",
        requires_approval=True,
        human_decision=decision,
        action_id=action_id
    )
    storage.close()
