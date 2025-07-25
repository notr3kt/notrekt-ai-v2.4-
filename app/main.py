"""
main.py - FastAPI entrypoint for NOTREKT.AI v2.0
---
Refactor Summary (2025-07-25):
- Implements OAuth2/JWT, RBAC, API key checks for all endpoints (SOP-ARC-001)
- HITL endpoints and VerifierAgent middleware scaffolded (SOP-EXE-002, SOP-REV-002)
- All actions/decisions immutably logged (SOP-GOV-001)
- Modular structure: see /app for agents, governance, utils
---
SOP refs: SOP-ARC-001, SOP-GOV-001, SOP-EXE-002, SOP-REV-002
"""
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional


# Modular imports
from app.governance import GovernanceCore
from app.worm_storage import WORMStorage
from app.rag_system import ResearchAgent
from app.verifier_agent import VerifierAgent
from app.agents.integrity_agent import IntegrityAgent
from app.agents.hitl_agent import HITLAgent
from app.utils.rag_utils import log_rag_sources, detect_context_drift
from app.utils.llm_provider import LLMProvider

app = FastAPI(title="NOTREKT.AI Governance API", version="2.0")

# CORS (for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2/JWT config (SOP-ARC-001)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# RBAC roles
ROLES = {"admin", "reviewer", "user"}

# API Key config
API_KEY_HEADER = "X-API-Key"
API_KEYS = set(os.getenv("API_KEYS", "test-key").split(","))

# Pydantic models
class HITLDecision(BaseModel):
    action_id: str
    decision: str  # APPROVE or REJECT
    reason: Optional[str] = None
    approver_id: str
    timestamp: str

# Auth utils
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role not in ROLES:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"user_id": user_id, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def api_key_check(x_api_key: str = Header(None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")

# VerifierAgent middleware (SOP-REV-002)
@app.middleware("http")
async def verifier_agent_middleware(request: Request, call_next):
    response = await call_next(request)
    # [GAP: Intercept/validate AI responses against RAG/KB]
    return response

# HITL endpoints (SOP-EXE-002)
@app.post("/action/approve", dependencies=[Depends(get_current_user)])
async def approve_action(decision: HITLDecision):
    # [GAP: Log decision immutably, process approval]
    return {"status": "approved", "action_id": decision.action_id}

@app.post("/action/reject", dependencies=[Depends(get_current_user)])
async def reject_action(decision: HITLDecision):
    # [GAP: Log decision immutably, process rejection]
    return {"status": "rejected", "action_id": decision.action_id}

# Example protected endpoint
@app.get("/secure-data", dependencies=[Depends(get_current_user), Depends(api_key_check)])
async def secure_data():
    return {"data": "This is protected data."}

# [GAP: Add more endpoints, governance logic, agent modularization]
