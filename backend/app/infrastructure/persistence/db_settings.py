from __future__ import annotations

import os
from pathlib import Path


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///backend/.data/liber_trade_v2.db")


def get_sqlite_db_path_from_url(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("現在は sqlite DATABASE_URL のみサポートしています")
    relative = database_url.removeprefix("sqlite:///")
    root = Path(__file__).resolve().parents[4]
    return (root / relative).resolve()


def get_sqlalchemy_database_url() -> str:
    database_url = get_database_url()
    sqlite_path = get_sqlite_db_path_from_url(database_url)
    return f"sqlite:///{sqlite_path}"
