# NOTREKT.AI Gemini LLM Integration

This document describes how to configure and use the Gemini LLM integration in NOTREKT.AI.

## 1. API Key Management
- **Never hardcode secrets.**
- Copy `.env.example` to `.env` and set your actual Gemini API key.
- The key is loaded securely using `python-dotenv`.

## 2. LLMProvider Usage
- All LLM calls must go through `app/utils/llm_provider.py`.
- Supports text, structured (JSON), and multimodal (text+image) prompts.
- Example usage:

```python
from app.utils.llm_provider import LLMProvider

response = LLMProvider.generate_text("What is the capital of France?")
```

## 3. Security & Auditability
- All LLM calls are logged for audit.
- API key is never exposed in logs or code.

## 4. Dependencies
- Install requirements:
  - `pip install requests python-dotenv`

## 5. Troubleshooting
- If you see `ImportError: requests could not be resolved`, run the install command above.
- Ensure `.env` is present and contains a valid key.

## 6. Compliance
- This integration follows open source and security best practices.
- See `SOP-ARC-003` for architecture details.

---
For further help, see the main README or contact the maintainers.
