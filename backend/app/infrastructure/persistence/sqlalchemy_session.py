from __future__ import annotations

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from app.infrastructure.persistence.db_settings import get_sqlalchemy_database_url


def create_engine_and_sessionmaker() -> tuple[Engine, sessionmaker]:
    engine = create_engine(get_sqlalchemy_database_url(), future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
