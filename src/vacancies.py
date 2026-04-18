from __future__ import annotations

from typing import Any


def compute_salary_mid(raw: dict[str, Any] | None) -> int | None:
    """Одно число для зарплаты из блока salary; нет данных — None."""
    if not raw:
        return None
    f, t = raw.get("from"), raw.get("to")
    if f is not None and t is not None:
        return int((int(f) + int(t)) / 2)
    if f is not None:
        return int(f)
    if t is not None:
        return int(t)
    return None


def normalize_vacancy(
    item: dict[str, Any], employer_id: int
) -> tuple[int, int, str, int | None, int | None, str | None, int | None, str]:
    """Одна вакансия из `items` → кортеж для INSERT в `vacancies`."""
    vid = int(item["id"])
    name = str(item.get("name") or "").strip()
    sal = item.get("salary")
    if isinstance(sal, dict):
        cur = sal.get("currency")
        if cur is None or str(cur).upper() not in ("RUR", "RUB"):
            sal = None
    s_from = int(sal["from"]) if sal and sal.get("from") is not None else None
    s_to = int(sal["to"]) if sal and sal.get("to") is not None else None
    cur = str(sal["currency"]) if sal and sal.get("currency") else None
    mid = compute_salary_mid(sal if isinstance(sal, dict) else None)
    url = str(
        item.get("alternate_url")
        or item.get("url")
        or f"https://hh.ru/vacancy/{vid}"
    )
    return (vid, employer_id, name, s_from, s_to, cur, mid, url)
