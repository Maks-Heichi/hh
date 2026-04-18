from __future__ import annotations

from urllib.parse import quote_plus

import psycopg2
from psycopg2.extensions import connection as PgConnection

from file_storage import DatabaseSettings


def connect_postgres(settings: DatabaseSettings, *, dbname: str) -> PgConnection:
    """Одно соединение по URI; спецсимволы в логине/пароле кодируются через ``quote_plus``."""
    user = quote_plus(settings.user, safe="")
    password = quote_plus(settings.password, safe="")
    host = quote_plus(settings.host, safe=":")
    dbn = quote_plus(dbname, safe="")
    uri = f"postgresql://{user}:{password}@{host}:{settings.port}/{dbn}"
    return psycopg2.connect(uri)
