# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IPRoyal Reseller API 客户端 — 静态住宅IP自动采购。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

IPROYAL_API_BASE_DEFAULT = "https://apid.iproyal.com/v1/reseller"

# IPRoyal 默认代理端口（购买后固定）
_DEFAULT_HTTP_PORT = 12323
_DEFAULT_SOCKS_PORT = 12324


class IPRoyalAPIError(Exception):
    """IPRoyal API 调用失败。"""
    pass


@dataclass
class IPRoyalOrderResult:
    """下单成功后解析的结构化结果。"""
    order_id: int
    product_name: str
    plan_name: str
    expire_date: str
    status: str
    location: str
    quantity: int
    proxies: list[dict[str, Any]]
    ports: dict[str, Any]
    raw: dict[str, Any]


class IPRoyalClient:
    """IPRoyal Reseller REST API 封装。

    认证：Header ``X-Access-Token``。
    重试：指数退避，最多 3 次。
    """
    def __init__(
        self,
        api_token: str,
        api_base: str = IPROYAL_API_BASE_DEFAULT,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param api_token: 参数 api_token
        :param api_base: 参数 api_base
        :return: 返回处理结果。
        """
        self.api_token = api_token
        self.api_base = api_base.rstrip("/")

    # ── 公开方法 ────────────────────────────────────────────────
    def get_products(self) -> list[dict[str, Any]]:
        """获取产品列表。"""
        return self._get("/products")

    def create_order(
        self,
        *,
        product_id: int,
        plan_id: int,
        location_id: int,
        quantity: int = 5,
        auto_extend: bool = False,
        card_id: int | None = None,
    ) -> IPRoyalOrderResult:
        """下单购买静态住宅IP。

        Args:
            product_id: 产品ID（Static Residential = 9）
            plan_id: 计划ID（30天=3, 60天=4, 90天=5）
            location_id: 位置ID
            quantity: 数量（最低5）
            auto_extend: 是否自动续费
            card_id: 绑卡ID（None则用余额）

        Returns:
            IPRoyalOrderResult 包含订单详情和代理列表
        """
        body: dict[str, Any] = {
            "product_id": product_id,
            "product_plan_id": plan_id,
            "product_location_id": location_id,
            "quantity": max(5, quantity),
        }
        if auto_extend:
            body["auto_extend"] = True
        if card_id is not None:
            body["card_id"] = card_id

        data = self._post("/orders", body)
        return self._parse_order(data)

    def get_order(self, order_id: int) -> IPRoyalOrderResult:
        """查询单个订单详情。"""
        data = self._get(f"/orders/{order_id}")
        return self._parse_order(data)

    def list_orders(
        self,
        *,
        product_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        """查询订单列表。"""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if product_id is not None:
            params["product_id"] = product_id
        if status:
            params["status"] = status
        result = self._get("/orders", params=params)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("data", [])
        return []

    def extend_order(
        self,
        order_id: int,
        *,
        plan_id: int,
        proxies: list[str] | None = None,
    ) -> dict[str, Any]:
        """续费订单（保持原IP不变）。

        Args:
            order_id: 要续费的订单ID
            plan_id: 续费计划ID（30/60/90天）
            proxies: 要续费的代理IP列表（空则续费全部）
        """
        body: dict[str, Any] = {"product_plan_id": plan_id}
        if proxies:
            body["proxies"] = proxies
        return self._post(f"/orders/{order_id}/extend", body)

    def get_account_balance(self) -> dict[str, Any]:
        """查询账户余额。"""
        return self._get("/account/balance")

    # ── 内部方法 ────────────────────────────────────────────────
    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """_get。

        参数说明：
        :param self: 参数 self
        :param path: 参数 path
        :param params: 参数 params
        :return: 返回处理结果。
        """
        return self._request("GET", path, params=params)

    def _post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """_post。

        参数说明：
        :param self: 参数 self
        :param path: 参数 path
        :param body: 参数 body
        :return: 返回处理结果。
        """
        return self._request("POST", path, json_body=body)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """_request。

        参数说明：
        :param self: 参数 self
        :param method: 参数 method
        :param path: 参数 path
        :param params: 参数 params
        :param json_body: 参数 json_body
        :return: 返回处理结果。
        """
        url = f"{self.api_base}{path}"
        headers = {
            "X-Access-Token": self.api_token,
            "Content-Type": "application/json",
        }
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.request(
                        method, url, headers=headers,
                        params=params, json=json_body,
                    )
                    if resp.status_code == 429:
                        wait = min(2 ** attempt * 2, 30)
                        logger.warning("IPRoyal rate limited, wait %ds", wait)
                        time.sleep(wait)
                        continue
                    if resp.status_code >= 400:
                        raise IPRoyalAPIError(
                            f"IPRoyal HTTP {resp.status_code}: {resp.text[:300]}"
                        )
                    return resp.json()
            except httpx.TimeoutException as exc:
                last_exc = exc
                wait = min(2 ** attempt * 2, 30)
                logger.warning("IPRoyal timeout (attempt %d), retry in %ds", attempt + 1, wait)
                time.sleep(wait)
            except IPRoyalAPIError:
                raise
            except Exception as exc:
                last_exc = exc
                wait = min(2 ** attempt * 2, 30)
                logger.warning("IPRoyal error (attempt %d): %s", attempt + 1, exc)
                time.sleep(wait)

        raise IPRoyalAPIError(f"IPRoyal API 请求失败（重试3次后）: {last_exc}")

    def _parse_order(self, data: Any) -> IPRoyalOrderResult:
        """解析 IPRoyal 订单响应为结构化结果。"""
        if not isinstance(data, dict):
            raise IPRoyalAPIError(f"IPRoyal 订单响应格式异常: {type(data)}")

        proxy_data = data.get("proxy_data") or {}
        ports = proxy_data.get("ports") or {}
        proxies_raw = proxy_data.get("proxies") or []
        proxies: list[dict[str, Any]] = []
        for p in proxies_raw:
            if isinstance(p, dict):
                proxies.append(p)
            elif isinstance(p, str):
                # 某些返回纯字符串 IP
                proxies.append({"ip": p})

        return IPRoyalOrderResult(
            order_id=data.get("id", 0),
            product_name=data.get("product_name", ""),
            plan_name=data.get("plan_name", ""),
            expire_date=data.get("expire_date", ""),
            status=data.get("status", ""),
            location=data.get("location", data.get("locations", "")),
            quantity=data.get("quantity", len(proxies)),
            proxies=proxies,
            ports=ports,
            raw=data,
        )
