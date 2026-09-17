# -*- coding: utf-8 -*-
"""内容 CMS 写操作属主校验测试（非全局超管不能操作他人页面）。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.api.v1.routes.content import _ensure_owned, _is_global_admin


class _U:
    def __init__(self, uid: str, role: str):
        self.id = uid
        self.role = role


def test_global_admin_skips_ownership_check():
    service = MagicMock()
    service.get_page = MagicMock(side_effect=AssertionError("不应查询"))
    # 平台超管直接放行，不查库
    _ensure_owned(service, "page-1", _U("u1", "super_admin"))


def test_tenant_admin_can_operate_own_page():
    service = MagicMock()
    page = MagicMock()
    page.author_id = "u2"
    service.get_page.return_value = page
    _ensure_owned(service, "page-1", _U("u2", "tenant_admin"))


def test_tenant_admin_cannot_operate_others_page():
    service = MagicMock()
    page = MagicMock()
    page.author_id = "u3"
    service.get_page.return_value = page
    with pytest.raises(ValueError, match="forbidden"):
        _ensure_owned(service, "page-1", _U("u2", "tenant_admin"))


def test_missing_page_raises_not_found():
    service = MagicMock()
    service.get_page.return_value = None
    with pytest.raises(ValueError, match="page_not_found"):
        _ensure_owned(service, "page-1", _U("u2", "tenant_admin"))


def test_is_global_admin_roles():
    assert _is_global_admin(_U("u1", "super_admin")) is True
    assert _is_global_admin(_U("u1", "admin")) is True
    assert _is_global_admin(_U("u1", "tenant_admin")) is False
    assert _is_global_admin(_U("u1", "editor")) is False
