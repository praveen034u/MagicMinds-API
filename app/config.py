"""Application configuration."""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    PORT: int = 8080
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_AUDIENCE: str
    AUTH0_ISSUER: str
    AUTH0_JWKS_URL: str
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # GCP
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    
    # Stripe (optional)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
