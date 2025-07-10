import os
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass

from . import consts


class Config:
    """Configuration manager that reads from environment variables with fallbacks."""
    
    def __init__(self, path=None):
        # Legacy: path parameter kept for backward compatibility but ignored
        # All configuration now comes from environment variables
        pass
    
    def _get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default."""
        return os.getenv(key, default)
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        value = self._get_env(key, str(default).lower())
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Get environment variable as integer."""
        value = self._get_env(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_env_float(self, key: str, default: float) -> float:
        """Get environment variable as float."""
        value = self._get_env(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    # General settings
    def debug(self) -> bool:
        return self._get_env_bool('DEBUG', False)
    
    def database_path(self) -> str:
        return self._get_env('DATABASE_PATH', consts.DEFAULT_DATABASE_PATH)
    
    # LangChain settings
    def langchain_api_key(self) -> Optional[str]:
        return self._get_env('LANGCHAIN_API_KEY')
    
    def langchain_project(self) -> Optional[str]:
        return self._get_env('LANGCHAIN_PROJECT')
    
    # LLM settings
    def llm(self) -> str:
        # Map from new LLM_PROVIDER to legacy llm values
        provider = self._get_env('LLM_PROVIDER', 'openai').lower()
        if provider == 'gemini':
            return 'openai'  # Use OpenAI infrastructure for Gemini
        return provider
    
    def llm_provider(self) -> str:
        """Get the actual LLM provider (openai, gemini)."""
        return self._get_env('LLM_PROVIDER', 'openai').lower()
    
    # OpenAI settings
    def openai_api_key(self) -> Optional[str]:
        return self._get_env('OPENAI_API_KEY')
    
    def openai_org_id(self) -> Optional[str]:
        return self._get_env('OPENAI_ORG_ID')
    
    def openai_model(self) -> str:
        return self._get_env('OPENAI_MODEL', consts.DEFAULT_OPENAI_MODEL)
    
    # Gemini settings
    def gemini_api_key(self) -> Optional[str]:
        return self._get_env('GEMINI_API_KEY')
    
    def gemini_model(self) -> str:
        return self._get_env('GEMINI_MODEL', 'gemini-1.5-flash')
    
    # Ollama settings (legacy)
    def ollama_url(self) -> str:
        return self._get_env('OLLAMA_URL', consts.DEFAULT_OLLAMA_URL)
    
    def ollama_model(self) -> str:
        return self._get_env('OLLAMA_MODEL', consts.DEFAULT_OLLAMA_MODEL)
    
    # Embeddings settings
    def embeddings_provider(self) -> str:
        return self._get_env('EMBEDDINGS_PROVIDER', 'openai')
    
    def embeddings_model(self) -> str:
        # If using OpenAI embeddings
        if self.embeddings_provider() == 'openai':
            return self._get_env('EMBEDDINGS_MODEL', 'text-embedding-3-small')
        # Default for other providers
        return self._get_env('EMBEDDINGS_MODEL', consts.DEFAULT_EMBEDDINGS_MODEL)
    
    # Vector store settings
    def db_persist_directory(self) -> str:
        return self._get_env('DB_PERSIST_DIR', consts.DEFAULT_DB_PERSIST_DIR)
    
    # Text splitter settings
    def split_chunk_size(self) -> int:
        return self._get_env_int('SPLIT_CHUNK_SIZE', consts.DEFAULT_SPLIT_CHUNK_SIZE)
    
    def split_chunk_overlap(self) -> int:
        return self._get_env_int('SPLIT_CHUNK_OVERLAP', consts.DEFAULT_SPLIT_CHUNK_OVERLAP)
    
    # Search settings
    def chain_type(self) -> str:
        return self._get_env('CHAIN_TYPE', consts.DEFAULT_CHAIN_TYPE)
    
    def doc_chain_type(self) -> str:
        return self._get_env('DOC_CHAIN_TYPE', consts.DEFAULT_DOC_CHAIN_TYPE)
    
    def search_type(self) -> str:
        return self._get_env('SEARCH_TYPE', consts.DEFAULT_SEARCH_TYPE)
    
    def retrieve_type(self) -> str:
        return self._get_env('RETRIEVE_TYPE', consts.DEFAULT_RETRIEVER_TYPE)
    
    def memory_type(self) -> str:
        return self._get_env('MEMORY_TYPE', consts.DEFAULT_MEMORY_TYPE)
    
    def custom_prompts(self) -> bool:
        return self._get_env_bool('CUSTOM_PROMPTS', False)
    
    def return_sources(self) -> bool:
        return self._get_env_bool('RETURN_SOURCES', False)
    
    def score_threshold(self) -> float:
        return self._get_env_float('SCORE_THRESHOLD', consts.DEFAULT_SCORE_THRESHOLD)
    
    def document_count(self) -> int:
        return self._get_env_int('DOCUMENT_COUNT', consts.DEFAULT_DOCUMENT_COUNT)