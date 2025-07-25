"""
ResearchAgent - Enforces zero-guessing, RAG-001, and citation for all research outputs.
SOP-REV-002, SOP-RAG-001
"""

from app.utils.llm_provider import LLMProvider
from app.worm_storage import WORMStorage
from datetime import datetime

class ResearchAgent:
    def __init__(self, knowledge_base, worm_storage: WORMStorage):
        self.knowledge_base = knowledge_base
        self.cache = {}
        self.worm_storage = worm_storage

    def answer(self, query, user_context=None):
        # In-memory cache for frequent queries
        if query in self.cache:
            return self.cache[query]

        # RAG: Retrieve context from knowledge base (simulate)
        context = self.knowledge_base.retrieve(query) if hasattr(self.knowledge_base, 'retrieve') else None
        rag_prompt = f"Answer the following question using only the provided context. Cite all sources.\n\nContext:\n{context if context else '[No context found]'}\n\nQuestion: {query}\n\nAnswer (with citations):"

        # Call LLMProvider
        llm_response = LLMProvider.generate_text(rag_prompt, model_type="flash")

        # Enforce citation: check for citation pattern (e.g., [1], (source), etc.)
        has_citation = any(token in llm_response for token in ['[', '(', 'source', 'http'])
        if not has_citation:
            answer = "[GAP: No verifiable source found]"
        else:
            answer = llm_response

        # Audit log the LLM/RAG action
        self.worm_storage.log_event(
            action_name="RESEARCH_ANSWER",
            status="SUCCESS" if has_citation else "BREACH",
            metadata={
                "query": query,
                "context": context,
                "llm_prompt": rag_prompt,
                "llm_response": llm_response,
                "citation_enforced": has_citation,
                "user_context": user_context,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            risk_tier="LOW" if has_citation else "HIGH",
            requires_approval=not has_citation,
            human_decision=None
        )

        self.cache[query] = answer
        return answer
