"""
Simple, robust LLM downloader - minimal approach
"""
import os
from dotenv import load_dotenv
from huggingface_hub import login

# Load environment
load_dotenv()

# Login to Hugging Face
hf_token = os.getenv('HF_TOKEN') or os.getenv('HF_API_KEY')
if hf_token:
    login(token=hf_token)
    print("[INFO] Logged in to Hugging Face")
else:
    print("[ERROR] No HF_TOKEN found!")
    exit(1)

# Simple download function
def download_model(model_name):
    print(f"\n=== Downloading {model_name} ===")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
        
        # Download tokenizer first
        print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✅ Tokenizer downloaded")
        
        # Special handling for Llama 3.1 rope_scaling issue
        if "Llama-3.1" in model_name:
            print("🔧 Applying Llama 3.1 configuration fix...")
            config = AutoConfig.from_pretrained(model_name)
            
            # Fix the rope_scaling configuration by removing problematic fields
            if hasattr(config, 'rope_scaling') and isinstance(config.rope_scaling, dict):
                original = config.rope_scaling.copy()
                print(f"Original rope_scaling: {original}")
                
                # Keep only the two required fields
                config.rope_scaling = {
                    'type': original.get('rope_type', 'default'),
                    'factor': original.get('factor', 8.0)
                }
                print(f"Fixed rope_scaling: {config.rope_scaling}")
            
            # Download model with fixed config
            print("Downloading model with fixed configuration...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                config=config,
                torch_dtype="auto",
                device_map="cpu",
                low_cpu_mem_usage=True
            )
        else:
            # Download model with minimal config for other models
            print("Downloading model...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map="cpu",
                low_cpu_mem_usage=True
            )
        
        print(f"✅ SUCCESS: {model_name} downloaded!")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {model_name} - {e}")
        return False

# Download models one by one
models = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "google/gemma-2-9b-it",  # Updated to Gemma 2 (more stable than the 12B version)
    "meta-llama/Meta-Llama-3.1-8B-Instruct"
]

success = 0
for model in models:
    if download_model(model):
        success += 1

print(f"\n🎯 FINAL RESULT: {success}/{len(models)} models downloaded successfully!")

if success == len(models):
    print("🚀 ALL MODELS READY! NOTREKT.AI v2.4 is complete!")
else:
    print("⚠️  Some models failed, but you can still use the successful ones.")
