"""
Fixed Local LLM Download Script using official Hugging Face patterns
"""
import os
import logging
from dotenv import load_dotenv
from huggingface_hub import login
import transformers
import torch

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def download_local_llms():
    """Download all required local LLMs using official patterns"""
    
    # Login to Hugging Face
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HF_API_KEY')
    if not hf_token:
        logging.error("No HF_TOKEN found in environment!")
        return False
    
    try:
        login(token=hf_token)
        logging.info("Successfully logged in to Hugging Face.")
    except Exception as e:
        logging.error(f"Failed to login to HF: {e}")
        return False
    
    # Models to download with official configurations
    models = [
        {
            "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
            "config": {
                "torch_dtype": torch.bfloat16,
                "device_map": "auto",
                "trust_remote_code": True
            }
        },
        {
            "name": "mistralai/Mistral-7B-Instruct-v0.3", 
            "config": {
                "torch_dtype": torch.float16,
                "device_map": "auto",
                "trust_remote_code": True
            }
        },
        {
            "name": "google/gemma-7b-it",
            "config": {
                "torch_dtype": torch.float16,
                "device_map": "auto", 
                "trust_remote_code": True
            }
        }
    ]
    
    success_count = 0
    
    for model_info in models:
        model_name = model_info["name"]
        config = model_info["config"]
        
        logging.info(f"Downloading {model_name} using official transformers pipeline...")
        
        try:
            # Use the official transformers pipeline approach (from Llama docs)
            pipeline = transformers.pipeline(
                "text-generation",
                model=model_name,
                model_kwargs=config
            )
            
            # Test the pipeline with a simple prompt
            test_prompt = [{"role": "user", "content": "Hello"}]
            outputs = pipeline(test_prompt, max_new_tokens=10)
            
            logging.info(f"[SUCCESS] {model_name} downloaded and tested successfully!")
            success_count += 1
            
        except Exception as e:
            logging.error(f"[ERROR] Failed to download {model_name}: {e}")
            
            # Fallback: Try just downloading without testing
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
                logging.info(f"Trying fallback download for {model_name}...")
                
                # Special handling for Llama 3.1 rope_scaling issue
                if "Llama-3.1" in model_name:
                    logging.info("Applying Llama 3.1 rope_scaling fix...")
                    model_config = AutoConfig.from_pretrained(model_name)
                    
                    # Fix the rope_scaling configuration
                    if hasattr(model_config, 'rope_scaling') and isinstance(model_config.rope_scaling, dict):
                        old_rope_scaling = model_config.rope_scaling
                        model_config.rope_scaling = {
                            'type': old_rope_scaling.get('rope_type', 'llama3'),
                            'factor': old_rope_scaling.get('factor', 8.0)
                        }
                        logging.info(f"Fixed rope_scaling: {model_config.rope_scaling}")
                    
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(model_name, config=model_config, torch_dtype=config["torch_dtype"], device_map=config["device_map"])
                else:
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=config["torch_dtype"], device_map=config["device_map"])
                
                logging.info(f"[SUCCESS] {model_name} downloaded via fallback method!")
                success_count += 1
                
            except Exception as e2:
                logging.error(f"[FAILED] Both methods failed for {model_name}: {e2}")
    
    logging.info(f"Download complete: {success_count}/{len(models)} models successful")
    return success_count == len(models)

if __name__ == "__main__":
    download_local_llms()
