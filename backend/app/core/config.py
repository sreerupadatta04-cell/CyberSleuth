import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Ensure Google GenAI SDK targets v1beta API version by default for modern Gemini models
os.environ.setdefault("GOOGLE_GENAI_API_VERSION", "v1beta")

class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberSleuth"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # SQLite Database
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATABASE_URL: str = f"sqlite:///{Path(__file__).resolve().parent.parent.parent.as_posix()}/cybersleuth.db"
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///./") or v == "sqlite:///cybersleuth.db":
            backend_dir = Path(__file__).resolve().parent.parent.parent.as_posix()
            db_name = v.split("///")[-1].lstrip("./")
            return f"sqlite:///{backend_dir}/{db_name}"
        return v
    
    # Dual LLM Provider Settings
    LLM_PROVIDER: str = "gemini" # "gemini" | "openai" | "auto"
    LLM_FALLBACK_PROVIDER: str = "openai" # "openai" | "gemini"
    
    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-lite-latest"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Execution & Safety Safeguards
    LLM_LIVE_REASONING: bool = True
    LLM_ALLOW_DETERMINISTIC_FALLBACK: bool = True
    
    # Ingestion Limits
    MAX_UPLOAD_SIZE_MB: int = 10
    
    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        extra = "allow"

settings = Settings()
