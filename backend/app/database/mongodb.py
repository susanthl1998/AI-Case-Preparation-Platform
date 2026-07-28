"""MongoDB connection management.

Per the platform architecture, MongoDB holds the schemaless, per-session
documents Module 1 (AI Trainer) produces — chat transcripts, AI evaluation
results, RAG artifacts. Relational data (accounts, profiles, case metadata)
lives in PostgreSQL; see ``postgres.py`` and ADR-02 in
``docs/Architecture/architecture.md`` for why case metadata was kept
relational rather than split across both stores.

**Optional by design.** ``MONGODB_URI`` unset means Mongo is simply not
configured, and ``get_database()`` raises a clear error only when something
actually asks for it. Module 2's endpoints never touch Mongo, so a missing
or unreachable Mongo must not prevent the service from starting and serving
auth, profiles, and the case repository.

Usage from a router::

    from app.database.mongodb import get_mongo_db

    @router.get("/transcripts/{session_id}")
    def read_transcript(session_id: str, mongo=Depends(get_mongo_db)):
        return mongo.transcripts.find_one({"session_id": session_id})
"""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:  # pragma: no cover - import only for type checkers
    from pymongo.database import Database

settings = get_settings()


class MongoNotConfiguredError(RuntimeError):
    """Raised when Mongo is used but ``MONGODB_URI`` was never set."""


@lru_cache
def get_client():
    """Return a process-wide ``MongoClient``.

    Cached because MongoClient maintains its own internal connection pool
    and is designed to be created once per process — building one per
    request would defeat that pooling entirely.
    """
    if not settings.mongodb_uri:
        raise MongoNotConfiguredError(
            "MONGODB_URI is not set — see backend/.env.example. "
            "Module 2 (accounts, profiles, case repository) does not need "
            "Mongo; only Module 1's chat/evaluation features do."
        )

    # Imported lazily so the dependency is only required by deployments
    # that actually enable Mongo.
    from pymongo import MongoClient

    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)


def get_database() -> "Database":
    """Return the configured Mongo database handle."""
    return get_client()[settings.mongodb_database]


def get_mongo_db() -> "Database":
    """FastAPI dependency wrapper around :func:`get_database`."""
    return get_database()


def is_configured() -> bool:
    """Whether a Mongo URI was provided. Lets callers degrade gracefully
    instead of catching :class:`MongoNotConfiguredError`."""
    return bool(settings.mongodb_uri)
