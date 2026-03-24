from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from src.config import settings
from src.api.v1 import auth, departments, agents, admin, chat, me

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("tania.startup", env=settings.ENVIRONMENT)
    yield
    log.info("tania.shutdown")


app = FastAPI(
    title="TanIA API",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(departments.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
