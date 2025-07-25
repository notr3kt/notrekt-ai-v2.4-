
"""
llm_provider.py - Abstracts LLM API calls to support multiple vendors and open-source models.
SOP-ARC-003
"""

import os
import requests
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LLMProvider:
    """
    Centralized provider for interacting with various Large Language Models.
    Manages API keys, model selection, and basic error handling.
    """
    _api_key = os.getenv("GEMINI_API_KEY", "")

    @classmethod
    def _make_api_call(cls, model_name: str, contents: list, generation_config: dict = None, response_schema: dict = None) -> str:
        """
        Internal method to make a generic API call to the Google Generative Language API.
        Adds retry logic for transient errors.
        """
        import time
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={cls._api_key}"
        payload = {"contents": contents}
        if generation_config:
            payload["generationConfig"] = generation_config
        if response_schema:
            payload["generationConfig"] = payload.get("generationConfig", {}) # Ensure generationConfig exists
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = response_schema
        headers = {'Content-Type': 'application/json'}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logging.info(f"Calling LLM: {model_name} with payload (truncated): {json.dumps(payload)[:200]}...")
                response = requests.post(api_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                result = response.json()
                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    text_response = result["candidates"][0]["content"]["parts"][0]["text"]
                    logging.info(f"LLM {model_name} call successful.")
                    return text_response
                else:
                    logging.warning(f"LLM {model_name} call successful but no content found in response: {result}")
                    return "[GAP: LLM response structure unexpected or empty]"
            except requests.exceptions.RequestException as e:
                logging.error(f"LLM {model_name} API call failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"[GAP: LLM API call error: {e}]"
            except json.JSONDecodeError as e:
                logging.error(f"LLM {model_name} API response not valid JSON: {e}")
                return f"[GAP: LLM API response error: Invalid JSON]"
            except Exception as e:
                logging.error(f"An unexpected error occurred during LLM {model_name} call: {e}")
                return f"[GAP: Unexpected LLM error: {e}]"

    @classmethod
    def generate_text(cls, prompt: str, model_type: str = "flash", generation_config: dict = None) -> str:
        """
        Generates text using the specified Gemini model.
        Args:
            prompt (str): The input prompt for the LLM.
            model_type (str): "flash" for gemini-1.5-flash (default), "pro" for gemini-1.5-pro.
            generation_config (dict, optional): Custom generation configuration.
        Returns:
            str: The generated text.
        """
        GEMINI_MODELS = {
            "flash": "gemini-1.5-flash",
            "pro": "gemini-1.5-pro"
        }
        model_name = GEMINI_MODELS.get(model_type, "gemini-1.5-flash")
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return cls._make_api_call(model_name, contents, generation_config)

    @classmethod
    def generate_structured_response(cls, prompt: str, response_schema: dict, model_type: str = "flash", generation_config: dict = None) -> str:
        """
        Generates a structured (JSON) response using the specified Gemini model.
        Args:
            prompt (str): The input prompt.
            response_schema (dict): The JSON schema for the desired response.
            model_type (str): "flash" or "pro".
            generation_config (dict, optional): Custom generation configuration.
        Returns:
            str: The generated JSON string.
        """
        GEMINI_MODELS = {
            "flash": "gemini-1.5-flash",
            "pro": "gemini-1.5-pro"
        }
        model_name = GEMINI_MODELS.get(model_type, "gemini-1.5-flash")
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        return cls._make_api_call(model_name, contents, generation_config, response_schema)

    @classmethod
    def generate_multimodal_response(cls, prompt: str, base64_image: str, mime_type: str = "image/png", model_type: str = "pro", generation_config: dict = None) -> str:
        """
        Generates a response from a multimodal prompt (text + image).
        Args:
            prompt (str): The text prompt.
            base64_image (str): Base64 encoded image data.
            mime_type (str): MIME type of the image (e.g., "image/png", "image/jpeg").
            model_type (str): "pro" for gemini-1.5-pro (default).
            generation_config (dict, optional): Custom generation configuration.
        Returns:
            str: The generated text response.
        """
        GEMINI_MODELS = {
            "flash": "gemini-1.5-flash",
            "pro": "gemini-1.5-pro"
        }
        model_name = GEMINI_MODELS.get(model_type, "gemini-1.5-pro")
        contents = [
            {"role": "user", "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": mime_type, "data": base64_image}}
            ]}
        ]
        return cls._make_api_call(model_name, contents, generation_config)
