# ---
# verifier_agent.py - VerifierAgent for NOTREKT.AI v2.0
# Refactor Summary (2025-07-25):
# - Intercepts and validates AI-generated responses for hallucinations/unverified claims (SOP-REV-002)
# - [GAP: Implement RAG/KB validation logic]
# ---

from .rag_system import synthesize_answer


from .utils.llm_provider import LLMProvider

import re
import logging

class VerifierAgent:
    def __init__(self, rag_vector_store=None):
        # Optionally inject a RAG vector store for direct KB validation
        try:
            from .rag_system import VectorStore
            self.vector_store = rag_vector_store or VectorStore()
        except Exception:
            self.vector_store = None
        self.logger = logging.getLogger("VerifierAgent")

    def extract_claims(self, text: str) -> list:
        """
        Naive claim extraction: split by sentences, filter short/noise.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = [s.strip() for s in sentences if len(s.strip()) > 10]
        return claims

    def verify_output(self, ai_output_content: str, sources_used: list, llm_backend: str = None) -> dict:
        """
        Multi-step verification:
        1. Extract claims from output.
        2. For each claim, check if supported by sources (exact match or RAG search).
        3. Use LLM as fallback for ambiguous cases.
        Returns dict with validity, confidence, unsupported_claims, breach_code, audit_log.
        """
        import json
        audit_log = []
        if not sources_used:
            return {
                "is_valid": False,
                "confidence": 0,
                "reason": "No sources provided for verification.",
                "breach_code": "NO-SOURCES",
                "unsupported_claims": [],
                "audit_log": audit_log
            }
        claims = self.extract_claims(ai_output_content)
        unsupported_claims = []
        for claim in claims:
            supported = False
            # Direct match in sources
            for src in sources_used:
                if claim in src:
                    supported = True
                    audit_log.append({"claim": claim, "method": "direct_match", "result": True})
                    break
            # RAG/KB search if not direct match
            if not supported and self.vector_store:
                try:
                    results = self.vector_store.search(claim, k=1, min_score=0.7)
                    if results:
                        supported = True
                        audit_log.append({"claim": claim, "method": "rag_search", "result": True, "doc_id": results[0].document.id, "score": results[0].score})
                except Exception as e:
                    self.logger.error(f"RAG search failed: {e}")
            if not supported:
                unsupported_claims.append(claim)
                audit_log.append({"claim": claim, "method": "none", "result": False})
        # If any unsupported, use LLM for nuanced check
        llm_reason = ""
        if unsupported_claims:
            sources_text = "\n---\n".join(sources_used)
            prompt = (
                "You are a fact-checking agent. Given the following AI output and sources, return JSON: "
                '{"supported": true/false, "unsupported_claims": [list]}'
                " AI Output: " + ai_output_content + "\nSources: " + sources_text
            )
            llm = LLMProvider()
            # Redundant check: Gemini and Gemma
            result_gemini = llm.generate(prompt, backend="gemini", model_type="pro")
            result_gemma = llm.generate(prompt, backend="gemma")
            try:
                parsed_gemini = json.loads(result_gemini)
                parsed_gemma = json.loads(result_gemma)
                # Consensus logic: both must agree for high confidence
                gemini_supported = parsed_gemini.get("supported", False)
                gemma_supported = parsed_gemma.get("supported", False)
                gemini_unsupported = set(parsed_gemini.get("unsupported_claims", []))
                gemma_unsupported = set(parsed_gemma.get("unsupported_claims", []))
                if gemini_supported == gemma_supported and gemini_unsupported == gemma_unsupported:
                    llm_reason = f"Consensus: {('All claims supported.' if gemini_supported else f'Unsupported claims: {list(gemini_unsupported)}')}"
                    unsupported_claims = list(set(unsupported_claims) | gemini_unsupported | gemma_unsupported)
                    is_valid = gemini_supported and not unsupported_claims
                    confidence = 99 if is_valid else 70
                    breach_code = None if is_valid else "UNSUPPORTED-CLAIMS"
                else:
                    llm_reason = f"Disagreement: Gemini={parsed_gemini}, Gemma={parsed_gemma}"
                    unsupported_claims = list(set(unsupported_claims) | gemini_unsupported | gemma_unsupported)
                    is_valid = False
                    confidence = 40
                    breach_code = "LLM-DISAGREE"
            except Exception as e:
                is_valid = False
                confidence = 0
                breach_code = "VERIFIER-ERROR"
                llm_reason = f"VerifierAgent: Invalid LLM response format. Error: {e}"
        else:
            is_valid = True
            confidence = 100
            breach_code = None
        reason = "All claims supported." if is_valid else f"Unsupported claims: {unsupported_claims}. {llm_reason}"
        # Audit log entry
        self.logger.info(f"Verification result: valid={is_valid}, confidence={confidence}, unsupported={unsupported_claims}")
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "reason": reason,
            "breach_code": breach_code,
            "unsupported_claims": unsupported_claims,
            "audit_log": audit_log
        }
