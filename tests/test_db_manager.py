from __future__ import annotations

from unittest.mock import MagicMock, patch

from db_manager import DBManager
from file_storage import DatabaseSettings


def _settings() -> DatabaseSettings:
    return DatabaseSettings(
        host="h",
        port=5432,
        name="db",
        user="u",
        password="p",
        maintenance_name="postgres",
    )


def test_get_avg_salary() -> None:
    cur = MagicMock()
    cur.fetchone.return_value = (125.5,)
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cur
    cursor_cm.__exit__.return_value = False
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value = cursor_cm
    db = DBManager(_settings())
    with patch.object(db, "_connect", return_value=conn):
        assert db.get_avg_salary() == 125.5


def test_get_vacancies_with_keyword() -> None:
    cur = MagicMock()
    cur.fetchall.return_value = [("Co", "Job", "http://u")]
    cursor_cm = MagicMock()
    cursor_cm.__enter__.return_value = cur
    cursor_cm.__exit__.return_value = False
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value = cursor_cm
    db = DBManager(_settings())
    with patch.object(db, "_connect", return_value=conn):
        rows = db.get_vacancies_with_keyword("py")
    assert rows == [("Co", "Job", "http://u")]
    cur.execute.assert_called_once()
    assert cur.execute.call_args[0][1] == ("%py%",)
