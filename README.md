# hh.ru → PostgreSQL

## Корень

- `main.py` — точка входа: `.env`, выбор API или веб-режима, БД, загрузка, меню.
- `requirements.txt` — зависимости Python.

## `src`

- `database.py` — создание БД и таблиц, очистка и заполнение из клиента hh.ru.
- `db_manager.py` — отчёты по БД для меню (JOIN, AVG, LIKE).
- `file_storage.py` — чтение `.env` и `data/employer_ids.json`.
- `pg_connection.py` — подключение к PostgreSQL.
- `hh_api.py` — данные с `api.hh.ru`.
- `hh_web.py` — данные с сайта `hh.ru` (HTML), если API недоступен; тот же сценарий, что у API-клиента.
- `vacancies.py` — приведение ответа hh.ru к полям для INSERT (зарплата только RUR/RUB).
- `user_interface.py` — консольное меню.

## `data`

- `employer_ids.json` — список id работодателей для загрузки.

## `tests`

- `test_*.py` — pytest по модулям `src`.
- `conftest.py` — общие фикстуры для тестов.

## Запуск

1. PostgreSQL, в корне файл `.env` (параметры БД, `HH_USER_AGENT`, при необходимости `HH_DATA_SOURCE=web` вместо `api`).
2. `pip install -r requirements.txt`
3. `python main.py`

## Тесты

```bash
pytest
```

При желании: `python -m flake8`.
