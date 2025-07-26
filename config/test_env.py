import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

print('GEMINI_API_KEY:', os.getenv('GEMINI_API_KEY'))
print('HF_API_KEY:', os.getenv('HF_API_KEY'))
print('GOOGLE_PICKER_API_KEY:', os.getenv('GOOGLE_PICKER_API_KEY'))
