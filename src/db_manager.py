from __future__ import annotations

from psycopg2.extensions import connection as PgConnection

from file_storage import DatabaseSettings
from pg_connection import connect_postgres


class DBManager:
    """Только SQL-выборки; настройки подключения в `DatabaseSettings`."""

    def __init__(self, settings: DatabaseSettings) -> None:
        """Подключение к базе `settings.name`."""
        self._settings = settings

    def _connect(self) -> PgConnection:
        """Соединение с рабочей БД проекта."""
        return connect_postgres(self._settings, dbname=self._settings.name)

    def get_companies_and_vacancies_count(self) -> list[tuple[str, int]]:
        """Название компании и число её вакансий."""
        q = """
            SELECT e.name, COUNT(v.vacancy_id)::int
            FROM employers AS e
            LEFT JOIN vacancies AS v ON e.employer_id = v.employer_id
            GROUP BY e.employer_id, e.name
            ORDER BY e.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(q)
                rows = cur.fetchall()
            return [(str(r[0]), int(r[1])) for r in rows]
        finally:
            conn.close()

    def get_all_vacancies(self) -> list[tuple[str, str, int | None, str]]:
        """Компания, вакансия, оценка зарплаты (salary_mid), ссылка."""
        q = """
            SELECT e.name, v.name, v.salary_mid, v.alternate_url
            FROM vacancies AS v
            INNER JOIN employers AS e ON v.employer_id = e.employer_id
            ORDER BY e.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(q)
                return [
                    (str(a), str(b), int(c) if c is not None else None, str(d))
                    for a, b, c, d in cur.fetchall()
                ]
        finally:
            conn.close()

    def get_avg_salary(self) -> float | None:
        """Среднее по полю salary_mid (только где зарплата задана)."""
        q = """
            SELECT AVG(salary_mid)
            FROM vacancies
            WHERE salary_mid IS NOT NULL;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(q)
                row = cur.fetchone()
            if not row or row[0] is None:
                return None
            return float(row[0])
        finally:
            conn.close()

    def get_vacancies_with_higher_salary(self) -> list[tuple[str, str, int, str]]:
        """Вакансии, у которых salary_mid выше среднего по таблице."""
        q = """
            SELECT e.name, v.name, v.salary_mid, v.alternate_url
            FROM vacancies AS v
            INNER JOIN employers AS e ON v.employer_id = e.employer_id
            WHERE v.salary_mid IS NOT NULL
              AND v.salary_mid > (
                  SELECT AVG(salary_mid)
                  FROM vacancies
                  WHERE salary_mid IS NOT NULL
              )
            ORDER BY v.salary_mid DESC, e.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(q)
                return [(str(r[0]), str(r[1]), int(r[2]), str(r[3])) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_vacancies_with_keyword(self, keyword: str) -> list[tuple[str, str, str]]:
        """Вакансии, в названии которых есть `keyword` (SQL LIKE)."""
        q = """
            SELECT e.name, v.name, v.alternate_url
            FROM vacancies AS v
            INNER JOIN employers AS e ON v.employer_id = e.employer_id
            WHERE v.name LIKE %s
            ORDER BY e.name, v.name;
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(q, (f"%{keyword}%",))
                return [(str(r[0]), str(r[1]), str(r[2])) for r in cur.fetchall()]
        finally:
            conn.close()
