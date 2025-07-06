"""
FastAPI-specific configuration settings.
"""
import os
from typing import List


class FastAPIConfig:
    """Configuration for FastAPI application."""
    
    # Server settings
    HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    RELOAD: bool = os.getenv("FASTAPI_RELOAD", "false").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ]
    
    # API settings
    API_TITLE: str = "RAG-YouTube API"
    API_DESCRIPTION: str = "API for querying YouTube video content using RAG"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Static files
    STATIC_DIR: str = "static"
    STATIC_URL: str = "/static"
    
    # Rate limiting (requests per minute)
    RATE_LIMIT: int = 60
    
    # Streaming settings
    STREAM_CHUNK_SIZE: int = 1024
    STREAM_TIMEOUT: int = 60  # seconds
    
    # Cache settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_static_path(cls) -> str:
        """Get absolute path to static directory."""
        # Get the path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, cls.STATIC_DIR)