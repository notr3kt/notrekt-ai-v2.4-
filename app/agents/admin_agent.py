"""
AdminAgent - Manages SOP versioning, model versioning, and audit object registration.
SOP-GOV-003
"""

from app.utils.llm_provider import LLMProvider
from datetime import datetime, timezone

class AdminAgent:
    async def enforce_registry_audit(self, registry_type: str, entry: str, context_info=None, hitl_callback=None):
        """
        Enforce WORM-backed audit for registry operations (model/SOP add/remove).
        Logs to WORM and triggers HITL if required.
        """
        self.worm_storage.log_event(
            action_name=f"REGISTRY_{registry_type.upper()}_MODIFIED",
            status="PENDING",
            metadata={
                "entry": entry,
                "context": context_info,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            risk_tier="MEDIUM",
            requires_approval=True,
            human_decision=None
        )
        print(f"[AUDIT] Registry {registry_type} modification for {entry} logged as PENDING. Awaiting HITL.")
        if hitl_callback:
            await hitl_callback(entry, context_info)

    def __init__(self, sop_registry, model_registry, worm_storage):
        self.sop_registry = sop_registry
        self.model_registry = model_registry
        self.worm_storage = worm_storage

    async def register_sop_version(self, sop_version, context_info=None):
        """
        Log SOP version as an immutable audit object (SOP-GOV-003) and use LLMProvider to explain the change.
        """
        from app.utils import audit_utils
        audit_utils.export_audit_log(
            log_path=self.sop_registry,
            export_path=f"sop_version_{sop_version}.json"
        )
        # Use LLM to explain the SOP version registration
        prompt = (
            f"You are an admin agent. Explain the significance of registering SOP version {sop_version} in the context of governance and compliance.\n"
            f"Context: {context_info if context_info else 'N/A'}"
        )
        llm_explanation = await LLMProvider.generate_text(prompt, model_type="pro")
        self.worm_storage.log_event(
            action_name="LLM_SOP_VERSION_REGISTERED",
            status="SUCCESS",
            metadata={
                "sop_version": sop_version,
                "llm_explanation": llm_explanation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            risk_tier="LOW",
            requires_approval=False,
            human_decision=None
        )
        print(f"[AUDIT] SOP version {sop_version} registered and exported. LLM: {llm_explanation}")

    async def register_model_version(self, model_version, context_info=None):
        """
        Log model version as an immutable audit object (SOP-GOV-003) and use LLMProvider to explain the change.
        """
        from app.utils import audit_utils
        audit_utils.export_audit_log(
            log_path=self.model_registry,
            export_path=f"model_version_{model_version}.json"
        )
        # Use LLM to explain the model version registration
        prompt = (
            f"You are an admin agent. Explain the significance of registering model version {model_version} in the context of governance and compliance.\n"
            f"Context: {context_info if context_info else 'N/A'}"
        )
        llm_explanation = await LLMProvider.generate_text(prompt, model_type="pro")
        self.worm_storage.log_event(
            action_name="LLM_MODEL_VERSION_REGISTERED",
            status="SUCCESS",
            metadata={
                "model_version": model_version,
                "llm_explanation": llm_explanation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            risk_tier="LOW",
            requires_approval=False,
            human_decision=None
        )
        print(f"[AUDIT] Model version {model_version} registered and exported. LLM: {llm_explanation}")
