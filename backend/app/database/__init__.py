"""Database connections.

- ``postgres`` — SQLAlchemy engine/session and the declarative ``Base``.
  Source of truth for relational data (accounts, profiles, case metadata).
- ``mongodb`` — optional document store for Module 1's chat transcripts
  and AI evaluation results.
- ``vector_db`` — vector store for Module 1's RAG features (Team 1).

Import the submodule you need directly (``from app.database.postgres
import get_db``) rather than re-exporting here, so that importing one
store never pulls in another's driver.
"""
