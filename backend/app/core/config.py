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
    # pydantic_settings will read CORS_ORIGINS env var and map it to this field
    # We use a different field name to avoid List[str] type parsing
    CORS_ORIGINS_STR: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Map CORS_ORIGINS env var to CORS_ORIGINS_STR field
        fields = {
            "CORS_ORIGINS_STR": {"env": "CORS_ORIGINS"}
        }
    
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

