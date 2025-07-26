import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

print('GEMINI_API_KEY:', os.getenv('GEMINI_API_KEY'))
print('HF_API_KEY:', os.getenv('HF_API_KEY'))
print('GOOGLE_PICKER_API_KEY:', os.getenv('GOOGLE_PICKER_API_KEY'))

print('NOTREKT_SECRET_KEY:', os.getenv('NOTREKT_SECRET_KEY'))
print('NOTREKT_API_KEY:', os.getenv('NOTREKT_API_KEY'))
print('NOTREKT_ENV:', os.getenv('NOTREKT_ENV'))
