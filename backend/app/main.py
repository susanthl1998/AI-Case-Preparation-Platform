"""FastAPI application entrypoint for the AI Case Preparation Platform.

Run locally with ``uvicorn app.main:app --reload`` (see backend/README.md).

All feature routes are registered in ``app/api/v1/__init__.py`` and mounted
here as a single router, so adding endpoints never requires editing this
file — that keeps merge conflicts between the three teams confined to one
short list of ``include_router`` calls.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered case-interview preparation platform. "
        "See /docs for the interactive API reference, and docs/API/api-spec.md "
        "for the integration contract between modules."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    # Lets Vercel preview deployments call the API — each pull request gets
    # its own hostname, so an exact allowlist alone would break every
    # preview. None when VERCEL_PROJECT_SLUG is unset.
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
def root() -> dict:
    """A bare 404 on the root URL is a poor first impression for anyone
    landing on this service cold (a teammate, a reviewer) — point them at
    the interactive docs instead of leaving them guessing.
    """
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_v1_prefix,
    }


@app.get("/health", tags=["health"])
def health() -> dict:
    """Unversioned liveness check, mirroring ``/api/v1/health``.

    Hosting platforms (Render, Cloud Run, Kubernetes probes) are configured
    with one fixed health path; keeping this outside the version prefix
    means bumping to /api/v2 later won't silently break deployment health
    checks.
    """
    return {"status": "ok"}
