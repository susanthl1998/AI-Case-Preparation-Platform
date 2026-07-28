"""Signup, verification, login, refresh, and current-user lookup.

Implements US-03 (account creation) and the auth-related FRs (FR-01, FR-02)
plus NFR-01 (hashed passwords, session handling). Account lockout after
repeated failed logins is part of the US-03 acceptance criteria.

Policy lives in ``app/services/auth_service.py``; this module is only the
HTTP surface over it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.postgres import get_db
from app.models.user import User
from app.schemas.token import AccessTokenResponse, RefreshRequest, TokenResponse
from app.schemas.user import LoginRequest, SignupRequest, SignupResponse, UserOut, VerifyRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    user, verification_token = auth_service.register_user(db, payload.email, payload.password)
    return SignupResponse(
        id=user.id,
        email=user.email,
        is_verified=user.is_verified,
        verification_token=verification_token,
    )


@router.post("/verify")
def verify(payload: VerifyRequest, db: Session = Depends(get_db)) -> dict:
    auth_service.verify_account(db, payload.token)
    return {"message": "account verified"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate(db, payload.email, payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    return auth_service.refresh_access_token(db, payload.refresh_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
