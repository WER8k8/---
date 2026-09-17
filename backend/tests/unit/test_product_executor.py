# -*- coding: utf-8 -*-
"""ProductExecutor 契约回归测试（不连真库）。"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.hermes_orchestration import TaskNode
from app.services.hermes.executors.base import ExecutorContext
from app.services.hermes.executors.product_executor import ProductExecutor


def _ctx() -> ExecutorContext:
    return ExecutorContext(db=MagicMock(), tenant_id="tenant-1", plan_id="plan-1")


def _node(**inp) -> TaskNode:
    return TaskNode(id="n1", executor="product", capability="product.create",
                    depends_on=[], input=inp)


def test_success_returns_product_id_and_slug():
    """成功路径：真实 create_product 返回 Product，执行器透传字段。"""
    fake_product = MagicMock()
    fake_product.id = "prod-001"
    fake_product.slug = "cement-bags"
    fake_product.name = "水泥袋"

    with patch("app.services.product_service.ProductService") as MockSvc:
        MockSvc.return_value.create_product.return_value = fake_product
        result = asyncio.run(ProductExecutor().run(
            _node(title="水泥袋", slug="cement-bags", category_id="cat-1"),
            _ctx()))

    assert result.status == "succeeded"
    assert result.output["product_id"] == "prod-001"
    assert result.output["slug"] == "cement-bags"
    assert result.output["status"] == "created"


def test_missing_title_fails():
    """缺 title/name 必须返回 failed。"""
    result = asyncio.run(ProductExecutor().run(_node(), _ctx()))
    assert result.status == "failed"
    assert "missing_title" in (result.error or "")


def test_slug_conflict_returns_failed():
    """slug 唯一校验冲突 → 明确 failed，不抛异常给调用方。"""
    with patch("app.services.product_service.ProductService") as MockSvc:
        MockSvc.return_value.create_product.side_effect = ValueError("产品slug已存在")
        result = asyncio.run(ProductExecutor().run(
            _node(title="水泥袋", slug="duplicate-slug", category_id="cat-1"),
            _ctx()))

    assert result.status == "failed"
    assert "slug_conflict" in (result.error or "")
