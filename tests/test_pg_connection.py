from __future__ import annotations

from unittest.mock import MagicMock, patch

from file_storage import DatabaseSettings
from pg_connection import connect_postgres


def test_connect_postgres_uses_uri() -> None:
    s = DatabaseSettings(
        host="localhost",
        port=5432,
        name="db",
        user="u",
        password="p@:",
        maintenance_name="postgres",
    )
    with patch("pg_connection.psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        connect_postgres(s, dbname="postgres")
    arg = mock_connect.call_args[0][0]
    assert isinstance(arg, str)
    assert arg.startswith("postgresql://")
