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
        Returns (True, None) if supported, else (False, reason).
        """
        if not sources_used:
            return False, "No sources provided for verification."
        sources_text = "\n---\n".join(sources_used)
        prompt = (
            f"You are a fact-checking agent. Given the following AI output and sources, determine if every claim in the output is directly supported by the sources.\n"
            f"If any claim is not supported, respond with 'UNSUPPORTED: <reason>'. If all claims are supported, respond with 'SUPPORTED'.\n"
            f"AI Output:\n{ai_output_content}\n"
            f"Sources:\n{sources_text}\n"
            f"Result:"
        )
        llm = LLMProvider("gemini", {})
        result = llm.generate(prompt)
        if result.strip().upper().startswith("SUPPORTED"):
            return True, None
        if result.strip().upper().startswith("UNSUPPORTED"):
            reason = result.split(":", 1)[-1].strip() if ":" in result else "Claim not supported by sources."
            return False, reason
        return False, "Unable to determine support from LLM response."
