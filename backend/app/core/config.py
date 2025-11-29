"""
Application configuration
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Configuration - store as string to avoid JSON parsing issues
    # Read directly from os.getenv to avoid pydantic_settings trying to parse as JSON
    # This bypasses pydantic_settings' automatic JSON parsing for List types
    CORS_ORIGINS_STR: str = os.getenv("CORS_ORIGINS", "*")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @computed_field
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS from string"""
        if self.CORS_ORIGINS_STR == "*":
            return ["*"]
        # Split comma-separated values
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]
    
    @computed_field
    @property
    def CORS_CREDENTIALS(self) -> bool:
        """Set credentials based on CORS_ORIGINS"""
        return self.CORS_ORIGINS_STR != "*"
    
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "xai")
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    XAI_MODEL: str = os.getenv("XAI_MODEL", "grok-beta")
    
    # Database
    PARTS_DATABASE_PATH: str = os.getenv("PARTS_DATABASE_PATH", "app/data/parts")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

