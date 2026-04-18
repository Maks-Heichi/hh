from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from hh_api import HeadHunterAPI


@patch("hh_api.time.sleep", return_value=None)
def test_get_employer_ok(_sleep: MagicMock) -> None:
    api = HeadHunterAPI()
    fake = MagicMock()
    fake.raise_for_status = MagicMock()
    fake.json.return_value = {"id": 1, "name": "Co"}
    with patch.object(api._session, "get", return_value=fake):
        assert api.get_employer(1) == {"id": 1, "name": "Co"}


@patch("hh_api.time.sleep", return_value=None)
def test_get_employer_error_returns_none(_sleep: MagicMock) -> None:
    api = HeadHunterAPI()
    with patch.object(
        api._session,
        "get",
        side_effect=requests.RequestException("net"),
    ):
        assert api.get_employer(1) is None


@patch("hh_api.time.sleep", return_value=None)
def test_get_vacancies_for_employer_pages(_sleep: MagicMock) -> None:
    api = HeadHunterAPI()

    def fake_get(_url: str, **kwargs: object) -> MagicMock:
        page = int(kwargs["params"]["page"])
        r = MagicMock()
        r.raise_for_status = MagicMock()
        if page == 0:
            r.json.return_value = {"items": [{"id": 1}], "pages": 2}
        else:
            r.json.return_value = {"items": [{"id": 2}], "pages": 2}
        return r

    with patch.object(api._session, "get", side_effect=fake_get):
        items = api.get_vacancies_for_employer(5)
    assert [x["id"] for x in items] == [1, 2]
