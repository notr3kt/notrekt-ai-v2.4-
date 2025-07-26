# NOTREKT.AI v2.3 (Latest Development Release)

**This is the latest development version of NOTREKT.AI, based on the open source release.**

**Next-Generation AI Governance, Audit, and Compliance System**

---

## Overview
NOTREKT.AI v2.3 is a production-grade, modular, and fully auditable AI governance platform. It features:
- Secure, cryptographically chained WORM audit logging
- Human-in-the-Loop (HITL) workflows
- Modular agent architecture (governance, code, research, integrity, HITL)
- Zero-guessing RAG system with trusted knowledge corpus
- Full SOP-driven compliance and auditability

## Key Features
- **Governance Core:** Enforces rules, risk tiers, and approvals
- **WORM Storage:** Tamper-proof, immutable audit trail
- **HITL:** Human approvals for high-risk actions
- **RAG System:** Retrieval-augmented generation with source verification
- **Modular Agents:** Extensible for code, research, admin, and more
- **Comprehensive SOPs:** All protocols and governance logic documented

## Getting Started
1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see `.env.example`)
4. Run the app: `python -m app.main`

## Installation

1. Create and activate a Python virtual environment (venv recommended):
   - Windows:
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. If you use `faiss-cpu` or `faiss-gpu`, ensure your hardware/OS supports it. For GPU acceleration, install `faiss-gpu` as needed and document any extra steps.

4. Set up your `.env` file with required API keys (see `.env.example` if provided).

5. Run your main app or tests as needed.

## Brutal Checklist
- No import errors in any file, ever.
- `requirements.txt` includes every used external library.
- This README contains all steps for a clean install and run.

## Documentation
- See the `SOPs/` directory for all Standard Operating Procedures
- See `AUDIT_LOG.md` for a full audit trail of all codebase changes

## License
MIT License

---

*For more details, see the Master SOP and in-code documentation.*

---

## Version Summary & Next Steps

**v2.1:** A strong, modular prototype with core features and some [GAP]s.

**v2.2:** A clean, open source–ready, governance-compliant release with improved documentation, explicit [GAP] tracking, and a structure that’s easier for new users, contributors, and auditors.


**v2.3 Progress & Remaining Priorities:**
The following are now complete:
- WORM storage integrity is robust and cryptographically chained
- All audit events are digitally signed and verified
- In-memory state is fully migrated to persistent storage
- Core cryptographic and audit features are production-grade

Remaining priorities for a production-ready v2.3:
- Finalize and harden RAG and VerifierAgent logic
- Systematically fill any remaining [GAP]s in agent and utility modules
- Conduct full-system integration and security review

This will ensure NOTREKT.AI delivers on its promise of “brutal governance,” auditability, and security.
