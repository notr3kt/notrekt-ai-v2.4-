"""
HITLAgent - Manages Human-in-the-Loop approvals, denials, and audit logging.
SOP-EXE-002, SOP-GOV-001
"""

from datetime import datetime, timezone
from datetime import datetime
from app.utils.llm_provider import LLMProvider
from app.notification import notify_all

class HITLAgent:
    async def request_approval(self, action_id, action_context, notify_callback=None):
        """
        Request human approval for a pending action. Notifies a human via callback, or uses the default notification system.
        """
        msg = f"[HITL] Approval requested for action {action_id}. Context: {action_context}"
        if notify_callback:
            await notify_callback(action_id, action_context)
        else:
            await notify_all(action_id, action_context)
        return {"status": "pending", "action_id": action_id}
    def __init__(self, audit_log):
        self.audit_log = audit_log

    async def approve(self, action_id, approver_context):
        # Use LLMProvider to generate an approval explanation
        prompt = (
            f"You are a human-in-the-loop (HITL) auditor. Explain why the following action was approved, "
            f"and what governance or compliance rules apply.\nAction ID: {action_id}\nApprover: {approver_context.get('user')}"
        )
        llm_explanation = await LLMProvider.generate_text(prompt, model_type="pro")
        event = {
            "action_id": action_id,
            "approver": approver_context.get("user"),
            "decision": "approved",
            "llm_explanation": llm_explanation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.audit_log.log_event(
            action_name="HITL_APPROVAL",
            status="APPROVED",
            metadata=event,
            risk_tier="HIGH",
            requires_approval=False,
            human_decision="APPROVED"
        )
        return {"status": "approved", "action_id": action_id, "llm_explanation": llm_explanation}

    async def reject(self, action_id, approver_context):
        # Use LLMProvider to generate a rejection explanation
        prompt = (
            f"You are a human-in-the-loop (HITL) auditor. Explain why the following action was rejected, "
            f"and what governance or compliance rules apply.\nAction ID: {action_id}\nApprover: {approver_context.get('user')}"
        )
        llm_explanation = await LLMProvider.generate_text(prompt, model_type="pro")
        event = {
            "action_id": action_id,
            "approver": approver_context.get("user"),
            "decision": "rejected",
            "llm_explanation": llm_explanation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.audit_log.log_event(
            action_name="HITL_REJECTION",
            status="DENIED",
            metadata=event,
            risk_tier="HIGH",
            requires_approval=False,
            human_decision="DENIED"
        )
        return {"status": "rejected", "action_id": action_id, "llm_explanation": llm_explanation}
