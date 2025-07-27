import os
import json
import logging
from dotenv import load_dotenv

# Import for Google Generative AI API
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None
    GenerationConfig = None
    HarmCategory = None
    HarmBlockThreshold = None
    print("[WARNING] google.generativeai not installed. Gemini API features will be unavailable.")

# Import for local Hugging Face models
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    import torch # Assuming PyTorch backend for transformers
    logging.info("Hugging Face Transformers and PyTorch imported successfully for local models.")
except ImportError:
    logging.warning("Hugging Face Transformers or PyTorch not found. Local LLM functionality will be disabled.")
    AutoModelForCausalLM = None
    AutoTokenizer = None
    pipeline = None
    torch = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LLMProvider:
    """
    Centralized provider for interacting with various Large Language Models.
    Supports both Google Gemini API and locally hosted Hugging Face models.
    """
    
    _initialized_genai = False
    _local_models = {} # Cache for loaded local models and tokenizers

    @classmethod
    def _initialize_genai(cls):
        """Initializes the Google Generative AI client with the API key."""
        if not cls._initialized_genai:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY", "")

            if not api_key:
                logging.warning("GEMINI_API_KEY is not set. Google Gemini API functionality will be disabled.")
                return False

            try:
                genai.configure(api_key=api_key)
                cls._initialized_genai = True
                logging.info("Google Generative AI client configured successfully.")
                return True

            except Exception as e:
                logging.critical(f"Failed to configure Google Generative AI client: {e}")
                return False

    @classmethod
    def _load_local_model(cls, local_model_path: str):
        """
        Loads a local Hugging Face model and tokenizer into memory.
        Caches them for subsequent use.
        """
        if local_model_path in cls._local_models:
            logging.info(f"Local model '{local_model_path}' already loaded from cache.")
            return cls._local_models[local_model_path]

        if AutoModelForCausalLM is None or AutoTokenizer is None or torch is None:
            logging.error("Hugging Face Transformers or PyTorch not available. Cannot load local model.")
            return None, None

        if not os.path.exists(local_model_path):
            logging.error(f"Local model path '{local_model_path}' does not exist. Cannot load model.")
            return None, None

        try:
            logging.info(f"Loading local model and tokenizer from '{local_model_path}'...")
            tokenizer = AutoTokenizer.from_pretrained(local_model_path, trust_remote_code=True)
            # Use `torch_dtype=torch.bfloat16` or `torch.float16` for memory efficiency if GPU is available
            # Use `device_map="auto"` to offload to CPU/disk if GPU VRAM is insufficient
            model = AutoModelForCausalLM.from_pretrained(
                local_model_path,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else None, # Use bfloat16 if CUDA is available for memory
                device_map="auto", # Automatically distributes model layers across available devices (GPU, CPU, disk)
                trust_remote_code=True # Required for some models like Llama 3.1
            )
            model.eval() # Set model to evaluation mode

            cls._local_models[local_model_path] = (model, tokenizer)
            logging.info(f"Local model '{local_model_path}' loaded successfully.")
            return model, tokenizer
        except Exception as e:
            logging.error(f"Failed to load local model from '{local_model_path}': {e}")
            return None, None

    @classmethod
    async def _make_api_call(cls, model_name: str, contents: list, generation_config: dict = None, response_schema: dict = None) -> str:
        """
        Internal asynchronous method to make a generic API call to a Gemini model.
        """
        if not cls._initialized_genai:
            if not cls._initialize_genai():
                return "[GAP: Google Gemini API not initialized due to missing/invalid API key]"

        try:
            model = genai.GenerativeModel(model_name)
            gen_config_obj = GenerationConfig(**generation_config) if generation_config else GenerationConfig()
            
            safety_settings = [
                {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
                {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
            ]

            if response_schema:
                gen_config_obj.response_mime_type = "application/json"
                gen_config_obj.response_schema = response_schema
            
            logging.info(f"Calling LLM API: {model_name}...")
            response = await model.generate_content_async(
                contents=contents,
                generation_config=gen_config_obj,
                safety_settings=safety_settings
            )
            
            if response.candidates:
                text_response = response.candidates[0].content.parts[0].text
                logging.info(f"LLM API {model_name} call successful.")
                return text_response
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                logging.warning(f"LLM API {model_name} prompt blocked: {response.prompt_feedback.block_reason}")
                return f"[GAP: LLM API Prompt Blocked: {response.prompt_feedback.block_reason}]"
            else:
                logging.warning(f"LLM API {model_name} call successful but no content found in response: {response.text}")
                return "[GAP: LLM API response structure unexpected or empty]"

        except genai.types.BlockedPromptException as e:
            logging.error(f"LLM API {model_name} prompt blocked by safety settings: {e}")
            return f"[GAP: LLM API Prompt Blocked by Safety: {e}]"
        except genai.types.StopCandidateException as e:
            logging.warning(f"LLM API {model_name} generation stopped prematurely: {e}")
            return f"[GAP: LLM API Generation Stopped: {e}]"
        except Exception as e:
            logging.error(f"An unexpected error occurred during LLM API {model_name} call: {e}")
            return f"[GAP: Unexpected LLM API error: {e}]"

    @classmethod
    async def _make_local_inference(cls, model_path: str, prompt: str, generation_config: dict = None) -> str:
        """
        Internal asynchronous method to perform inference with a locally loaded Hugging Face model.
        """
        model, tokenizer = cls._local_models.get(model_path, (None, None))
        if model is None or tokenizer is None:
            model, tokenizer = cls._load_local_model(model_path)
            if model is None or tokenizer is None:
                return f"[GAP: Local model '{model_path}' not loaded. Check logs for errors.]"

        try:
            logging.info(f"Performing local inference with model: {model_path}...")
            
            # Prepare chat template for instruction-tuned models
            messages = [{"role": "user", "content": prompt}]
            input_ids = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            )
            
            # Move input_ids to GPU if available
            if torch and torch.cuda.is_available():
                input_ids = input_ids.to(model.device)

            # Generate response (blocking operation, run in executor for async compatibility)
            # This is where the local model's speed limitations will be most apparent
            import asyncio
            loop = asyncio.get_running_loop()
            
            # Default generation parameters
            max_new_tokens = generation_config.get("max_output_tokens", 1024) if generation_config else 1024
            temperature = generation_config.get("temperature", 0.7) if generation_config else 0.7
            top_k = generation_config.get("top_k", 50) if generation_config else 50
            top_p = generation_config.get("top_p", 0.95) if generation_config else 0.95

            output_ids = await loop.run_in_executor(
                None, # Use default ThreadPoolExecutor
                lambda: model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    do_sample=True if temperature > 0 else False, # Only sample if temperature > 0
                    pad_token_id=tokenizer.eos_token_id # Important for generation
                )
            )
            
            response_text = tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True)
            logging.info(f"Local inference with '{model_path}' successful.")
            return response_text
        except Exception as e:
            logging.error(f"An error occurred during local inference with '{model_path}': {e}")
            return f"[GAP: Local inference error: {e}]"

    @classmethod
    async def generate_text(cls, prompt: str, model_type: str = "flash", local_model_path: str = None, generation_config: dict = None) -> str:
        """
        Generates text using the specified LLM.
        Args:
            prompt (str): The input prompt for the LLM.
            model_type (str): "flash" for gemini-1.5-flash, "pro" for gemini-1.5-pro,
                              "local" if using a local_model_path.
            local_model_path (str, optional): Path to the locally downloaded Hugging Face model.
            generation_config (dict, optional): Custom generation configuration.
        Returns:
            str: The generated text.
        """
        if local_model_path and model_type == "local":
            return await cls._make_local_inference(local_model_path, prompt, generation_config)
        elif model_type in ["flash", "pro"]:
            model_name = "gemini-1.5-flash" if model_type == "flash" else "gemini-1.5-pro"
            contents = [{"role": "user", "parts": [{"text": prompt}]}]
            return await cls._make_api_call(model_name, contents, generation_config)
        else:
            return "[GAP: Invalid model_type or local_model_path not provided for local type.]"

    @classmethod
    async def generate_structured_response(cls, prompt: str, response_schema: dict, model_type: str = "flash", local_model_path: str = None, generation_config: dict = None) -> str:
        """
        Generates a structured (JSON) response using the specified LLM.
        Note: Local models' structured output capabilities depend on their fine-tuning.
        """
        if local_model_path and model_type == "local":
            # Local models often don't have native structured output. You'd prompt them for JSON.
            # This is a basic prompt for JSON, not a guaranteed structured output.
            json_prompt = f"{prompt}\n\nProvide the response strictly in JSON format matching this schema: {json.dumps(response_schema)}"
            return await cls._make_local_inference(local_model_path, json_prompt, generation_config)
        elif model_type in ["flash", "pro"]:
            model_name = "gemini-1.5-flash" if model_type == "flash" else "gemini-1.5-pro"
            contents = [{"role": "user", "parts": [{"text": prompt}]}]
            return await cls._make_api_call(model_name, contents, generation_config, response_schema)
        else:
            return "[GAP: Invalid model_type or local_model_path not provided for local type.]"

    @classmethod
    async def generate_multimodal_response(cls, prompt: str, base64_image: str, mime_type: str = "image/png", model_type: str = "pro", local_model_path: str = None, generation_config: dict = None) -> str:
        """
        Generates a response from a multimodal prompt (text + image).
        Note: Local multimodal models (like Gemma 3) need to be loaded correctly.
        """
        if local_model_path and model_type == "local":
            # Local multimodal models (like Gemma 3) are loaded via transformers
            # This requires the model to have a vision encoder.
            # The _make_local_inference currently only handles text-to-text.
            # [GAP: Implement multimodal inference for local models]
            logging.error("Local multimodal inference is not yet implemented.")
            return "[GAP: Local multimodal inference not supported yet.]"
        elif model_type in ["pro"]: # Only Gemini Pro currently supports multimodal via API
            model_name = "gemini-1.5-pro"
            contents = [
                {"role": "user", "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": base64_image}}
                ]}
            ]
            return await cls._make_api_call(model_name, contents, generation_config)
        else:
            return "[GAP: Invalid model_type or local_model_path not provided for local type.]"


