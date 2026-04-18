from __future__ import annotations

import json
from pathlib import Path

import pytest

from file_storage import DatabaseSettings, load_database_settings, load_employer_ids


def test_load_employer_ids_from_employers(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text(
        json.dumps({"employers": [{"id": 10, "name": "A"}, {"id": 20, "name": "B"}]}),
        encoding="utf-8",
    )
    assert load_employer_ids(path) == [10, 20]


def test_load_employer_ids_legacy(tmp_path: Path) -> None:
    path = tmp_path / "y.json"
    path.write_text(json.dumps({"employer_ids": [3, 4]}), encoding="utf-8")
    assert load_employer_ids(path) == [3, 4]


def test_load_employer_ids_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_employer_ids(tmp_path / "missing.json")


def test_load_database_settings_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "h")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "n")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.delenv("DB_MAINTENANCE_NAME", raising=False)
    import file_storage as fs

    monkeypatch.setattr(fs, "_apply_env_file", lambda *_a, **_k: None)
    s = load_database_settings()
    assert isinstance(s, DatabaseSettings)
    assert (s.host, s.port, s.name, s.user, s.password, s.maintenance_name) == (
        "h",
        5433,
        "n",
        "u",
        "p",
        "postgres",
    )


def test_load_database_settings_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import file_storage as fs

    monkeypatch.setattr(fs, "_apply_env_file", lambda *_a, **_k: None)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_HOST", "x")
    monkeypatch.setenv("DB_PORT", "1")
    with pytest.raises(ValueError):
        load_database_settings()
