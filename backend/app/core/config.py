"""Centralized application settings, loaded from environment variables.

See ``.env.example`` for the full list of variables a deployment must
provide. Nothing here hardcodes a secret — local dev falls back to
clearly-fake defaults so the app boots without a `.env` file, but every
fallback is something you would never accept in staging/production.
"""
import re
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def vercel_origin_regex(project_slug: str) -> str:
    """Regex matching a Vercel project's production and preview origins.

    Vercel gives every pull request its own hostname
    (``<project>-git-<branch>-<team>.vercel.app``), so an exact-match CORS
    allowlist blocks every preview deployment: the page loads and then each
    API call fails. This matches the project's whole hostname family.

    Anchored at both ends, and the slug is escaped, on purpose. An
    unanchored pattern like ``vercel\\.app`` would also match
    ``https://evil-vercel.app`` and ``https://vercel.app.attacker.com``,
    which would hand CORS access to anyone who can register a domain. The
    slug prefix further keeps it to *this* project rather than every app
    hosted on Vercel.
    """
    return rf"^https://{re.escape(project_slug)}(-[a-z0-9-]+)?\.vercel\.app$"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Case Preparation Platform"
    environment: str = "development"
    debug: bool = True

    # Mount point for the v1 API. Referenced by app.main and the test
    # suite rather than hardcoded, so a future /api/v2 is one change.
    api_v1_prefix: str = "/api/v1"

    # --- PostgreSQL -------------------------------------------------------
    # Source of truth for relational data: accounts, profiles, sessions and
    # case metadata (see docs/Architecture/architecture.md, ADR-02).
    # SQLite is acceptable only for a zero-dependency local smoke test.
    database_url: str = "sqlite:///./dev.db"

    # --- MongoDB ----------------------------------------------------------
    # Document store for Module 1 (AI Trainer): chat transcripts, AI
    # evaluation results, and other schemaless per-session documents.
    # Optional — the app boots and serves Module 2 without it, so a missing
    # Mongo does not take down account management or the case repository.
    # See app/database/mongodb.py.
    mongodb_uri: str = ""
    mongodb_database: str = "casearena"

    # Auth
    jwt_secret_key: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Account lockout (FR: "5 consecutive failures -> temporary lock")
    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # File uploads (FR-09: PDF up to 10 MB)
    max_upload_size_bytes: int = 10 * 1024 * 1024
    upload_storage_dir: str = "./storage/uploads"

    # Where uploaded PDFs live. One of:
    #   "local"    — disk, dev only; wiped on redeploy on most hosts
    #   "database" — bytes in Postgres; no extra vendor/credentials needed
    #   "s3"       — AWS S3, or S3-compatible (Cloudflare R2) via
    #                s3_endpoint_url; the right choice past demo volumes
    # Anything other than "local" survives a restart. See ADR-07.
    storage_backend: str = "local"
    s3_bucket_name: str = ""
    s3_region: str = "auto"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint_url: str = ""  # leave blank for real AWS S3; set for R2/MinIO/etc.

    # CORS — the frontend origin(s) allowed to call this API
    cors_allow_origins: list[str] = ["http://localhost:5173"]

    # Vercel project slug (e.g. "ai-case-prep"). Setting it lets every
    # preview deployment for that project through CORS automatically;
    # otherwise each pull request's preview URL would have to be added to
    # cors_allow_origins by hand, which nobody will remember to do.
    # Leave blank to disable regex matching entirely.
    vercel_project_slug: str = ""

    @property
    def cors_allow_origin_regex(self) -> str | None:
        if not self.vercel_project_slug:
            return None
        return vercel_origin_regex(self.vercel_project_slug)


@lru_cache
def get_settings() -> Settings:
    return Settings()
