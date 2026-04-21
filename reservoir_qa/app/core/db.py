from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_config


def get_admin_engine() -> Engine:
    config = get_config()
    return create_engine(config.database_url_admin)


def get_query_engine() -> Engine:
    config = get_config()
    return create_engine(config.database_url_query)

