"""Authentication operations: registration, verification, login, refresh.

Split from the router (``app/api/v1/auth.py``) so the HTTP layer stays thin
and this logic can be reused — Team 1 and Team 3 need to *validate* tokens,
not reimplement lockout rules, and anything running outside a request
(scripts, background jobs) can call these directly.

The division of labour with ``app/core/security.py``: that module holds the
primitives (hashing, JWT encode/decode) and knows nothing about the
database; this one holds the policy (who may log in, when an account
locks) and does the persistence.

These functions raise ``HTTPException`` directly rather than defining a
parallel exception hierarchy for the routers to translate. That is a
deliberate simplification for a service that is only ever consumed by this
FastAPI app — revisit it if this package is ever imported by a non-HTTP
consumer.
"""
from __future__ import annotations

import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    hash_password,
    verify_password,
)
from app.models.profile import Profile
from app.models.user import User
from app.schemas.token import AccessTokenResponse, TokenResponse

settings = get_settings()


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    """Create an account and its empty profile row.

    Returns the user and its verification token. See ADR-04 for why the
    token is returned to the caller rather than emailed — there is no
    transactional email provider wired up in v1.0.
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "an account with this email already exists")

    token = generate_verification_token()
    user = User(
        email=email,
        hashed_password=hash_password(password),
        verification_token=token,
    )
    db.add(user)
    db.flush()  # populate user.id before creating the dependent profile row

    # An empty profile row so onboarding (US-03 AC) has something to update.
    db.add(Profile(user_id=user.id))
    db.commit()
    db.refresh(user)

    return user, token


def verify_account(db: Session, token: str) -> None:
    user = db.query(User).filter(User.verification_token == token).first()
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid verification token")

    user.is_verified = True
    user.verification_token = None
    db.commit()


def _raise_if_locked(db: Session, user: User | None) -> None:
    """Reject a login attempt while the lockout window is still open.

    If the window has passed, the counters are reset in place so this
    attempt is judged on its own merits.
    """
    if user is None or user.locked_until is None:
        return

    now = dt.datetime.now(dt.timezone.utc)
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        # SQLite round-trips datetimes without tzinfo; treat naive values
        # as UTC rather than letting the comparison below raise.
        locked_until = locked_until.replace(tzinfo=dt.timezone.utc)

    if locked_until > now:
        retry_after = int((locked_until - now).total_seconds())
        raise HTTPException(
            status.HTTP_423_LOCKED,
            {
                "detail": "account temporarily locked due to repeated failed logins",
                "retry_after_seconds": retry_after,
            },
        )

    user.failed_login_attempts = 0
    user.locked_until = None


def _register_failed_attempt(db: Session, user: User | None) -> None:
    """Count a failed login and lock the account at the configured limit."""
    if user is None:
        return

    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.max_failed_login_attempts:
        user.locked_until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=settings.lockout_duration_minutes
        )
    db.commit()


def authenticate(db: Session, email: str, password: str) -> User:
    """Return the user for valid credentials, or raise 401/423.

    The same 401 is returned for an unknown email and a wrong password, so
    the response cannot be used to enumerate registered accounts.
    """
    user = db.query(User).filter(User.email == email, User.is_deleted.is_(False)).first()

    _raise_if_locked(db, user)

    if user is None or not verify_password(password, user.hashed_password):
        _register_failed_attempt(db, user)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "incorrect email or password")

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    return user


def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.email, user.is_admin),
        refresh_token=create_refresh_token(user.id, user.email, user.is_admin),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def refresh_access_token(db: Session, refresh_token: str) -> AccessTokenResponse:
    try:
        token_payload = decode_token(refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = db.get(User, int(token_payload["sub"]))
    if user is None or user.is_deleted:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user no longer exists")

    return AccessTokenResponse(
        access_token=create_access_token(user.id, user.email, user.is_admin),
        expires_in=settings.access_token_expire_minutes * 60,
    )
