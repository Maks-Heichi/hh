from __future__ import annotations

from unittest.mock import MagicMock, patch

from user_interface import run_user_menu


def test_run_user_menu_exit() -> None:
    fake_db = MagicMock()
    with patch("builtins.input", side_effect=["0"]), patch("builtins.print") as pr:
        run_user_menu(fake_db)
    fake_db.assert_not_called()
    printed = " ".join(str(c.args[0]) for c in pr.call_args_list)
    assert "До свидания" in printed


def test_run_user_menu_option1() -> None:
    fake_db = MagicMock()
    fake_db.get_companies_and_vacancies_count.return_value = [("A", 2)]
    with patch("builtins.input", side_effect=["1", "0"]), patch("builtins.print"):
        run_user_menu(fake_db)
    fake_db.get_companies_and_vacancies_count.assert_called_once()
