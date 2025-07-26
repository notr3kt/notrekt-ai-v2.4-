"""
End-to-End Test for NOTREKT-AI v2.3 LLMProvider and Agent LLM/Audit Integration
"""
import base64
from datetime import datetime
from app.utils.llm_provider import LLMProvider
from app.worm_storage import WORMStorage
from app.agents.integrity_agent import IntegrityAgent
from app.agents.hitl_agent import HITLAgent
from app.agents.code_agent import CodeAgent
from app.agents.admin_agent import AdminAgent

# Setup WORM storage (use a test DB path)
worm = WORMStorage(db_path='notrekt_worm_audit_test.db')

# 1. Test LLMProvider (text, structured, multimodal)
def test_llm_provider():
    print("Testing LLMProvider.generate_text...")
    text = LLMProvider.generate_text("Summarize the importance of audit logging in AI governance.")
    print("Text Response:", text)

    print("Testing LLMProvider.generate_structured_response...")
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    structured = LLMProvider.generate_structured_response("Summarize the importance of audit logging in AI governance.", schema)
    print("Structured Response:", structured)

    print("Testing LLMProvider.generate_multimodal_response...")
    # Use a small blank PNG for demo
    blank_png = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR').decode()
    multimodal = LLMProvider.generate_multimodal_response("What is this image?", blank_png)
    print("Multimodal Response:", multimodal)

# 2. Test IntegrityAgent
integrity_agent = IntegrityAgent(worm)
def test_integrity_agent():
    print("Testing IntegrityAgent.verify_chain...")
    result = integrity_agent.verify_chain(context_info="Routine audit test.")
    print("Chain Verification Result:", result)

    print("Testing IntegrityAgent.respond_to_breach...")
    breach_event = {"event_id": "test123", "risk_tier": "LOW", "status": "BREACH"}
    response = integrity_agent.respond_to_breach(breach_event)
    print("Breach Response:", response)

# 3. Test HITLAgent
hitl_agent = HITLAgent(worm)
def test_hitl_agent():
    print("Testing HITLAgent.approve...")
    approval = hitl_agent.approve("action123", {"user": "alice"})
    print("Approval:", approval)

    print("Testing HITLAgent.reject...")
    rejection = hitl_agent.reject("action456", {"user": "bob"})
    print("Rejection:", rejection)

# 4. Test CodeAgent
code_agent = CodeAgent(worm)
def test_code_agent():
    print("Testing CodeAgent.generate_code...")
    code = code_agent.generate_code("Write a Python function to add two numbers.", validation_rules="Must use type hints and return type.")
    print("Generated Code:", code)


import os
import tempfile
import shutil
def test_admin_agent():
    temp_dir = tempfile.mkdtemp()
    sop_registry_db = os.path.join(temp_dir, "sop_registry_test.db")
    model_registry_db = os.path.join(temp_dir, "model_registry_test.db")
    # Initialize both DBs with the audit_events schema
    import sqlite3
    schema_path = os.path.join(os.path.dirname(__file__), "model_registry_test_schema.sql")
    for db_path in [sop_registry_db, model_registry_db]:
        conn = sqlite3.connect(db_path)
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
    worm = WORMStorage(db_path=sop_registry_db)
    admin_agent = AdminAgent(sop_registry_db, model_registry_db, worm)
    try:
        print("Testing AdminAgent.register_sop_version...")
        admin_agent.register_sop_version("v2.3-test", context_info="E2E test run.")
        print("Testing AdminAgent.register_model_version...")
        admin_agent.register_model_version("model-v2.3-test", context_info="E2E test run.")
    finally:
        worm.close()
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_llm_provider()
    test_integrity_agent()
    test_hitl_agent()
    test_code_agent()
    test_admin_agent()
    print("\nEnd-to-end test complete. Check WORM audit log for entries.")
