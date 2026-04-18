from __future__ import annotations

from vacancies import compute_salary_mid, normalize_vacancy


def test_compute_salary_mid_none() -> None:
    assert compute_salary_mid(None) is None
    assert compute_salary_mid({}) is None


def test_compute_salary_mid_range() -> None:
    assert compute_salary_mid({"from": 100, "to": 200}) == 150


def test_compute_salary_mid_one_side() -> None:
    assert compute_salary_mid({"from": 80}) == 80
    assert compute_salary_mid({"to": 120}) == 120


def test_normalize_vacancy() -> None:
    item = {
        "id": 1,
        "name": " Dev ",
        "salary": {"from": 10, "to": 30, "currency": "RUR"},
        "alternate_url": "https://hh.ru/vacancy/1",
    }
    row = normalize_vacancy(item, 99)
    assert row[0] == 1 and row[1] == 99 and row[2] == "Dev"
    assert row[3] == 10 and row[4] == 30 and row[5] == "RUR"
    assert row[6] == 20
    assert row[7].startswith("http")


def test_normalize_vacancy_skips_non_rub() -> None:
    item = {
        "id": 2,
        "name": "X",
        "salary": {"from": 1000, "to": 2000, "currency": "USD"},
        "alternate_url": "https://hh.ru/vacancy/2",
    }
    row = normalize_vacancy(item, 1)
    assert row[3] is None and row[4] is None and row[5] is None and row[6] is None