# Example usage (for testing purposes, remove in production main.py)
if __name__ == "__main__":
    import asyncio
    import base64

    # Define paths to your downloaded models
    # IMPORTANT: Adjust these paths to where your models are actually downloaded!
    # Example: If downloaded to C:\Users\asus\OneDrive\Desktop\NOTREKT v2.0\NOTREKT-AI-v2.4\mistralai\Mistral-7B-Instruct-v0.3

    MISTRAL_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mistralai", "Mistral-7B-Instruct-v0.3")

    def _call_localai(prompt: str, **kwargs) -> str:
        """
        Calls LocalAI API (open-source, local LLM server), with retry logic.
        """
        import time
        import logging
        max_retries = 3
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": kwargs.get("model", "llama2"),
                    "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", 512),
                    "temperature": kwargs.get("temperature", 0.7)
                }
                headers = {"Content-Type": "application/json"}
                # Simulate a result for demonstration
                simulated_result = {"choices": [{"text": "[Simulated LocalAI response]"}]}
                return simulated_result.get("choices", [{}])[0].get("text", "[GAP: LocalAI response missing]")
            except Exception as e:
                logging.warning(f"LocalAI call failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logging.error(f"LocalAI call permanently failed: {e}")
                    return f"[GAP: LocalAI error: {e}]"

    def _call_hf(prompt: str, **kwargs) -> str:
        """
        Calls Hugging Face Inference API, with retry logic.
        """
        import time
        import logging
        max_retries = 3
        hf_model = kwargs.get("hf_model", "")
        hf_api_key = kwargs.get("hf_api_key", "")
        for attempt in range(max_retries):
            try:
                api_url = f"https://api-inference.huggingface.co/models/{hf_model}"
                headers = {"Authorization": f"Bearer {hf_api_key}", "Content-Type": "application/json"}
                payload = {"inputs": prompt}
                # Simulate a result for demonstration
                simulated_result = [{"generated_text": "[Simulated HF response]"}]
                if isinstance(simulated_result, list) and simulated_result and "generated_text" in simulated_result[0]:
                    return simulated_result[0]["generated_text"]
                elif isinstance(simulated_result, dict) and "error" in simulated_result:
                    return f"[GAP: HF error: {simulated_result['error']}]"
                else:
                    return str(simulated_result)
            except Exception as e:
                logging.warning(f"Hugging Face call failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logging.error(f"Hugging Face call permanently failed: {e}")
                    return f"[GAP: Hugging Face error: {e}]"


