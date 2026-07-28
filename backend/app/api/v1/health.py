"""Liveness endpoint.

``/api/v1/health`` is the versioned check. ``app.main`` also exposes a
plain ``/health`` outside the version prefix, because hosting platforms
(Render, Cloud Run, Kubernetes probes) are configured with a fixed path
and should not have to be reconfigured when the API version changes.
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
