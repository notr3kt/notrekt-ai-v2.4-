# Fix for BASE_DIR undefined
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#!/usr/bin/env python3
"""
NOTREKT.AI v2.0 - Configuration Management
Security-first configuration using environment variables and validation.
"""


import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Logger for config
logger = logging.getLogger("notrekt.config")

# Load environment variables from .env file
load_dotenv()

class Config:
    # Local LLM Model Paths
    MISTRAL_LOCAL_MODEL_PATH: str = os.getenv('MISTRAL_LOCAL_MODEL_PATH', os.path.abspath(os.path.join(BASE_DIR, '..', 'mistralai', 'Mistral-7B-Instruct-v0.3')))
    GEMMA_LOCAL_MODEL_PATH: str = os.getenv('GEMMA_LOCAL_MODEL_PATH', os.path.abspath(os.path.join(BASE_DIR, '..', 'google', 'gemma-7b-it')))
    """
    Centralized, security-first configuration management.
    All sensitive values must be loaded from environment variables.
    """
    

    # Security Configuration
    SECRET_KEY: str = os.getenv('NOTREKT_SECRET_KEY', 'INSECURE_DEFAULT_CHANGE_ME')
    ENVIRONMENT: str = os.getenv('NOTREKT_ENVIRONMENT', 'development')

    # Base directory for absolute path resolution
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # Local LLM Model Paths (must come after BASE_DIR)
    MISTRAL_LOCAL_MODEL_PATH: str = os.getenv('MISTRAL_LOCAL_MODEL_PATH', os.path.abspath(os.path.join(BASE_DIR, '..', 'mistralai', 'Mistral-7B-Instruct-v0.3')))
    GEMMA_LOCAL_MODEL_PATH: str = os.getenv('GEMMA_LOCAL_MODEL_PATH', os.path.abspath(os.path.join(BASE_DIR, '..', 'google', 'gemma-7b-it')))

    # Database Configuration  
    WORM_DB_PATH: str = os.path.abspath(os.getenv('NOTREKT_WORM_DB_PATH', os.path.join(BASE_DIR, '..', 'data', 'notrekt_worm_audit.db')))

    # Rules Configuration
    # Always use the correct config/rules.json path unless explicitly overridden
    _default_rules_path = os.path.abspath(os.path.join(BASE_DIR, '..', 'config', 'rules.json'))
    RULES_PATH: str = os.path.abspath(os.getenv('NOTREKT_RULES_PATH', _default_rules_path))
    logger.info(f"[Config] Using RULES_PATH: {RULES_PATH}")

    # RAG System Configuration
    CORPUS_PATH: str = os.path.abspath(os.getenv('NOTREKT_CORPUS_PATH', os.path.join(BASE_DIR, '..', 'trusted_knowledge_corpus')))
    VECTOR_DB_PATH: str = os.path.abspath(os.getenv('NOTREKT_VECTOR_DB_PATH', os.path.join(BASE_DIR, '..', 'data', 'vector_store')))
    
    # API Configuration
    API_HOST: str = os.getenv('NOTREKT_API_HOST', 'localhost')
    API_PORT: int = int(os.getenv('NOTREKT_API_PORT', '8000'))
    API_DEBUG: bool = os.getenv('NOTREKT_API_DEBUG', 'false').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('NOTREKT_LOG_LEVEL', 'INFO')
    LOG_PATH: str = os.getenv('NOTREKT_LOG_PATH', './logs/notrekt.log')
    
    @classmethod
    def validate_config(cls) -> tuple[bool, list[str]]:
        """
        Validate configuration and return (is_valid, errors).
        Performs security checks and ensures required files exist.
        """
        errors = []
        
        # Security validations
        if cls.SECRET_KEY == 'INSECURE_DEFAULT_CHANGE_ME':
            errors.append("CRITICAL: Using default SECRET_KEY. Set NOTREKT_SECRET_KEY environment variable.")
        
        if len(cls.SECRET_KEY) < 32:
            errors.append("CRITICAL: SECRET_KEY must be at least 32 characters long.")
        
        # Path validations
        config_dir = Path(cls.RULES_PATH).parent
        if not config_dir.exists():
            errors.append(f"CRITICAL: Config directory does not exist: {config_dir}")
        
        if not Path(cls.RULES_PATH).exists():
            errors.append(f"CRITICAL: Rules file not found: {cls.RULES_PATH}")
        
        # Create required directories
        for path in [cls.WORM_DB_PATH, cls.VECTOR_DB_PATH, cls.LOG_PATH]:
            directory = Path(path).parent
            directory.mkdir(parents=True, exist_ok=True)
        
        corpus_path = Path(cls.CORPUS_PATH)
        corpus_path.mkdir(parents=True, exist_ok=True)
        
        return len(errors) == 0, errors
    
    @classmethod
    def setup_logging(cls):
        """Configure logging based on configuration."""
        log_dir = Path(cls.LOG_PATH).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(cls.LOG_PATH),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger("notrekt")

# Initialize logging
logger = Config.setup_logging()
