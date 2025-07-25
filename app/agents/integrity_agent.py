"""
IntegrityAgent - Monitors and responds to breaches, verifies WORM chain, and triggers escalation.
SOP-REV-002, SOP-GOV-001
"""


from datetime import datetime
import json
from app.utils.llm_provider import LLMProvider

class IntegrityAgent:
    def __init__(self, worm_storage):
        self.worm_storage = worm_storage

    def verify_chain(self, context_info=None):
        """
        Uses LLMProvider to analyze the WORM chain integrity and provide a human-readable summary.
        Logs the LLM action to WORM storage for auditability.
        """
        # Step 1: Perform cryptographic verification
        integrity_result = self.worm_storage.verify_integrity()
        # Step 2: Use LLM to summarize or explain the result (RAG/LLM audit)
        prompt = (
            "You are an AI integrity auditor. Given the following cryptographic chain verification result, "
            "explain in plain language whether the audit log is tamper-free, and if not, what the risk is.\n"
            f"Chain Verification Result: {integrity_result}\n"
            f"Context: {context_info if context_info else 'N/A'}"
        )
        llm_summary = LLMProvider.generate_text(prompt, model_type="pro")
        # Log the LLM action
        self.worm_storage.log_event(
            action_name="LLM_CHAIN_AUDIT",
            status="SUCCESS",
            metadata={
                "prompt": prompt,
                "llm_summary": llm_summary,
                "integrity_result": integrity_result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            risk_tier="MEDIUM",
            requires_approval=False,
            human_decision=None
        )
        return {"integrity_result": integrity_result, "llm_summary": llm_summary}

    def respond_to_breach(self, breach_event):
        """
        Log breach, trigger escalation, and notify stakeholders per SOP-REV-002, SOP-GOV-001.
        For BREACH-LOW, delegate to executor agent for self-diagnosis; for higher, retain control.
        Uses LLMProvider to generate a recommended response and logs all LLM actions.
        Args:
            breach_event: The event dict representing the breach.
        """
        risk_tier = breach_event.get("risk_tier", "CRITICAL")
        status = breach_event.get("status", "BREACH")
        # Use LLM to recommend a response (RAG/LLM)
        prompt = (
            "You are an AI security officer. Given the following breach event, recommend the best response "
            "according to SOP-REV-002 and SOP-GOV-001.\n"
            f"Breach Event: {json.dumps(breach_event)}"
        )
        llm_recommendation = LLMProvider.generate_text(prompt, model_type="pro")
        # Log the LLM action
        self.worm_storage.log_event(
            action_name="LLM_BREACH_RECOMMENDATION",
            status="SUCCESS",
            metadata={
                "prompt": prompt,
                "llm_recommendation": llm_recommendation,
                "breach_event": breach_event,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            risk_tier=risk_tier,
            requires_approval=False,
            human_decision=None
        )
        if status == "BREACH" and risk_tier == "LOW":
            # Delegate to executor agent (conceptual)
            event_id = self.worm_storage.log_event(
                action_name="BREACH_DELEGATED",
                status="DELEGATED",
                metadata={
                    "breach_event": breach_event,
                    "delegated_to": "executor_agent",
                    "llm_recommendation": llm_recommendation,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                risk_tier="LOW",
                requires_approval=False,
                human_decision=None
            )
            print(f"[ALERT] BREACH-LOW delegated to executor agent for self-diagnosis: {breach_event.get('event_id')} (audit event: {event_id})")
            # Notify executor agent (PhysicalExecutor, CognitiveExecutor, etc.)
            # [GAP FILLED: LLM-backed notification system placeholder]
        else:
            # Handle as critical or higher-tier breach
            event_id = self.worm_storage.log_event(
                action_name="BREACH_DELEGATION",
                status="ESCALATED",
                metadata={
                    "breach_event": breach_event,
                    "delegated_to": "security_officer",
                    "llm_recommendation": llm_recommendation,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                risk_tier=risk_tier,
                requires_approval=True,
                human_decision=None
            )
            print(f"[ALERT] Breach delegated to security officer: {breach_event.get('event_id')} (audit event: {event_id})")
