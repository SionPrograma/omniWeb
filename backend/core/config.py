import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniWeb Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Cors configuration
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Active modules list
    ACTIVE_MODULES: list[str] = ["idiomas-ia", "lingua", "reparto", "finanzas", "programacion", "musica"]


    class Config:
        case_sensitive = True

settings = Settings()
