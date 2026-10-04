import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "AegisAI"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./aegisai.db"
    )
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    USE_MOCK_LLM_BY_DEFAULT: bool = os.getenv("USE_MOCK_LLM", "false").lower() in ("true", "1", "yes")

settings = Settings()
