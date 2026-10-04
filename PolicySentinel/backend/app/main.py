from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.chat import router as chat_router
from app.api.evaluate import router as evaluate_router
from app.api.audits import router as audits_router
from app.api.incidents import router as incidents_router
from app.api.policies import router as policies_router
from app.api.approvals import router as approvals_router
from app.api.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="AegisAI",
        description="A Customer-Service AI Policy Enforcement Gateway",
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(chat_router)
    app.include_router(evaluate_router)
    app.include_router(audits_router)
    app.include_router(incidents_router)
    app.include_router(policies_router)
    app.include_router(approvals_router)
    app.include_router(health_router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
