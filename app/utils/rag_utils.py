"""
rag_utils.py - Utilities for RAG source logging, context window management, and drift detection.
SOP-RAG-001
"""
def log_rag_sources(task_id, query, sources_retrieved, llm_response_id, confidence_score, worm_storage=None):
    """
    Log RAG trace to the WORM audit log, including all details as a RAG_TRACE action.
    """
    metadata = {
        "task_id": task_id,
        "query": query,
        "sources_retrieved": sources_retrieved,
        "llm_response_id": llm_response_id,
        "confidence_score": confidence_score
    }
    if worm_storage:
        worm_storage.log_event(
            action_name="RAG_TRACE",
            status="SUCCESS",
            metadata=metadata,
            risk_tier="LOW",
            requires_approval=False,
            human_decision=None
        )
    else:
        import json
        with open("rag_source_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata) + "\n")

def detect_context_drift(session_history, current_context_window):
    """
    Simulate detecting if the current context is losing coherence or exceeding limits.
    Compare a hash of the current context with a summary of session_history.
    """
    import hashlib
    def hash_text(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    context_hash = hash_text(current_context_window)
    history_summary = " ".join(session_history[-5:]) if session_history else ""
    history_hash = hash_text(history_summary)
    if context_hash != history_hash:
        print(f"[RAG][DRIFT] Context drift detected: context_hash={context_hash[:8]}, history_hash={history_hash[:8]}")
        return True
    return False

def get_top_k_results(query, vector_index, k=3):
    """
    Retrieve the top K most relevant results from the vector index for a query.
    Implements vector search, returns top k results.
    """
    if not hasattr(vector_index, "search"):
        return []
    # Assume vector_index is a FAISS index and query is a string
    try:
        embedding = vector_index.model.encode([query])
        D, I = vector_index.search(embedding, k)
        results = []
        for idx in I[0]:
            if idx == -1:
                continue
            results.append(vector_index.documents[idx])
        return results
    except Exception as e:
        print(f"[RAG][ERROR] Vector search failed: {e}")
        return []
