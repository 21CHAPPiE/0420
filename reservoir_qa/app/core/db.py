from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_config


def _create_server_engine(db_url: str) -> Engine:
    url = make_url(db_url).set(database=None)
    return create_engine(url)


def get_admin_engine() -> Engine:
    config = get_config()
    return create_engine(config.database_url_admin)


def get_admin_server_engine() -> Engine:
    config = get_config()
    return _create_server_engine(config.database_url_admin)


def get_query_engine() -> Engine:
    config = get_config()
    return create_engine(config.database_url_query)


def _can_connect(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def can_connect_admin_server() -> bool:
    return _can_connect(get_admin_server_engine())


def can_connect_query_database() -> bool:
    return _can_connect(get_query_engine())
