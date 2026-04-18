from __future__ import annotations

from db_manager import DBManager


def _salary_text(mid: int | None) -> str:
    """Строка зарплаты для печати."""
    if mid is None:
        return "зарплата не указана"
    return f"{mid:,} руб. (оценка)".replace(",", " ")


def run_user_menu(db: DBManager) -> None:
    """Цикл меню: пункты вызывают методы `db`, печать — обычным текстом."""
    menu = (
        "\nМеню:\n"
        "1 — компании и число вакансий\n"
        "2 — все вакансии\n"
        "3 — средняя зарплата\n"
        "4 — вакансии выше средней\n"
        "5 — поиск по слову в названии\n"
        "0 — выход\n"
    )
    while True:
        print(menu)
        choice = input("Выберите пункт: ").strip()
        if choice == "0":
            print("До свидания.")
            return
        if choice == "1":
            rows = db.get_companies_and_vacancies_count()
            if not rows:
                print("Компаний нет.")
                continue
            print("Компании и число вакансий:")
            for company, cnt in rows:
                print(f"— {company}: {cnt} вакансий")
        elif choice == "2":
            rows = db.get_all_vacancies()
            if not rows:
                print("Вакансий нет.")
                continue
            print("Вакансии:")
            for company, title, mid, url in rows:
                print(f"— {company} | {title} | {_salary_text(mid)} | {url}")
        elif choice == "3":
            avg = db.get_avg_salary()
            if avg is None:
                print("Нет данных для средней зарплаты.")
            else:
                print(f"Средняя зарплата: {avg:,.2f} руб.".replace(",", " "))
        elif choice == "4":
            rows = db.get_vacancies_with_higher_salary()
            if not rows:
                print("Нет вакансий выше средней.")
                continue
            print("Выше средней:")
            for company, title, mid, url in rows:
                print(f"— {company} | {title} | {mid:,} руб. | {url}".replace(",", " "))
        elif choice == "5":
            kw = input("Слово для поиска: ").strip()
            if not kw:
                print("Пустой запрос.")
                continue
            rows = db.get_vacancies_with_keyword(kw)
            if not rows:
                print("Ничего не найдено.")
                continue
            print("Результат:")
            for company, title, url in rows:
                print(f"— {company} | {title} | {url}")
        else:
            print("Неизвестный пункт.")
