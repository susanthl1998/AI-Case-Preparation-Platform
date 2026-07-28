"""User-facing account endpoints: onboarding, profile, dashboard, deletion.

This file is the platform skeleton's ``users.py`` slot. It merges what
Module 2 developed as two routers (``profile`` and ``account``) because
both are operations on the authenticated user's own record.

URL paths are kept as ``/profile/*``, ``/dashboard`` and ``/account/me``
rather than being flattened under a ``/users`` prefix — the file layout
changed, the API contract deliberately did not (beyond the ``/api/v1``
prefix added in ``app.main``). See ``docs/API/api-spec.md``.

Implements US-03 onboarding (FR-03), profile editing (FR-05), dashboard
ordering (FR-04, ARCHITECTURE ADR-06), and account deletion (ADR-03).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.postgres import get_db
from app.models.case import Case
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import DashboardOut, OnboardingRequest, ProfileOut, ProfileUpdateRequest
from app.schemas.user import AccountDeletionResult
from app.services.case_service import case_to_out, case_types_for_preferences
from app.services.storage_service import get_storage

router = APIRouter(tags=["users"])


def _get_or_create_profile(db: Session, user: User) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.flush()
    return profile


# --------------------------------------------------------------------------
# Onboarding and profile
# --------------------------------------------------------------------------


@router.post("/profile/onboarding", response_model=ProfileOut)
def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = _get_or_create_profile(db, current_user)
    profile.target_firm_type = payload.target_firm_type
    profile.case_preferences = payload.case_preferences
    profile.onboarding_completed = True
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile/me", response_model=ProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Profile:
    return _get_or_create_profile(db, current_user)


@router.patch("/profile/me", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = _get_or_create_profile(db, current_user)
    if payload.target_firm_type is not None:
        profile.target_firm_type = payload.target_firm_type
    if payload.case_preferences is not None:
        profile.case_preferences = payload.case_preferences
    db.commit()
    db.refresh(profile)
    return profile


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardOut:
    """FR-04: dashboard ordered by the user's stated preference. See
    ARCHITECTURE ADR-06 — ordering is driven by ``case_preferences``
    (which map onto the consulting-only case taxonomy), not by
    ``target_firm_type`` directly, since Product Management has no
    matching case types in v1.0.
    """
    profile = _get_or_create_profile(db, current_user)

    base_query = db.query(Case).filter(Case.is_shared.is_(True), Case.is_removed.is_(False))
    preferred_types = case_types_for_preferences(profile.case_preferences)

    if preferred_types:
        matching = (
            base_query.filter(Case.case_type.in_(preferred_types)).order_by(Case.created_at.desc()).limit(10).all()
        )
        remaining_slots = 10 - len(matching)
        others = []
        if remaining_slots > 0:
            others = (
                base_query.filter(Case.case_type.notin_(preferred_types))
                .order_by(Case.created_at.desc())
                .limit(remaining_slots)
                .all()
            )
        cases = matching + others
    else:
        # No matched preference — newest-first. For a Product Management
        # user this is the documented v1.0 limitation (ADR-06), not an
        # error: there is no PM-specific case type to prioritize yet.
        cases = base_query.order_by(Case.created_at.desc()).limit(10).all()

    return DashboardOut(
        profile=ProfileOut.model_validate(profile),
        recommended_cases=[case_to_out(c, current_user.id) for c in cases],
    )


# --------------------------------------------------------------------------
# Account deletion (ADR-03: shared cases are retained and anonymized,
# private-only cases are hard-deleted with the account)
# --------------------------------------------------------------------------


@router.delete("/account/me", response_model=AccountDeletionResult)
def delete_account(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AccountDeletionResult:
    owned_cases = db.query(Case).filter(Case.owner_id == current_user.id).all()

    anonymized = 0
    deleted = 0
    storage = get_storage()
    for case in owned_cases:
        if case.is_shared:
            case.owner_deleted = True
            case.owner_id = None
            anonymized += 1
        else:
            storage.delete(case.storage_key)
            db.delete(case)
            deleted += 1

    # Scrub credentials so a "deleted" account can never authenticate again,
    # while keeping the row itself for referential integrity / audit trail
    # (NFR-01: protect user data even in the deletion path).
    current_user.is_deleted = True
    current_user.email = f"deleted-user-{current_user.id}@caseArena.invalid"
    current_user.hashed_password = ""
    current_user.verification_token = None
    db.commit()

    return AccountDeletionResult(
        message="account deleted",
        cases_anonymized=anonymized,
        cases_deleted=deleted,
    )
