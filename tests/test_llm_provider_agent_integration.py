import unittest
from unittest.mock import patch
from app.utils.llm_provider import LLMProvider
from app.agents.admin_agent import AdminAgent
from app.worm_storage import WORMStorage
import tempfile
import os

class DummyWormStorage(WORMStorage):
    def __init__(self):
        super().__init__(db_path=tempfile.mktemp(suffix='.db'))
    def close(self):
        super().close()
        os.remove(self.db_path)

class TestLLMProviderAgentIntegration(unittest.TestCase):
    @patch('requests.post')
    def test_admin_agent_register_sop_version_llm(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "SOP version registered for compliance."}]}}
            ]
        }
        worm = DummyWormStorage()
        # Initialize sop_registry.db as a WORMStorage DB so audit_events table exists
        from app.worm_storage import WORMStorage as RealWORMStorage
        sop_registry_db = tempfile.mktemp(suffix='.db')
        sop_registry = RealWORMStorage(db_path=sop_registry_db)
        sop_registry.close()
        agent = AdminAgent(sop_registry_db, "model_registry.db", worm)
        agent.register_sop_version("vX.Y-test", context_info="Integration test run.")
        # Check that the event was logged
        event = worm.get_event_by_id(next(iter(worm.cursor.execute('SELECT event_id FROM audit_events WHERE action_name=?', ("LLM_SOP_VERSION_REGISTERED",)).fetchone()), None))
        self.assertIsNotNone(event)
        self.assertIn("SOP version registered", event["metadata"]["llm_explanation"])
        worm.close()

if __name__ == "__main__":
    unittest.main()
