from __future__ import annotations

from hh_web import _parse_employer_from_html, _parse_salary_text, _parse_vacancy_cards


def test_parse_employer_from_og_title() -> None:
    html = (
        '<head><meta property="og:title" '
        'content="Работа в компании ТестКомпания в Москве — 7 вакансий на hh.ru">'
    )
    d = _parse_employer_from_html(html, 99)
    assert d is not None
    assert d["name"] == "ТестКомпания"
    assert d["open_vacancies"] == 7
    assert d["alternate_url"] == "https://hh.ru/employer/99"


def test_parse_vacancy_cards_minimal() -> None:
    html = """
data-qa="vacancy-serp__vacancy"
<a href="https://hh.ru/vacancy/1001"><span data-qa="serp-item__title-text" class="t">Аналитик</span></a>
data-qa="vacancy-serp__vacancy"
<a href="https://perm.hh.ru/vacancy/1002?x=1"><span data-qa="serp-item__title-text" class="t">Разработчик</span></a>
"""
    rows = _parse_vacancy_cards(html)
    assert len(rows) == 2
    assert rows[0]["id"] == 1001
    assert rows[0]["name"] == "Аналитик"
    assert rows[0]["salary"] is None
    assert rows[1]["id"] == 1002
    assert rows[1]["name"] == "Разработчик"


def test_parse_salary_text_variants() -> None:
    assert _parse_salary_text("з/п не указана") is None
    assert _parse_salary_text("от 68 000 ₽") == {"from": 68000, "to": None, "currency": "RUR"}
    assert _parse_salary_text("до 120 000 руб.") == {"from": None, "to": 120000, "currency": "RUR"}
    assert _parse_salary_text("120 000–180 000 ₽") == {"from": 120000, "to": 180000, "currency": "RUR"}
    assert _parse_salary_text("от 3000 USD") is None
    assert _parse_salary_text("100 000") is None


def test_parse_salary_ignores_gross_after_tax_tail() -> None:
    s = "от 68 000 ₽ за месяц, до вычета налогов"
    assert _parse_salary_text(s) == {"from": 68000, "to": None, "currency": "RUR"}


def test_parse_vacancy_cards_extracts_salary() -> None:
    html = """
data-qa="vacancy-serp__vacancy"
<a href="https://hh.ru/vacancy/1001"><span data-qa="serp-item__title-text">Аналитик</span></a>
<span class="magritte-text_typography-label-1-regular___x">от <!-- -->90 000<!-- --> ₽</span>
"""
    rows = _parse_vacancy_cards(html)
    assert rows[0]["salary"] == {"from": 90000, "to": None, "currency": "RUR"}
