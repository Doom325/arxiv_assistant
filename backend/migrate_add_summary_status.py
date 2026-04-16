"""Migration: Add summary_status / summary_error / summary_attempted_at columns.

Moves summarization failure state out of ``papers.generated_summary`` (which
previously encoded failures as ``__ERROR__: ...`` strings) and into dedicated
columns. Backfills any existing ``__ERROR__`` rows by parsing the message,
populating the new structured columns, and NULLing the overloaded column.

Idempotent — safe to run multiple times. Each DDL guard checks the live
schema before mutating.
"""

import logging

from sqlalchemy import inspect, text

from database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ERROR_PREFIX = "__ERROR__: "


def _is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


def _infer_error_code(message: str) -> str:
    """Map a legacy error message to a structured error code."""
    lowered = message.lower()
    if "failed to download pdf" in lowered:
        return "pdf_download_failed"
    if "summarization failed" in lowered:
        return "summarization_failed"
    return "legacy_unknown"


def _add_columns_if_missing() -> None:
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("papers")}

    json_type = "JSON" if _is_sqlite() else "JSONB"

    with engine.begin() as conn:
        if "summary_status" not in existing:
            conn.execute(text(
                "ALTER TABLE papers ADD COLUMN summary_status VARCHAR(20)"
            ))
            logger.info("Added column: papers.summary_status")
        else:
            logger.info("Column papers.summary_status already exists — skipping.")

        if "summary_error" not in existing:
            conn.execute(text(
                f"ALTER TABLE papers ADD COLUMN summary_error {json_type}"
            ))
            logger.info("Added column: papers.summary_error")
        else:
            logger.info("Column papers.summary_error already exists — skipping.")

        if "summary_attempted_at" not in existing:
            conn.execute(text(
                "ALTER TABLE papers ADD COLUMN summary_attempted_at TIMESTAMP"
            ))
            logger.info("Added column: papers.summary_attempted_at")
        else:
            logger.info(
                "Column papers.summary_attempted_at already exists — skipping."
            )


def _add_check_constraint_if_missing() -> None:
    """Postgres-only: add CHECK constraint for summary_status values."""
    if _is_sqlite():
        return
    with engine.begin() as conn:
        existing = conn.execute(text(
            "SELECT 1 FROM pg_constraint WHERE conname = "
            "'ck_papers_summary_status'"
        )).first()
        if existing:
            logger.info(
                "Constraint ck_papers_summary_status already exists — skipping."
            )
            return
        conn.execute(text(
            "ALTER TABLE papers ADD CONSTRAINT ck_papers_summary_status "
            "CHECK (summary_status IS NULL OR summary_status IN "
            "('pending', 'running', 'succeeded', 'failed'))"
        ))
        logger.info("Added constraint: ck_papers_summary_status")


def _backfill_legacy_error_rows() -> int:
    """Parse existing ``__ERROR__: ...`` rows and migrate them.

    Returns the number of rows backfilled.
    """
    rows_touched = 0
    with engine.begin() as conn:
        result = conn.execute(text(
            "SELECT id, generated_summary, updated_date "
            "FROM papers "
            "WHERE generated_summary LIKE :prefix "
            "AND (summary_status IS NULL OR summary_status <> 'failed')"
        ), {"prefix": f"{ERROR_PREFIX}%"})
        legacy_rows = result.fetchall()

        for row in legacy_rows:
            paper_id = row[0]
            legacy_summary = row[1] or ""
            updated_date = row[2]
            message = legacy_summary[len(ERROR_PREFIX):] if legacy_summary.startswith(
                ERROR_PREFIX
            ) else legacy_summary

            attempted_at_iso = (
                updated_date.isoformat() if updated_date is not None else None
            )
            error_payload = {
                "code": _infer_error_code(message),
                "message": message,
                "attempted_at": attempted_at_iso,
                "attempt_count": 1,
            }

            if _is_sqlite():
                import json as _json
                conn.execute(text(
                    "UPDATE papers SET "
                    "  summary_status = 'failed', "
                    "  summary_error = :err, "
                    "  summary_attempted_at = COALESCE(updated_date, CURRENT_TIMESTAMP), "
                    "  generated_summary = NULL "
                    "WHERE id = :pid"
                ), {"err": _json.dumps(error_payload), "pid": paper_id})
            else:
                conn.execute(text(
                    "UPDATE papers SET "
                    "  summary_status = 'failed', "
                    "  summary_error = CAST(:err AS JSONB), "
                    "  summary_attempted_at = COALESCE(updated_date, NOW()), "
                    "  generated_summary = NULL "
                    "WHERE id = :pid"
                ), {
                    "err": __import__("json").dumps(error_payload),
                    "pid": paper_id,
                })
            rows_touched += 1

    return rows_touched


def run_migration() -> None:
    inspector = inspect(engine)
    if "papers" not in inspector.get_table_names():
        logger.warning("Table 'papers' does not exist — skipping migration.")
        return

    _add_columns_if_missing()
    _add_check_constraint_if_missing()
    touched = _backfill_legacy_error_rows()
    logger.info(
        "Migration complete. Legacy __ERROR__ rows backfilled: %d", touched
    )


if __name__ == "__main__":
    run_migration()
