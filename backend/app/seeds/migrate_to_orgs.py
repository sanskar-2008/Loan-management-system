"""
Required order: (1) create `organizations` with `default_flat_rate` / `default_compound_rate`,
(2) add `loans.organization_id` FK, (3) backfill default org for existing rows,
(4) THEN run `seed_demo.py` reseed.

Reseeding before org rate columns exist breaks the "orgs with default rates set on some"
demo data requirement.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import select, text

from app.config import get_settings
from app.database import SessionLocal, engine, Base
from app.models import Admin, Organization, Settings  # noqa: F401 — register models
from app.models.organization import LEGACY_ORG_CODE, LEGACY_ORG_NAME
from app.seeds.seed_admin import init_db
from app.utils.security import hash_password


def _db_path() -> Path:
    from app.config import DATA_DIR

    return DATA_DIR / "loan_management.db"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def migrate_schema() -> dict:
    """Steps 1–3: create orgs (+ rates), add organization_id, backfill Legacy / Unassigned."""
    init_db()
    db_path = _db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        # Step 1 — organizations table with rate columns (SQLAlchemy create_all)
        Base.metadata.create_all(bind=engine)

        # Ensure rate columns exist if table was created earlier without them
        if _table_exists(conn, "organizations"):
            if not _column_exists(conn, "organizations", "default_flat_rate"):
                conn.execute(
                    "ALTER TABLE organizations ADD COLUMN default_flat_rate NUMERIC(7,4)"
                )
            if not _column_exists(conn, "organizations", "default_compound_rate"):
                conn.execute(
                    "ALTER TABLE organizations ADD COLUMN default_compound_rate NUMERIC(7,4)"
                )

        # Step 2 — loans.organization_id
        if _table_exists(conn, "loans") and not _column_exists(conn, "loans", "organization_id"):
            conn.execute("ALTER TABLE loans ADD COLUMN organization_id VARCHAR(36)")

        # Make borrower_id nullable if needed (SQLite can't easily ALTER nullability;
        # new inserts may omit it; existing rows keep values)
        conn.commit()
    finally:
        conn.close()

    # Step 3 — backfill Legacy / Unassigned
    db = SessionLocal()
    try:
        legacy = db.scalar(select(Organization).where(Organization.code == LEGACY_ORG_CODE))
        if not legacy:
            legacy = Organization(
                code=LEGACY_ORG_CODE,
                name=LEGACY_ORG_NAME,
                status="active",
                notes="Auto-created during migration for loans without an organization.",
            )
            db.add(legacy)
            db.flush()

        # Assign loans missing organization_id
        db.execute(
            text(
                "UPDATE loans SET organization_id = :oid "
                "WHERE organization_id IS NULL OR organization_id = ''"
            ),
            {"oid": legacy.id},
        )
        db.commit()
        return {"legacy_org_id": legacy.id, "legacy_code": LEGACY_ORG_CODE}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_migration(*, with_seed: bool = False) -> dict:
    result = migrate_schema()
    if with_seed:
        # Step 4 — only after 1–3
        from app.seeds.seed_demo import seed_demo

        seed_result = seed_demo(force=True)
        result["seed"] = seed_result
    return result


if __name__ == "__main__":
    import sys

    with_seed = "--seed" in sys.argv
    out = run_migration(with_seed=with_seed)
    print("Migration complete:", out)
