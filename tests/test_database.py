from __future__ import annotations

from unittest.mock import MagicMock, patch

from database import create_database_if_not_exists, create_tables
from file_storage import DatabaseSettings


def _settings() -> DatabaseSettings:
    return DatabaseSettings(
        host="h",
        port=5432,
        name="db1",
        user="u",
        password="p",
        maintenance_name="postgres",
    )


def test_create_database_if_not_exists_creates_when_missing() -> None:
    settings = _settings()
    cur = MagicMock()
    cur.fetchone.return_value = None
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cur
    cursor_cm.__exit__.return_value = False
    conn = MagicMock()
    conn.cursor.return_value = cursor_cm
    with patch("database._connect", return_value=conn):
        create_database_if_not_exists(settings)
    assert conn.autocommit is True
    assert cur.execute.call_count >= 2


def test_create_tables_runs_ddl() -> None:
    settings = _settings()
    cur = MagicMock()
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cur
    cursor_cm.__exit__.return_value = False
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value = cursor_cm
    with patch("database._connect", return_value=conn):
        create_tables(settings)
    cur.execute.assert_called_once()
    assert "CREATE TABLE" in cur.execute.call_args[0][0]
