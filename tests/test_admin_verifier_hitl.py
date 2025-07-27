import pytest
from unittest import mock
from app.agents import admin_agent, hitl_agent
from app.verifier_agent import VerifierAgent

def test_adminagent_registry_audit_stub():
    agent = admin_agent.AdminAgent(sop_registry=None, model_registry=None, worm_storage=mock.Mock())
    agent.enforce_registry_audit("model", "test-model", context_info={"user": "alice"})
    # Should log event with PENDING status
    agent.worm_storage.log_event.assert_called_once()
    args, kwargs = agent.worm_storage.log_event.call_args
    assert args[0] == "REGISTRY_MODEL_MODIFIED"
    assert kwargs["status"] == "PENDING"
    assert kwargs["metadata"]["entry"] == "test-model"

def test_verifieragent_registry_check_stub():
    verifier = VerifierAgent()
    registry = {"foo/bar"}
    assert verifier.enforce_registry_check(registry, "foo/bar") is True
    assert verifier.enforce_registry_check(registry, "not-in-registry") is False

def test_hitlagent_request_approval_stub():
    agent = hitl_agent.HITLAgent(audit_log=mock.Mock())
    result = agent.request_approval("action-123", {"user": "bob"})
    assert result["status"] == "pending"
    assert result["action_id"] == "action-123"
