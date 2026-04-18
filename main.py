from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from database import (
    HhDataSource,
    create_database_if_not_exists,
    create_tables,
    populate_from_hh,
)
from db_manager import DBManager
from file_storage import dotenv_path, load_database_settings, load_employer_ids
from hh_api import HeadHunterAPI
from hh_web import HeadHunterWeb
from user_interface import run_user_menu


def main() -> None:
    """Читает ``.env``, при необходимости создаёт БД и таблицы, загружает данные с hh.ru, открывает меню."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except OSError:
            pass
    settings = load_database_settings()
    hh_ua = (os.getenv("HH_USER_AGENT") or "").strip()
    if not hh_ua:
        logging.warning(
            "Нет HH_USER_AGENT (файл `%s`). Пример: HH_USER_AGENT=MyCourse/1.0 (you@mail.ru)",
            dotenv_path(),
        )
    elif "(" not in hh_ua or ")" not in hh_ua:
        logging.warning("HH_USER_AGENT лучше с email в скобках: MyCourse/1.0 (you@mail.ru)")
    mode = (os.getenv("HH_DATA_SOURCE") or "api").strip().lower()
    hh_client: HhDataSource
    if mode in ("web", "html", "site"):
        hh_client = HeadHunterWeb(user_agent=hh_ua or None)
        logging.info("Режим web: данные с сайта hh.ru, класс HeadHunterWeb")
    else:
        hh_client = HeadHunterAPI(user_agent=hh_ua or None)
        logging.info("Режим api: данные с api.hh.ru, класс HeadHunterAPI")

    create_database_if_not_exists(settings)
    create_tables(settings)
    populate_from_hh(settings, hh_client, load_employer_ids())
    run_user_menu(DBManager(settings))


if __name__ == "__main__":
    main()
