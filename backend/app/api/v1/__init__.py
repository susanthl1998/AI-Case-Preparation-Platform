"""v1 API router aggregation — the single integration point for all teams.

Each module contributes an ``APIRouter`` from its own file in this package
and registers it below. ``app.main`` mounts this one router under
``/api/v1``, so no team needs to touch ``main.py`` to add endpoints, and
merge conflicts stay confined to the short list below.

**Adding your module's routes:**

1. Define ``router = APIRouter(prefix="/yourthing", tags=["yourthing"])``
   in your own file in this package.
2. Import it and add one ``include_router`` line below.

Team 1 (AI Trainer) owns ``chat.py`` and ``interview.py``; Team 3
(Multiplayer) has no file here yet — add one rather than extending
another team's module, so ownership stays obvious in the git history.
"""
from fastapi import APIRouter

from app.api.v1 import auth, cases, health, users

api_router = APIRouter()

# --- Module 2 — Account Management & Case Repository (Team 2) ---
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cases.router)

# --- Module 1 — AI Trainer (Team 1) ---
# chat.py and interview.py are still empty scaffolding. Uncomment as each
# gains a `router`; importing an empty module here would raise on startup.
# from app.api.v1 import chat, interview
# api_router.include_router(chat.router)
# api_router.include_router(interview.router)

# --- Module 3 — Multiplayer Group Preparation (Team 3) ---
# from app.api.v1 import groups
# api_router.include_router(groups.router)

__all__ = ["api_router"]
