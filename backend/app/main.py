"""Papery API — FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import (
    admin,
    auth,
    files,
    findings,
    license,
    reports,
    team,
    verifications,
)
from .seed import seed_data
from .storage import ensure_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data()
    ensure_dir(settings.STORAGE_DIR)
    from .pipeline import recover_interrupted

    recover_interrupted()
    yield


app = FastAPI(title=settings.PROJECT_NAME, version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}


api = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api)
app.include_router(license.router, prefix=api)
app.include_router(team.router, prefix=api)
app.include_router(files.router, prefix=api)
app.include_router(verifications.router, prefix=api)
app.include_router(findings.router, prefix=api)
app.include_router(reports.router, prefix=api)
app.include_router(admin.router, prefix=api)
