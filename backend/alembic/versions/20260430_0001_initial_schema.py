"""initial schema

Revision ID: 20260430_0001
Revises:
Create Date: 2026-04-30 22:40:00
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260430_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    migration_sql_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "infrastructure"
        / "persistence"
        / "migrations"
        / "0001_initial.sql"
    )
    bind = op.get_bind()
    raw_conn = bind.connection.driver_connection
    raw_conn.executescript(migration_sql_path.read_text(encoding="utf-8"))
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_type_inference_logs (
          evaluation_id TEXT PRIMARY KEY,
          process_id TEXT NOT NULL,
          document_id TEXT NOT NULL,
          rule_set_version TEXT NOT NULL,
          predicted_doc_type TEXT NOT NULL,
          confidence REAL NOT NULL DEFAULT 0,
          reasons_json TEXT NOT NULL DEFAULT '[]',
          final_doc_type TEXT NOT NULL,
          is_overridden INTEGER NOT NULL DEFAULT 0 CHECK (is_overridden IN (0, 1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_type_inference_logs")
    op.execute("DROP TABLE IF EXISTS document_comparison_items")
    op.execute("DROP TABLE IF EXISTS document_comparisons")
    op.execute("DROP TABLE IF EXISTS comparison_rules")
    op.execute("DROP TABLE IF EXISTS comparison_rule_sets")
    op.execute("DROP TABLE IF EXISTS document_type_rules")
    op.execute("DROP TABLE IF EXISTS document_type_rule_sets")
    op.execute("DROP TABLE IF EXISTS document_links")
    op.execute("DROP TABLE IF EXISTS trade_documents")
    op.execute("DROP TABLE IF EXISTS trade_chains")
    op.execute("DROP TABLE IF EXISTS document_processes")
