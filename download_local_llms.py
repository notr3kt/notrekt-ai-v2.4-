"""
download_local_llms.py - Pre-download all required local LLMs for NOTREKT.AI v2.4

This script will download and cache Gemma-7B, Llama-3-8B, and Mistral-7B from Hugging Face for offline use.
Requires: transformers, torch, and a valid Hugging Face token (HF_TOKEN or HF_API_KEY in .env)

Usage:
    python download_local_llms.py
"""
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login as hf_login
from dotenv import load_dotenv

# --- Load .env if present ---
load_dotenv()

hf_token = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY")
if hf_token:
    try:
        hf_login(token=hf_token)
        print("[INFO] Successfully logged in to Hugging Face.")
    except Exception as e:
        print(f"[WARN] Hugging Face login failed: {e}")
else:
    print("[WARN] No Hugging Face token found in HF_TOKEN or HF_API_KEY. Model downloads may fail.")

models = [
    "google/gemma-7b-it",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

# --- Paging File Warning for Windows Users ---
if os.name == 'nt':
    print("[WARN] Windows Users: If you see an error like 'The paging file is too small',")
    print("        it means your system is running out of virtual memory. This is common")
    print("        when downloading large models like Mistral (~15GB).")
    print("        To fix this, you need to increase your system's page file size.")
    print("        Search for 'Adjust the appearance and performance of Windows' ->")
    print("        'Advanced' tab -> 'Virtual memory' section, click 'Change...' ->")
    print("        Uncheck 'Automatically manage...' and set a larger custom size.")
    print("        A size of 32GB (32768 MB) or more is recommended.")
    print("-" * 70)


for model_name in models:
    print(f"Downloading {model_name} ...")
    if "meta-llama" in model_name:
        print(f"[INFO] {model_name} is a gated model. Please ensure you have been granted access on Hugging Face.")
    try:
        if "gemma" in model_name:
            print("[INFO] Downloading Gemma with compatibility fixes...")
            try:
                # Try with default configuration first
                AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True, torch_dtype="auto")
            except Exception as e:
                print(f"[INFO] Default approach failed, trying with config patches: {e}")
                # Fallback: Try various config modifications
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(model_name)
                
                # Try different activation function fixes
                for activation in ["gelu_pytorch_tanh", "gelu", "gelu_new", "swish"]:
                    try:
                        config.hidden_activation = activation
                        print(f"[INFO] Trying activation function: {activation}")
                        AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                        AutoModelForCausalLM.from_pretrained(model_name, config=config, trust_remote_code=True)
                        print(f"[SUCCESS] Gemma downloaded with activation: {activation}")
                        break
                    except Exception as inner_e:
                        print(f"[DEBUG] Failed with {activation}: {inner_e}")
                        continue
                else:
                    # If all activation functions fail, try downloading without config
                    print("[INFO] All config patches failed, downloading with minimal config...")
                    AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                    AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
        elif "Llama-3.1" in model_name:
            # Alternative approach: Download without config modifications
            # Let the model handle its own configuration
            print("[INFO] Downloading Llama 3.1 with default configuration handling...")
            try:
                AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                # Use torch_dtype to reduce memory usage and avoid config issues
                AutoModelForCausalLM.from_pretrained(
                    model_name, 
                    trust_remote_code=True,
                    torch_dtype="auto",
                    device_map="auto"
                )
            except Exception as e:
                print(f"[INFO] First attempt failed, trying with config patch: {e}")
                # Fallback: Try with minimal config modification
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(model_name)
                if hasattr(config, "rope_scaling"):
                    # Remove rope_scaling entirely to let the model use defaults
                    delattr(config, "rope_scaling")
                    print("[INFO] Removed problematic rope_scaling configuration")
                AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                AutoModelForCausalLM.from_pretrained(model_name, config=config, trust_remote_code=True)
        else:
            AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
        print(f"[SUCCESS] Successfully downloaded {model_name}")
    except Exception as e:
        print(f"[ERROR] Failed to download {model_name}: {e}")
print("All local LLMs attempted. Check above for any errors.")
