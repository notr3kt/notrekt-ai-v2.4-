"""
test_governance_and_audit.py - Critical tests for governance, breach delegation, and audit logging
SOP-GOV-001, SOP-GOV-003, SOP-EXE-002
"""
import pytest
import asyncio

# Import from the app package
from app.notrekt_system import NotRektAISystem

@pytest.mark.asyncio
async def test_breach_delegation_and_logging():
    system = NotRektAISystem()
    # Simulate a blocked action (breach)
    result = await system.process_action(
        action_name="SYSTEM_ADMIN",
        metadata={"operation": "shutdown_production_server", "target": "primary_database", "reason": "maintenance"}
    )
    assert result is not None and isinstance(result, dict)
    assert result.get("status") == "blocked"
    assert result.get("risk_tier", "").upper() in ("CRITICAL", "HIGH", "BLOCKED")
    assert "event_id" in result
    # Check audit log for breach event
    event = system.worm_storage.get_event_by_id(result["event_id"])
    assert event is not None and isinstance(event, dict)
    assert event.get("status") == "BREACH"
    assert event.get("action_name") == "SYSTEM_ADMIN"
    # Check audit object structure
    assert "metadata" in event and event["metadata"] is not None
    assert (
        (isinstance(event["metadata"], dict) and ("reason" in event["metadata"] or "user_context" in event["metadata"]))
    )
    system.shutdown()

@pytest.mark.asyncio
async def test_advanced_audit_object_logging():
    system = NotRektAISystem()
    # Simulate a valid action
    result = await system.process_action(
        action_name="WRITE_CODE",
        metadata={"module_name": "test_module.py", "language": "python", "description": "Test module"},
        user_context={"user_id": "devtest", "role": "developer"}
    )
    assert result is not None and isinstance(result, dict)
    assert result.get("status") == "success"
    event = system.worm_storage.get_event_by_id(result["event_id"])
    assert event is not None and isinstance(event, dict)
    # Audit object must include all required fields
    assert event.get("action_name") == "WRITE_CODE"
    assert event.get("status") == "SUCCESS"
    assert "metadata" in event and event["metadata"] is not None
    # Defensive: check for user_context in metadata or result
    metadata = event["metadata"] if isinstance(event["metadata"], dict) else {}
    user_context_in_metadata = "user_context" in metadata
    user_context_in_result = "user_context" in result and isinstance(result["user_context"], dict)
    assert user_context_in_metadata or user_context_in_result
    system.shutdown()

def test_integrity_verification():
    system = NotRektAISystem()
    valid, errors = system.worm_storage.verify_integrity()
    assert valid
    assert errors == []
    system.shutdown()
