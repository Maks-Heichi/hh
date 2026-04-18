from __future__ import annotations

import logging
from typing import Any, Protocol

from psycopg2 import sql
from psycopg2.extras import execute_values

from file_storage import DatabaseSettings
from pg_connection import connect_postgres as _connect
from vacancies import normalize_vacancy

logger = logging.getLogger(__name__)


class HhDataSource(Protocol):
    """Источник данных hh.ru: API или парсинг сайта."""

    def get_employer(self, employer_id: int) -> dict[str, Any] | None:
        ...

    def get_vacancies_for_employer(self, employer_id: int) -> list[dict[str, Any]]:
        ...


def create_database_if_not_exists(settings: DatabaseSettings) -> None:
    """Создаёт базу `settings.name`, если её ещё нет (через maintenance DB)."""
    conn = _connect(settings, dbname=settings.maintenance_name)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (settings.name,),
            )
            if cur.fetchone() is None:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(settings.name)
                    )
                )
                logger.info("Создана БД %s", settings.name)
            else:
                logger.info("БД %s уже есть", settings.name)
    finally:
        conn.close()


def create_tables(settings: DatabaseSettings) -> None:
    """Создаёт таблицы `employers` и `vacancies` (если их ещё нет)."""
    ddl = """
    CREATE TABLE IF NOT EXISTS employers (
        employer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        open_vacancies INTEGER,
        alternate_url TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vacancies (
        vacancy_id INTEGER PRIMARY KEY,
        employer_id INTEGER NOT NULL REFERENCES employers (employer_id)
            ON DELETE CASCADE,
        name TEXT NOT NULL,
        salary_from INTEGER,
        salary_to INTEGER,
        salary_currency VARCHAR(16),
        salary_mid INTEGER,
        alternate_url TEXT NOT NULL
    );
    """
    conn = _connect(settings, dbname=settings.name)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        logger.info("Таблицы готовы")
    finally:
        conn.close()


def _truncate(settings: DatabaseSettings) -> None:
    """Полная очистка таблиц перед новой загрузкой."""
    conn = _connect(settings, dbname=settings.name)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE vacancies, employers CASCADE;")
    finally:
        conn.close()


def populate_from_hh(
    settings: DatabaseSettings,
    api: HhDataSource,
    employer_ids: list[int],
) -> None:
    """Очистка таблиц (TRUNCATE), затем заполнение работодателей и вакансий (режим API или веб)."""
    logger.info("Очистка таблиц (TRUNCATE)…")
    _truncate(settings)
    logger.info("Таблицы очищены, загрузка работодателей.")

    conn = _connect(settings, dbname=settings.name)
    try:
        for eid in employer_ids:
            logger.info("Работодатель %s…", eid)
            emp = api.get_employer(eid)
            if not emp:
                logger.warning("Работодатель %s не найден, пропуск", eid)
                continue
            raw = api.get_vacancies_for_employer(eid)
            rows = [normalize_vacancy(v, eid) for v in raw]
            nm = str(emp.get("name") or "").strip()
            open_cnt = emp.get("open_vacancies")
            alt = str(emp.get("alternate_url") or f"https://hh.ru/employer/{eid}")
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO employers (employer_id, name, open_vacancies, alternate_url)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (employer_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            open_vacancies = EXCLUDED.open_vacancies,
                            alternate_url = EXCLUDED.alternate_url;
                        """,
                        (eid, nm, open_cnt, alt),
                    )
                    if rows:
                        execute_values(
                            cur,
                            """
                            INSERT INTO vacancies (
                                vacancy_id, employer_id, name,
                                salary_from, salary_to, salary_currency,
                                salary_mid, alternate_url
                            ) VALUES %s
                            ON CONFLICT (vacancy_id) DO UPDATE SET
                                employer_id = EXCLUDED.employer_id,
                                name = EXCLUDED.name,
                                salary_from = EXCLUDED.salary_from,
                                salary_to = EXCLUDED.salary_to,
                                salary_currency = EXCLUDED.salary_currency,
                                salary_mid = EXCLUDED.salary_mid,
                                alternate_url = EXCLUDED.alternate_url;
                            """,
                            rows,
                        )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            logger.info(
                "Работодатель %s: в БД записано вакансий: %s",
                eid,
                len(rows),
            )
        logger.info("Загрузка с hh.ru завершена")
    finally:
        conn.close()
