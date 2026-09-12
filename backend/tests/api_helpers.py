"""与 /api/v1 统一 APIResponse 及 axios 解包约定对齐的测试辅助。"""

from __future__ import annotations

from typing import Any


def api_payload(response) -> dict[str, Any]:
    body = response.json()
    assert isinstance(body, dict), body
    return body


def api_code(response) -> int:
    payload = api_payload(response)
    if "code" in payload:
        return int(payload["code"])
    return int(response.status_code)


def api_data(response) -> Any:
    payload = api_payload(response)
    assert api_code(response) == 0, payload
    return payload.get("data")


def assert_api_code(response, code: int) -> None:
    if response.status_code == code:
        return
    payload = api_payload(response)
    if isinstance(payload, dict) and "code" in payload:
        assert payload["code"] == code, payload
    else:
        assert response.status_code == code


def assert_api_code_in(response, codes: list[int]) -> None:
    payload = api_payload(response)
    if isinstance(payload, dict) and "code" in payload:
        assert payload["code"] in codes, payload
    else:
        assert response.status_code in codes


def login_json(username: str, password: str) -> dict[str, str]:
    return {"username_or_email": username, "password": password}


def extract_access_token(response) -> str:
    if response.status_code != 200:
        return ""
    try:
        data = api_data(response)
    except AssertionError:
        return ""
    if isinstance(data, dict):
        return str(data.get("access_token") or "")
    return ""
