import os
import tempfile
import shutil
from app.worm_storage import WORMStorage
from app.agents.research_agent import ResearchAgent

class DummyKnowledgeBase:
    def search(self, query, k=5):
        class DummyDoc:
            doc_id = "doc-123"
            title = "Trusted Source"
            url = "https://trusted.example.com"
            content = "This is a trusted answer about AI."
        class DummyResult:
            document = DummyDoc()
        return [DummyResult()]

def test_worm_storage_and_research_agent():
    # Use a temp DB for isolation
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_worm.db")
    ws = None
    try:
        ws = WORMStorage(db_path=db_path)
        kb = DummyKnowledgeBase()
        agent = ResearchAgent(knowledge_base=kb, worm_storage=ws)
        # Patch LLMProvider to always return a citation
        import sys
        from unittest.mock import patch
        with patch("app.utils.llm_provider.LLMProvider.generate_text", return_value="This is a trusted answer about AI. [doc-123] (https://trusted.example.com)"):
            answer = agent.answer("What is AI?", user_context={"user": "testuser"})
        assert "trusted" in answer.lower() or "doc-123" in answer or "https://trusted.example.com" in answer
        # Check audit log
        valid, errors = ws.verify_integrity()
        assert valid, f"Audit chain errors: {errors}"
    finally:
        if ws is not None:
            ws.close()
        shutil.rmtree(temp_dir)
