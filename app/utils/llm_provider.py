
# ...existing imports and code...

class LLMProvider:

    @classmethod
    def generate_text(cls, prompt: str, model_type: str = "flash", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for text generation.
        model_type: "flash"/"pro" for Gemini, or ignored for local models.
        backend: "gemini", "gemma", "llama", "mistral", etc.
        """
        if backend is None and model_type in ("flash", "pro"):
            backend = "gemini"
        provider = cls()
        return provider.generate(prompt, backend=backend or "gemini", model_type=model_type, **kwargs)

    @classmethod
    def generate_structured_response(cls, prompt: str, response_schema: dict, model_type: str = "flash", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for structured (JSON) response generation.
        """
        provider = cls()
        if backend is None and model_type in ("flash", "pro"):
            backend = "gemini"
        if backend == "gemini":
            return provider._call_gemini(prompt, model_type=model_type, response_schema=response_schema, **kwargs)
        else:
            import json
            result = provider.generate(prompt, backend=backend, model_type=model_type, **kwargs)
            try:
                return json.loads(result)
            except Exception:
                return result

    @classmethod
    def generate_multimodal_response(cls, prompt: str, base64_image: str, mime_type: str = "image/png", model_type: str = "pro", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for multimodal (text+image) response generation.
        Only Gemini supports this for now.
        """
        provider = cls()
        if backend is None:
            backend = "gemini"
        if backend == "gemini":
            return provider._call_gemini(prompt, model_type=model_type, base64_image=base64_image, mime_type=mime_type, **kwargs)
        else:
            return "[GAP: Multimodal not supported for backend: {}]".format(backend)

"""
llm_provider.py - Abstracts LLM API calls to support multiple vendors and open-source models.
SOP-ARC-003
"""

import os
from huggingface_hub import login as hf_login
import requests
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LLMProvider:

    @classmethod
    def generate_text(cls, prompt: str, model_type: str = "flash", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for text generation.
        model_type: "flash"/"pro" for Gemini, or ignored for local models.
        backend: "gemini", "gemma", "llama", "mistral", etc.
        """
        # Default: Gemini for flash/pro, else use backend
        if backend is None and model_type in ("flash", "pro"):
            backend = "gemini"
        provider = cls()
        return provider.generate(prompt, backend=backend or "gemini", model_type=model_type, **kwargs)

    @classmethod
    def generate_structured_response(cls, prompt: str, response_schema: dict, model_type: str = "flash", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for structured (JSON) response generation.
        """
        provider = cls()
        if backend is None and model_type in ("flash", "pro"):
            backend = "gemini"
        # Only Gemini supports response_schema for now
        if backend == "gemini":
            return provider._call_gemini(prompt, model_type=model_type, response_schema=response_schema, **kwargs)
        else:
            # Fallback: generate text and try to parse as JSON
            import json
            result = provider.generate(prompt, backend=backend, model_type=model_type, **kwargs)
            try:
                return json.loads(result)
            except Exception:
                return result

    @classmethod
    def generate_multimodal_response(cls, prompt: str, base64_image: str, mime_type: str = "image/png", model_type: str = "pro", backend: str = None, **kwargs) -> str:
        """
        Backward-compatible static method for multimodal (text+image) response generation.
        Only Gemini supports this for now.
        """
        provider = cls()
        if backend is None:
            backend = "gemini"
        if backend == "gemini":
            return provider._call_gemini(prompt, model_type=model_type, base64_image=base64_image, mime_type=mime_type, **kwargs)
        else:
            return "[GAP: Multimodal not supported for backend: {}]".format(backend)
    """
    Centralized provider for interacting with various Large Language Models.
    Supports multiple backends: Gemini, Gemma, LocalAI, Hugging Face, etc.
    Manages API keys, model selection, and error handling.
    """

    def __init__(self):
        # Authenticate with Hugging Face if token is present
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            try:
                hf_login(token=hf_token)
            except Exception as e:
                logging.warning(f"Hugging Face login failed: {e}")
        # Load all API keys and endpoints from environment/config
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.localai_endpoint = os.getenv("LOCALAI_ENDPOINT", "http://localhost:8080/v1/completions")
        self.hf_api_key = os.getenv("HF_API_KEY", "")
        self.default_backend = os.getenv("LLM_BACKEND", "gemini")
        # Local model cache for efficient inference
        self._local_models = {}

    def generate(self, prompt: str, backend: str = None, **kwargs) -> str:
        """
        Unified interface for text generation across multiple LLM backends.
        Args:
            prompt (str): The input prompt for the LLM.
            backend (str): Which backend to use (gemini, gemma, localai, hf). Defaults to env LLM_BACKEND.
            kwargs: Additional backend-specific parameters.
        Returns:
            str: The generated text.
        """
        logging.info(f"Calling LLM: backend={backend or self.default_backend}, prompt={prompt[:60]}...")
        backend = backend or self.default_backend
        if backend == "gemini":
            return self._call_gemini(prompt, **kwargs)
        elif backend == "gemma":
            return self._call_gemma_local(prompt, **kwargs)
        elif backend == "llama":
            return self._call_llama_local(prompt, **kwargs)
        elif backend == "mistral":
            return self._call_mistral_local(prompt, **kwargs)
        elif backend == "localai":
            return self._call_localai(prompt, **kwargs)
        elif backend == "hf":
            return self._call_hf(prompt, **kwargs)
        else:
            logging.error(f"Unknown LLM backend: {backend}")
            return "[GAP: Unknown LLM backend]"

    def _call_gemini(self, prompt: str, model_type: str = "flash", generation_config: dict = None, response_schema: dict = None, base64_image: str = None, mime_type: str = "image/png") -> str:
        """
        Calls Gemini API (Google Generative Language).
        Supports text and multimodal (text+image).
        """
        import time
        GEMINI_MODELS = {
            "flash": "gemini-1.5-flash",
            "pro": "gemini-1.5-pro"
        }
        model_name = GEMINI_MODELS.get(model_type, "gemini-1.5-flash")
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"
        if base64_image:
            contents = [
                {"role": "user", "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": base64_image}}
                ]}
            ]
        else:
            contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload = {"contents": contents}
        if generation_config:
            payload["generationConfig"] = generation_config
        if response_schema:
            payload["generationConfig"] = payload.get("generationConfig", {})
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = response_schema
        headers = {'Content-Type': 'application/json'}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logging.info(f"Calling Gemini: {model_name} with payload (truncated): {json.dumps(payload)[:200]}...")
                response = requests.post(api_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                result = response.json()
                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    text_response = result["candidates"][0]["content"]["parts"][0]["text"]
                    logging.info(f"Gemini {model_name} call successful.")
                    return text_response
                else:
                    logging.warning(f"Gemini {model_name} call successful but no content found in response: {result}")
                    return "[GAP: Gemini response structure unexpected or empty]"
            except requests.exceptions.RequestException as e:
                logging.error(f"Gemini {model_name} API call failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"[GAP: Gemini API call error: {e}]"
            except json.JSONDecodeError as e:
                logging.error(f"Gemini {model_name} API response not valid JSON: {e}")
                return f"[GAP: Gemini API response error: Invalid JSON]"
            except Exception as e:
                logging.error(f"An unexpected error occurred during Gemini {model_name} call: {e}")
                return f"[GAP: Unexpected Gemini error: {e}]"


    def _call_gemma_local(self, prompt: str, **kwargs) -> str:
        """
        Local inference for Gemma-7B using Hugging Face transformers.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            model_name = "google/gemma-7b-it"
            if model_name not in self._local_models:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                self._local_models[model_name] = (tokenizer, model)
            tokenizer, model = self._local_models[model_name]
            inputs = tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=256)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Gemma-7B local inference failed: {e}")
            return f"[GAP: Gemma-7B local error: {e}]"

    def _call_llama_local(self, prompt: str, **kwargs) -> str:
        """
        Local inference for Llama-3-8B using Hugging Face transformers.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
            if model_name not in self._local_models:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                self._local_models[model_name] = (tokenizer, model)
            tokenizer, model = self._local_models[model_name]
            inputs = tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=256)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Llama-3-8B local inference failed: {e}")
            return f"[GAP: Llama-3-8B local error: {e}]"

    def _call_mistral_local(self, prompt: str, **kwargs) -> str:
        """
        Local inference for Mistral-7B using Hugging Face transformers.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            model_name = "mistralai/Mistral-7B-Instruct-v0.2"
            if model_name not in self._local_models:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                self._local_models[model_name] = (tokenizer, model)
            tokenizer, model = self._local_models[model_name]
            inputs = tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=256)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Mistral-7B local inference failed: {e}")
            return f"[GAP: Mistral-7B local error: {e}]"

    def _call_localai(self, prompt: str, **kwargs) -> str:
        """
        Calls LocalAI API (open-source, local LLM server).
        """
        try:
            payload = {
                "model": kwargs.get("model", "llama2"),
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7)
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.localai_endpoint, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "[GAP: LocalAI response missing]")
        except Exception as e:
            logging.error(f"LocalAI call failed: {e}")
            return f"[GAP: LocalAI error: {e}]"

    def _call_hf(self, prompt: str, **kwargs) -> str:
        """
        Calls Hugging Face Inference API.
        """
        try:
            api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            headers = {"Authorization": f"Bearer {self.hf_api_key}", "Content-Type": "application/json"}
            payload = {"inputs": prompt}
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and result and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "error" in result:
                return f"[GAP: HF error: {result['error']}]"
            else:
                return str(result)
        except Exception as e:
            logging.error(f"Hugging Face call failed: {e}")
            return f"[GAP: Hugging Face error: {e}]"
