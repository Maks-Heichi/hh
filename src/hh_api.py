from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class HeadHunterAPI:
    """Работодатель и вакансии по id компании."""

    _BASE_URL = "https://api.hh.ru"
    _PER_PAGE = 100
    _PAUSE_SEC = 0.35
    _DEFAULT_USER_AGENT = "HH-Course-Project/1.0 (set HH_USER_AGENT in .env per api.hh.ru docs)"

    def __init__(self, user_agent: str | None = None) -> None:
        """Сессия с User-Agent: лучше передать строку из переменной окружения ``HH_USER_AGENT``."""
        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent or self._DEFAULT_USER_AGENT

    def get_employer(self, employer_id: int) -> dict[str, Any] | None:
        """Карточка работодателя или None при ошибке запроса."""
        url = f"{self._BASE_URL}/employers/{employer_id}"
        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self._PAUSE_SEC)
            return response.json()
        except requests.HTTPError as e:
            resp = e.response
            if resp is not None:
                logger.warning(
                    "employer %s: HTTP %s %s",
                    employer_id,
                    resp.status_code,
                    (resp.text or "")[:300],
                )
            else:
                logger.warning("employer %s: HTTP error %s", employer_id, e)
            return None
        except requests.RequestException as e:
            logger.warning("employer %s: %s", employer_id, e)
            return None

    def get_vacancies_for_employer(self, employer_id: int) -> list[dict[str, Any]]:
        """Все вакансии работодателя (все страницы /vacancies)."""
        out: list[dict[str, Any]] = []
        page = 0
        try:
            while True:
                response = self._session.get(
                    f"{self._BASE_URL}/vacancies",
                    params={
                        "employer_id": employer_id,
                        "page": page,
                        "per_page": self._PER_PAGE,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                payload = response.json()
                items = payload.get("items") or []
                out.extend(items)
                pages = int(payload.get("pages") or 0)
                time.sleep(self._PAUSE_SEC)
                if pages == 0 or page >= pages - 1:
                    break
                page += 1
        except requests.HTTPError as e:
            resp = e.response
            if resp is not None:
                logger.warning(
                    "vacancies employer=%s: HTTP %s %s",
                    employer_id,
                    resp.status_code,
                    (resp.text or "")[:300],
                )
            else:
                logger.warning("vacancies employer=%s: HTTP error %s", employer_id, e)
        except requests.RequestException as e:
            logger.warning("vacancies employer=%s: %s", employer_id, e)
        return out
