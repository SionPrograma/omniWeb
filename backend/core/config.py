import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniWeb Platform"
    VERSION: str = "0.4.4"
    API_V1_STR: str = "/api/v1"
    
    # Cors configuration
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Active modules list
    ACTIVE_MODULES: list[str] = ["idiomas-ia", "lingua", "reparto", "finanzas", "programacion", "musica"]

    # Database & Storage
    DATA_DIR: str = "backend/data"
    DATABASE_NAME: str = "omniweb.db"
    ADMIN_TOKEN: str = os.getenv("OMNIWEB_ADMIN_TOKEN", "omniweb-dev-secret-token")

    @property
    def DATABASE_URL(self) -> str:
        return os.path.join(self.DATA_DIR, self.DATABASE_NAME)


    class Config:
        case_sensitive = True

settings = Settings()

