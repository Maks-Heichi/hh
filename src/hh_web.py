from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

_SITE = "https://hh.ru"
_PAUSE_SEC = 0.35
_MAX_SEARCH_PAGES = 40
# (connect timeout, read timeout) — иначе на «висящем» TCP зависает весь процесс.
_REQUEST_TIMEOUT = (12, 90)


def _parse_salary_text(text: str) -> dict[str, Any] | None:
    """
    Парсит зарплату из строки выдачи hh.ru (только рубли).

    Примеры: "от 68 000 ₽", "до 120 000 руб.", "120 000–180 000 ₽".
    Иначе (доллары, евро, без валюты) — None.
    """
    s = (text or "").strip()
    if not s:
        return None

    s = s.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2009", " ")
    s_low = s.lower()
    if "не указ" in s_low:
        return None

    # «от 68 000 ₽ за месяц, до вычета налогов» — берём только кусок до запятой и до «за месяц»
    s = s.split(",")[0].strip()
    s = re.split(r"\s+за\s+", s, maxsplit=1, flags=re.I)[0].strip()
    s_low = s.lower()

    if "$" in s or "usd" in s_low or "€" in s or "eur" in s_low:
        return None

    if not ("₽" in s or "руб" in s_low or "rur" in s_low or "rub" in s_low):
        return None

    cur = "RUR"

    # числа (цифры с пробелами / unicode-пробелами между ними)
    nums: list[int] = []
    for chunk in re.findall(r"\d(?:[\d\s]+)?\d|\d{3,}", s):
        n = int(re.sub(r"\s+", "", chunk))
        nums.append(n)
    if not nums:
        return None

    s_from: int | None = None
    s_to: int | None = None

    if re.search(r"\bот\s*\d", s_low):
        s_from = nums[0]
    if re.search(r"\bдо\s*\d", s_low):
        s_to = nums[-1] if len(nums) >= 2 else nums[0]

    if s_from is None and s_to is None:
        if len(nums) >= 2 and re.search(
            r"\d(?:[\d\s]+)?\d\s*[–—-]\s*\d(?:[\d\s]+)?\d",
            s,
        ):
            s_from, s_to = nums[0], nums[1]
        else:
            s_from = nums[0]

    return {"from": s_from, "to": s_to, "currency": cur}


def _salary_line_from_vacancy_html(part: str) -> str | None:
    """Текст зарплаты из HTML-карточки вакансии (вёрстка hh.ru меняется)."""
    for m in re.finditer(
        r'magritte-text_typography-label-1-regular[^>]*>([\s\S]*?)</span>',
        part,
    ):
        raw = m.group(1)
        raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        low = line.lower()
        if "₽" in line or "руб" in low:
            return line
    legacy = re.search(
        r'data-qa="vacancy-serp__vacancy-compensation[^"]*"[^>]*>([^<]+)',
        part,
    )
    if legacy:
        t = legacy.group(1).strip()
        return t or None
    return None


def _browser_headers(user_agent: str | None) -> dict[str, str]:
    ua = (user_agent or "").strip() or (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
    }


def _parse_employer_from_html(html: str, employer_id: int) -> dict[str, Any] | None:
    """Имя и число вакансий из ``og:title`` страницы работодателя."""
    m = re.search(r'property="og:title"\s+content="([^"]+)"', html)
    if not m:
        return None
    title = m.group(1)
    name: str | None = None
    m2 = re.search(r"компании\s+(.+?)\s+в\s+", title)
    if m2:
        name = m2.group(1).strip()
    if not name:
        m3 = re.search(r"компании\s+(.+?)\s+—", title)
        if m3:
            name = m3.group(1).strip()
    if not name:
        name = f"employer_{employer_id}"
    open_cnt: int | None = None
    m4 = re.search(r"(\d+)\s+ваканс", title)
    if m4:
        open_cnt = int(m4.group(1))
    return {
        "id": employer_id,
        "name": name,
        "open_vacancies": open_cnt,
        "alternate_url": f"{_SITE}/employer/{employer_id}",
    }


def _parse_vacancy_cards(html: str) -> list[dict[str, Any]]:
    """Карточки выдачи ``/search/vacancy`` → словари в формате, похожем на элемент API."""
    chunks = re.split(r'data-qa="vacancy-serp__vacancy"', html)
    out: list[dict[str, Any]] = []
    for part in chunks[1:]:
        m_id = re.search(r"/vacancy/(\d+)", part)
        if not m_id:
            continue
        vid = int(m_id.group(1))
        m_title = re.search(
            r'data-qa="serp-item__title-text"[^>]*>([^<]+)',
            part,
        )
        title = (m_title.group(1).strip() if m_title else "").strip() or f"Vacancy {vid}"
        salary_raw = _salary_line_from_vacancy_html(part)
        salary = _parse_salary_text(salary_raw) if salary_raw else None
        out.append(
            {
                "id": vid,
                "name": title,
                "salary": salary,
                "alternate_url": f"{_SITE}/vacancy/{vid}",
            }
        )
    return out


class HeadHunterWeb:
    """Те же методы, что у ``HeadHunterAPI``, но запросы к HTML-страницам hh.ru."""

    def __init__(self, user_agent: str | None = None) -> None:
        self._session = requests.Session()
        self._session.headers.update(_browser_headers(user_agent))

    def get_employer(self, employer_id: int) -> dict[str, Any] | None:
        url = f"{_SITE}/employer/{employer_id}"
        try:
            response = self._session.get(url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            time.sleep(_PAUSE_SEC)
        except requests.RequestException as e:
            logger.warning("web employer %s: %s", employer_id, e)
            return None
        return _parse_employer_from_html(response.text, employer_id)

    def get_vacancies_for_employer(self, employer_id: int) -> list[dict[str, Any]]:
        seen: set[int] = set()
        merged: list[dict[str, Any]] = []
        for page in range(_MAX_SEARCH_PAGES):
            try:
                response = self._session.get(
                    f"{_SITE}/search/vacancy",
                    params={"employer_id": str(employer_id), "page": page},
                    timeout=_REQUEST_TIMEOUT,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                logger.warning("web vacancies employer=%s page=%s: %s", employer_id, page, e)
                break
            batch = _parse_vacancy_cards(response.text)
            new = [b for b in batch if b["id"] not in seen]
            if not new:
                break
            for b in new:
                seen.add(b["id"])
                merged.append(b)
            time.sleep(_PAUSE_SEC)
            if len(batch) < 5:
                break
        return merged
