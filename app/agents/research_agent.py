"""
ResearchAgent - Enforces zero-guessing, RAG-001, and citation for all research outputs.
SOP-REV-002, SOP-RAG-001
"""

from app.utils.llm_provider import LLMProvider
from app.worm_storage import WORMStorage
from datetime import datetime, timezone

class ResearchAgent:
    def __init__(self, knowledge_base, worm_storage: WORMStorage):
        self.knowledge_base = knowledge_base
        self.worm_storage = worm_storage
        # Use persistent cache table in WORMStorage DB
        self._init_cache_table()

    def _init_cache_table(self):
        conn = self.worm_storage.conn
        conn.execute('''CREATE TABLE IF NOT EXISTS research_cache (
            query TEXT PRIMARY KEY,
            answer TEXT,
            created_at TEXT
        )''')
        conn.commit()

    def _get_cache(self, query):
        conn = self.worm_storage.conn
        row = conn.execute('SELECT answer FROM research_cache WHERE query = ?', (query,)).fetchone()
        return row[0] if row else None

    def _set_cache(self, query, answer):
        conn = self.worm_storage.conn
        conn.execute('INSERT OR REPLACE INTO research_cache (query, answer, created_at) VALUES (?, ?, ?)',
                     (query, answer, datetime.now(timezone.utc).isoformat()))
        conn.commit()

    def answer(self, query, user_context=None):
        # Persistent cache for frequent queries
        cached = self._get_cache(query)
        if cached:
            return cached

        # Retrieve top sources from knowledge base (must have 'search' or 'retrieve')
        sources = []
        context = None
        if hasattr(self.knowledge_base, 'search'):
            sources = self.knowledge_base.search(query, k=5)  # List[SearchResult]
            # Build context from top sources
            context = '\n'.join([getattr(s.document, 'content', str(s.document)) for s in sources])
        elif hasattr(self.knowledge_base, 'retrieve'):
            context = self.knowledge_base.retrieve(query)
        else:
            context = None

        rag_prompt = f"Answer the following question using only the provided context. Cite all sources.\n\nContext:\n{context if context else '[No context found]'}\n\nQuestion: {query}\n\nAnswer (with citations):"

        # Call LLMProvider
        llm_response = LLMProvider.generate_text(rag_prompt, model_type="flash")

        # Robust citation enforcement: require answer to reference at least one actual source
        matched_sources = []
        if sources:
            for s in sources:
                # Try to match by document id, title, or url if present
                doc = s.document
                doc_id = getattr(doc, 'doc_id', None) or getattr(doc, 'id', None)
                doc_title = getattr(doc, 'title', None)
                doc_url = getattr(doc, 'url', None)
                # Check if any identifier is present in the answer
                for ident in filter(None, [str(doc_id), doc_title, doc_url]):
                    if ident and ident in llm_response:
                        matched_sources.append(ident)
                        break

        has_citation = bool(matched_sources)
        if not has_citation:
            answer = "[GAP: No verifiable source found]"
        else:
            answer = llm_response

        # Audit log the LLM/RAG action, including matched sources
        self.worm_storage.log_event(
            action_name="RESEARCH_ANSWER",
            status="SUCCESS" if has_citation else "BREACH",
            metadata={
                "query": query,
                "context": context,
                "llm_prompt": rag_prompt,
                "llm_response": llm_response,
                "citation_enforced": has_citation,
                "matched_sources": matched_sources,
                "user_context": user_context,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            risk_tier="LOW" if has_citation else "HIGH",
            requires_approval=not has_citation,
            human_decision=None
        )

        self._set_cache(query, answer)
        return answer
