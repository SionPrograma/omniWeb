import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniWeb Platform"
    VERSION: str = "1.5.0-cockpit"
    API_V1_STR: str = "/api/v1"
    
    # Cors configuration
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Active modules list (Lingua & Idiomas-IA desactivados por aislamiento de dependencias ML)
    ACTIVE_MODULES: list[str] = ["reparto", "finanzas", "programacion", "musica"]
    
    # System Mode: creator (full access) or user (simplified)
    OMNIWEB_MODE: str = os.getenv("OMNIWEB_MODE", "creator")

    # Database & Storage
    DATA_DIR: str = "backend/data"
    DATABASE_NAME: str = "omniweb.db"
    ADMIN_TOKEN: str = os.getenv("OMNIWEB_ADMIN_TOKEN", "omniweb-dev-secret-token")

    # Cognitive Bridge (L2 Deep Reasoning)
    COGNITIVE_PROVIDER: str = os.getenv("COGNITIVE_PROVIDER", "groq")
    COGNITIVE_API_KEY: str = os.getenv("COGNITIVE_API_KEY", "")
    COGNITIVE_MODEL: str = os.getenv("COGNITIVE_MODEL", "llama3-8b-8192")
    COGNITIVE_TIMEOUT_MS: int = int(os.getenv("COGNITIVE_TIMEOUT_MS", "3500"))


    # OAuth Settings (Phase 15)
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "mock_id")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "mock_secret")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "mock_id")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "mock_secret")
    # Creator Security Fortress (Phase 16)
    CREATOR_ID: str = os.getenv("OMNIWEB_CREATOR_ID", "1") # Default to admin user '1'
    CREATOR_PIN: str = os.getenv("OMNIWEB_CREATOR_PIN", "1234") # PIN for critical operations
    REQUIRE_TRUSTED_DEVICE: bool = True
    REQUIRE_HARDWARE_AUTH: bool = False # Set to true for high-security environments

    @property
    def DATABASE_URL(self) -> str:
        return os.path.join(self.DATA_DIR, self.DATABASE_NAME)

    @property
    def IS_ADMIN_TOKEN_SAFE(self) -> bool:
        """Checks if the current ADMIN_TOKEN is the default insecure one."""
        return self.ADMIN_TOKEN != "omniweb-dev-secret-token"


    class Config:
        case_sensitive = True

settings = Settings()

