from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSettings:
    """Параметры подключения к PostgreSQL (из `.env`)."""

    host: str
    port: int
    name: str
    user: str
    password: str
    maintenance_name: str


def _repo_root() -> Path:
    """Корень проекта (рядом с `data/` и корневым `main.py`)."""
    return Path(__file__).resolve().parent.parent


def dotenv_path() -> Path:
    """Абсолютный путь к `.env` в корне репозитория (для подсказок в логе)."""
    return _repo_root() / ".env"


def _apply_env_file(path: Path) -> None:
    """
    Подставляет переменные из `.env` в os.environ.

    Читает файл как байты и декодирует в UTF-8 с заменой ошибок — иначе на Windows
    смесь кодировок даёт UnicodeDecodeError уже внутри psycopg2/libpq.
    """
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().removeprefix("\ufeff")
        val = val.strip()
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1]
        if val.startswith("'") and val.endswith("'") and len(val) >= 2:
            val = val[1:-1]
        if not key:
            continue
        val = re.sub(r"\s+#.*$", "", val).strip()
        os.environ[key] = val


def load_database_settings() -> DatabaseSettings:
    """Читает `.env` и возвращает настройки БД (без них — ValueError)."""
    env_path = _repo_root() / ".env"
    if env_path.is_file():
        _apply_env_file(env_path)

    def _t(key: str, default: str | None = None) -> str | None:
        v = os.getenv(key, default) if default is not None else os.getenv(key)
        return v.strip() if isinstance(v, str) else v

    host = _t("DB_HOST", "localhost") or "localhost"
    port_raw = _t("DB_PORT", "5432") or "5432"
    name = _t("DB_NAME")
    user = _t("DB_USER")
    password = _t("DB_PASSWORD")
    maintenance = _t("DB_MAINTENANCE_NAME", "postgres") or "postgres"
    if not name or not user or password is None:
        raise ValueError("Заполните DB_NAME, DB_USER и DB_PASSWORD в `.env`.")
    return DatabaseSettings(
        host=host,
        port=int(port_raw),
        name=name,
        user=user,
        password=password,
        maintenance_name=maintenance,
    )


def load_employer_ids(json_path: Path | None = None) -> list[int]:
    """Список id работодателей из JSON (`employers` или `employer_ids`)."""
    path = json_path or _repo_root() / "data" / "employer_ids.json"
    if not path.is_file():
        raise FileNotFoundError(str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("employers")
    if isinstance(rows, list) and rows:
        out = [int(r["id"]) for r in rows if isinstance(r, dict) and "id" in r]
        if out:
            return out
        raise ValueError("В `employers` нет полей id.")
    legacy = payload.get("employer_ids")
    if isinstance(legacy, list) and legacy:
        return [int(x) for x in legacy]
    raise ValueError("Ожидается ключ `employers` или `employer_ids`.")
