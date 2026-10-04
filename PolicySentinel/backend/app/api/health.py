from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.policies.engine import policy_engine
from app.agents.llm_provider import check_ollama_alive

router = APIRouter(tags=["health"])

@router.get("/health")
@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    ollama_live = check_ollama_alive(settings.OLLAMA_BASE_URL)

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "model": settings.OLLAMA_MODEL,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_connected": ollama_live,
        "active_llm_engine": f"Ollama ({settings.OLLAMA_MODEL})" if ollama_live else "Intelligent Fallback Provider (Ollama server not running)",
        "active_policies_count": len(policy_engine.list_policies()),
        "policies_loaded": list(policy_engine.policies.keys())
    }
