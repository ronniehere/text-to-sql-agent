from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")


class Settings(BaseSettings):
    API_PORT: int = 8000
    GCP_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GCP_REGION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-2.0-flash"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    # Comma-separated list of allowed CORS origins for the API
    CORS_ORIGINS: str = "http://localhost:8501"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
