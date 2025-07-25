"""
CodeAgent - Enforces secure code generation, validation, and audit logging.
SOP-REV-002, SOP-GOV-001
"""

from app.utils.llm_provider import LLMProvider
from datetime import datetime

class CodeAgent:
    def __init__(self, worm_storage):
        self.worm_storage = worm_storage

    def generate_code(self, spec, validation_rules=None):
        """
        Uses LLMProvider to generate code from a spec, validates it, and logs all LLM actions to WORM storage.
        """
        # Step 1: Generate code using LLM
        prompt = (
            f"You are a secure code generation agent. Given the following specification, generate production-ready, secure code.\n"
            f"Specification: {spec}"
        )
        code = LLMProvider.generate_text(prompt, model_type="pro")
        # Step 2: Validate code using LLM (if rules provided)
        validation_result = None
        if validation_rules:
            validation_prompt = (
                f"You are a code security auditor. Validate the following code against these rules: {validation_rules}.\n"
                f"Code: {code}"
            )
            validation_result = LLMProvider.generate_text(validation_prompt, model_type="pro")
        # Step 3: Log all LLM actions
        self.worm_storage.log_event(
            action_name="LLM_CODE_GENERATION",
            status="SUCCESS",
            metadata={
                "spec": spec,
                "generated_code": code,
                "validation_rules": validation_rules,
                "validation_result": validation_result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            risk_tier="MEDIUM",
            requires_approval=False,
            human_decision=None
        )
        return {"code": code, "validation_result": validation_result}
