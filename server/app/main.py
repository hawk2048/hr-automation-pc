"""FastAPI Application Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.models import Base, engine
from app.errors import AppError, app_error_handler, generic_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager"""
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


# Create app
app = FastAPI(
    title="HR Automation API",
    description="HR Talent Matching System API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)


# Routes (import after app creation to avoid circular imports)
from app.routes import auth, jobs, candidates, matches, files, settings, evaluation, screening

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(screening.router, prefix="/api/screening", tags=["screening"])


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hr-automation-api"}


@app.get("/ready")
async def readiness_check():
    # Could add DB/Redis checks here
    return {"status": "ready"}


# Root
@app.get("/")
async def root():
    return {
        "message": "HR Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }