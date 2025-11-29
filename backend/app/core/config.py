"""
Application configuration
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Configuration
    _cors_origins_env = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS: List[str] = _cors_origins_env.split(",") if _cors_origins_env != "*" else ["*"]
    # If CORS_ORIGINS is "*", credentials must be False (browser security)
    CORS_CREDENTIALS: bool = _cors_origins_env != "*"
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "xai")
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    XAI_MODEL: str = os.getenv("XAI_MODEL", "grok-beta")
    
    # Database
    PARTS_DATABASE_PATH: str = os.getenv("PARTS_DATABASE_PATH", "app/data/parts")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

