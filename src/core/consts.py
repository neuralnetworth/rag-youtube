
# paths
# CONFIG_PATH is deprecated - using .env file instead

# defaults
DEFAULT_DEBUG = 'false'
DEFAULT_DATABASE_PATH = 'rag-youtube.db'
DEFAULT_LLM = 'ollama'
DEFAULT_OLLAMA_URL = 'http://localhost:11434'
DEFAULT_OLLAMA_MODEL = 'mistral:latest'
DEFAULT_OPENAI_MODEL = 'gpt-3.5-turbo-1106'
DEFAULT_DB_PERSIST_DIR = 'db'
DEFAULT_EMBEDDINGS_MODEL = 'all-mpnet-base-v2'
DEFAULT_SPLIT_CHUNK_SIZE = 2500
DEFAULT_SPLIT_CHUNK_OVERLAP = 500
DEFAULT_CHAIN_TYPE = 'base'
DEFAULT_DOC_CHAIN_TYPE = 'stuff'
DEFAULT_RETRIEVER_TYPE = 'base'
DEFAULT_SEARCH_TYPE = 'similarity'
DEFAULT_MEMORY_TYPE = 'buffer'
DEFAULT_CUSTOM_PROMPTS = 'false'
DEFAULT_RETURN_SOURCES = 'false'
DEFAULT_SCORE_THRESHOLD = 0.25
DEFAULT_DOCUMENT_COUNT = 4

# costing
# https://openai.com/pricing
# GPT-4 Turbo as of 16-Jan-2024
COST_INPUT_TOKENS_1K = 0.01
COST_OUTPUT_TOKENS_1K = 0.03
