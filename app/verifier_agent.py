# ---
# verifier_agent.py - VerifierAgent for NOTREKT.AI v2.0
# Refactor Summary (2025-07-25):
# - Intercepts and validates AI-generated responses for hallucinations/unverified claims (SOP-REV-002)
# - [GAP: Implement RAG/KB validation logic]
# ---

from .rag_system import synthesize_answer


from .utils.llm_provider import LLMProvider

class VerifierAgent:
    def verify_output(self, ai_output_content: str, sources_used: list) -> tuple:
        """
        Use LLM to verify if ai_output_content is truly supported by sources_used.
        Returns (is_valid, confidence, reason, breach_code)
        """
        import json
        if not sources_used:
            return False, 0, "No sources provided for verification.", "NO-SOURCES"
        sources_text = "\n---\n".join(sources_used)
        prompt = (
            "You are a fact-checking agent. Given the following AI output and sources, return JSON: "
            '{"supported": true/false, "unsupported_claims": [list]}. '
            "AI Output: " + ai_output_content + "\nSources: " + sources_text
        )
        llm = LLMProvider()
        result = llm.generate_text(prompt, model_type="pro")
        try:
            parsed = json.loads(result)
            is_valid = parsed.get("supported", False)
            unsupported = parsed.get("unsupported_claims", [])
            reason = "All claims supported." if is_valid else f"Unsupported claims: {unsupported}"
            confidence = 95 if is_valid else 50
            return is_valid, confidence, reason, None if is_valid else "UNSUPPORTED-CLAIMS"
        except Exception:
            return False, 0, "VerifierAgent: Invalid LLM response format.", "VERIFIER-ERROR"
