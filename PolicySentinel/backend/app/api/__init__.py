from app.api.chat import router as chat_router
from app.api.audits import router as audits_router
from app.api.incidents import router as incidents_router
from app.api.policies import router as policies_router
from app.api.approvals import router as approvals_router
from app.api.health import router as health_router

__all__ = [
    "chat_router",
    "audits_router",
    "incidents_router",
    "policies_router",
    "approvals_router",
    "health_router",
]
