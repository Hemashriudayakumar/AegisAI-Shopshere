import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "shopsphere_super_secret_key_change_in_production_2026")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///shopsphere.db")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///shopsphere.db")
    POLICY_SERVICE_URL = os.getenv("POLICY_SERVICE_URL", "http://localhost:8000")
    MOCK_POLICY_SERVICE = os.getenv("MOCK_POLICY_SERVICE", "false").lower() in ("true", "1", "yes")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

