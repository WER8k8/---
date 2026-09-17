# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""出口 IP — manual 运营录入 / mock 演示 / asocks JIT 采购 / iproyal 长期养号。"""

from __future__ import annotations

import logging
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ASOCKS_API_BASE_DEFAULT = "https://api.asocks.com"
AUTO_EGRESS_PROVIDERS = frozenset({"mock", "asocks", "iproyal"})


class EgressProvisionerError(Exception):
    pass


@dataclass
class PurchasedProxy:
    host: str
    port: int
    proxy_username: str
    proxy_password: str
    upstream_ref: str
    provider: str
    label: str | None = None
    raw: dict[str, Any] | None = None


class EgressProvisioner(Protocol):
    def purchase_one(self, *, country: str, region: str) -> PurchasedProxy:
        """purchase_one。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """


def active_egress_provider() -> str:
    """实现 activeegress提供商 的功能。
    
    :return: 返回 str 结果
    """
    return (settings.EGRESS_PROVIDER or "manual").strip().lower()


def is_manual_egress_mode() -> bool:
    """实现 ismanualegress模式 的功能。
    
    :return: 返回 bool 结果
    """
    return active_egress_provider() == "manual"


def is_auto_egress_mode() -> bool:
    """实现 isautoegress模式 的功能。
    
    :return: 返回 bool 结果
    """
    return active_egress_provider() in AUTO_EGRESS_PROVIDERS


@dataclass
class MockProvisioner:
    """开发演示：模拟上游采购，无真实费用。"""
    delay_sec: float = 0.0
    def purchase_one(self, *, country: str, region: str) -> PurchasedProxy:
        """purchase_one。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """
        if self.delay_sec > 0:
            time.sleep(min(self.delay_sec, 30.0))
        token = secrets.token_hex(4)
        ref = f"mock-{uuid.uuid4().hex[:12]}"
        return PurchasedProxy(
            host=f"{country.lower()}-isp-{token}.mock-egress.local",
            port=1080,
            proxy_username=f"tenant_{token}",
            proxy_password=secrets.token_urlsafe(16),
            upstream_ref=ref,
            provider="mock",
            label=f"{country} ISP (演示)",
        )


def _pick_str(obj: dict[str, Any], *keys: str) -> str | None:
    """实现 pickstr 的功能。
    
    :param obj: 参数 obj（类型: dict[str, Any]）
    :param keys: 参数 keys（类型: str）
    :return: 返回 str | None 结果
    """
    for key in keys:
        val = obj.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _pick_int(obj: dict[str, Any], *keys: str) -> int | None:
    """实现 pickint 的功能。
    
    :param obj: 参数 obj（类型: dict[str, Any]）
    :param keys: 参数 keys（类型: str）
    :return: 返回 int | None 结果
    """
    for key in keys:
        val = obj.get(key)
        if val is None:
            continue
        try:
            return int(val)
        except (TypeError, ValueError):
            continue
    return None


def _parse_proxy_endpoint(
    host: str, port: int, username: str, password: str, *, upstream_ref: str, raw: Any
) -> PurchasedProxy:
    """实现 解析proxyendpoint 的功能。
    
    :param host: 参数 host（类型: str）
    :param port: 参数 port（类型: int）
    :param username: 参数 username（类型: str）
    :param password: 参数 password（类型: str）
    :param upstream_ref: 参数 upstream_ref（类型: str）
    :param raw: 参数 raw（类型: Any）
    :return: 返回 PurchasedProxy 结果
    :raises EgressProvisionerError: 当操作失败时抛出 EgressProvisionerError 异常
    """
    if not host or not port or not username or not password:
        raise EgressProvisionerError("上游返回的代理字段不完整")
    return PurchasedProxy(
        host=host,
        port=port,
        proxy_username=username,
        proxy_password=password,
        upstream_ref=upstream_ref,
        provider="asocks",
        label="ASocks 住宅代理",
        raw=raw if isinstance(raw, dict) else {"raw": raw},
    )


def parse_asocks_proxy_line(line: str) -> tuple[str, int, str, str]:
    """解析 ASocks 链接模板输出（curl / http / raw）。"""
    text = (line or "").strip()
    if not text:
        raise EgressProvisionerError("空代理行")

    curl_match = re.search(
        r"https?://([^:@\s]+):([^@\s]+)@([^:\s]+):(\d+)",
        text,
    )
    if curl_match:
        user, pwd, host, port = curl_match.groups()
        return host, int(port), user, pwd

    proxy_match = re.search(
        r"(?:socks5?|https?)://([^:@\s]+):([^@\s]+)@([^:\s]+):(\d+)",
        text,
        flags=re.IGNORECASE,
    )
    if proxy_match:
        user, pwd, host, port = proxy_match.groups()
        return host, int(port), user, pwd

    if "@" in text and "://" not in text:
        creds, endpoint = text.rsplit("@", 1)
        if ":" in creds and ":" in endpoint:
            user, pwd = creds.split(":", 1)
            host, port_s = endpoint.rsplit(":", 1)
            return host.strip(), int(port_s.strip()), user.strip(), pwd.strip()

    parts = text.split(":")
    if len(parts) >= 4 and parts[1].isdigit():
        return parts[0], int(parts[1]), parts[2], ":".join(parts[3:])

    raise EgressProvisionerError(f"无法解析 ASocks 代理格式: {text[:80]}")


def parse_asocks_port_record(item: dict[str, Any]) -> PurchasedProxy:
    """解析 create-port / ports 列表中的单条记录。"""
    host = _pick_str(
        item,
        "server",
        "host",
        "ip",
        "proxy_host",
        "address",
        "proxy",
    )
    port = _pick_int(item, "port", "server_port", "proxy_port")
    username = _pick_str(item, "login", "username", "user", "proxy_login")
    password = _pick_str(item, "password", "pass", "proxy_password")
    if host and ":" in host and port is None:
        host_part, port_part = host.rsplit(":", 1)
        if port_part.isdigit():
            host, port = host_part, int(port_part)

    ref = _pick_str(item, "id", "port_id", "uuid") or f"asocks-{uuid.uuid4().hex[:12]}"
    return _parse_proxy_endpoint(
        host or "",
        port or 0,
        username or "",
        password or "",
        upstream_ref=str(ref),
        raw=item,
    )


def _asocks_api_request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    api_key: str,
    api_base: str,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """实现 asocksAPI请求 的功能。
    
    :param client: 参数 client（类型: httpx.Client）
    :param method: 参数 method（类型: str）
    :param path: 参数 path（类型: str）
    :param api_key: 参数 api_key（类型: str）
    :param api_base: 参数 api_base（类型: str）
    :param json_body: 参数 json_body（类型: dict[str, Any] | None）
    :param params: 参数 params（类型: dict[str, Any] | None）
    :return: 返回 dict[str, Any] 结果
    :raises EgressProvisionerError: 当操作失败时抛出 EgressProvisionerError 异常
    """
    query = dict(params or {})
    query["apiKey"] = api_key
    url = f"{api_base.rstrip('/')}{path}"
    resp = client.request(method, url, params=query, json=json_body)
    try:
        data = resp.json()
    except Exception as exc:
        raise EgressProvisionerError(
            f"ASocks 响应非 JSON (HTTP {resp.status_code}): {resp.text[:200]}"
        ) from exc
    if resp.status_code >= 400:
        raise EgressProvisionerError(
            f"ASocks HTTP {resp.status_code}: {data}"
        )
    if isinstance(data, dict) and data.get("success") is False:
        raise EgressProvisionerError(f"ASocks 业务失败: {data}")
    if not isinstance(data, dict):
        raise EgressProvisionerError(f"ASocks 响应格式异常: {data!r}")
    return data


def _extract_port_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """实现 提取port条目 的功能。
    
    :param payload: 参数 payload（类型: dict[str, Any]）
    :return: 返回 list[dict[str, Any]] 结果
    """
    items: list[dict[str, Any]] = []
    data = payload.get("data")
    if isinstance(data, list):
        items.extend(x for x in data if isinstance(x, dict))
    message = payload.get("message")
    if isinstance(message, dict):
        for key in ("data", "items", "ports", "list"):
            nested = message.get(key)
            if isinstance(nested, list):
                items.extend(x for x in nested if isinstance(x, dict))
    elif isinstance(message, list):
        items.extend(x for x in message if isinstance(x, dict))
    return items


@dataclass
class AsocksProvisioner:
    """ASocks JIT：POST /v2/proxy/create-port；可回退到链接列表。"""
    api_key: str
    api_base: str = ASOCKS_API_BASE_DEFAULT
    traffic_limit_gb: int = 10
    type_id: int | None = None
    proxy_type_id: int | None = None
    list_url: str | None = None
    list_type: str = "res"
    def purchase_one(self, *, country: str, region: str) -> PurchasedProxy:
        """purchase_one。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """
        if self.api_key:
            try:
                return self._purchase_via_create_port(country=country, region=region)
            except EgressProvisionerError as exc:
                if not self.list_url:
                    raise
                logger.warning("ASocks create-port failed, fallback to list: %s", exc)
        if self.list_url:
            return self._purchase_via_list(country=country)
        raise EgressProvisionerError("请配置 ASOCKS_API_KEY 或 ASOCKS_LIST_URL")

    def _purchase_via_create_port(self, *, country: str, region: str) -> PurchasedProxy:
        """_purchase_via_create_port。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """
        body: dict[str, Any] = {
            "country_code": country.upper(),
            "name": f"youding-{region}-{uuid.uuid4().hex[:10]}",
            "traffic_limit": max(1, int(self.traffic_limit_gb)),
        }
        if self.type_id is not None:
            body["type_id"] = self.type_id
        if self.proxy_type_id is not None:
            body["proxy_type_id"] = self.proxy_type_id

        with httpx.Client(timeout=120.0) as client:
            payload = _asocks_api_request(
                client,
                "POST",
                "/v2/proxy/create-port",
                api_key=self.api_key,
                api_base=self.api_base,
                json_body=body,
            )
            items = _extract_port_items(payload)
            if items:
                return parse_asocks_port_record(items[0])

            port_id = payload.get("id") or _pick_int(payload, "port_id")
            if port_id is None and isinstance(payload.get("data"), dict):
                port_id = _pick_int(payload["data"], "id", "port_id")
            if port_id is not None:
                detail = _asocks_api_request(
                    client,
                    "GET",
                    "/v2/proxy/ports",
                    api_key=self.api_key,
                    api_base=self.api_base,
                    params={"id": port_id, "per_page": 1},
                )
                detail_items = _extract_port_items(detail)
                if detail_items:
                    return parse_asocks_port_record(detail_items[0])

        raise EgressProvisionerError(f"ASocks create-port 未返回可用代理: {payload}")

    def _purchase_via_list(self, *, country: str) -> PurchasedProxy:
        """_purchase_via_list。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :return: 返回处理结果。
        """
        parsed = urlparse(self.list_url or "")
        query = parse_qs(parsed.query)
        query["limit"] = ["1"]
        query["type"] = [self.list_type or "res"]
        if country:
            query["country"] = [country.upper()]
        new_query = urlencode({k: v[0] for k, v in query.items()})
        url = urlunparse(parsed._replace(query=new_query))
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(url)
        if resp.status_code >= 400:
            raise EgressProvisionerError(
                f"ASocks 列表 HTTP {resp.status_code}: {resp.text[:200]}"
            )

        lines: list[str] = []
        try:
            payload = resp.json()
        except Exception:
            payload = None

        if isinstance(payload, list):
            lines = [str(x) for x in payload if str(x).strip()]
        elif isinstance(payload, dict):
            for key in ("data", "proxies", "list", "items"):
                val = payload.get(key)
                if isinstance(val, list):
                    lines = [str(x) for x in val if str(x).strip()]
                    break
        if not lines:
            lines = [ln.strip() for ln in resp.text.splitlines() if ln.strip()]

        if not lines:
            raise EgressProvisionerError("ASocks 列表为空，请检查余额与链接参数")

        host, port, user, pwd = parse_asocks_proxy_line(lines[0])
        ref = f"asocks-list-{uuid.uuid4().hex[:12]}"
        return _parse_proxy_endpoint(
            host,
            port,
            user,
            pwd,
            upstream_ref=ref,
            raw={"line": lines[0], "source": "list"},
        )


def run_egress_qc(host: str, *, provider: str | None = None) -> dict[str, Any]:
    """实现 执行egressqc 的功能。
    
    :param host: 参数 host（类型: str）
    :param provider: 参数 provider（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    if provider == "asocks":
        return {"ok": True, "skipped": True, "reason": "asocks_residential"}
    if provider == "iproyal":
        # IPRoyal 静态住宅IP：做增强QC（双ISP验证）
        return _run_iproyal_qc(host)
    if host.endswith(".mock-egress.local") or "mock" in host:
        return {"ok": True, "skipped": True, "reason": "mock_host"}
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"http://ip-api.com/json/{host}",
                params={"fields": "status,message,query,isp,org,proxy,hosting"},
            )
        data = resp.json()
        if data.get("status") != "success":
            return {"ok": False, "raw": data}
        hosting = bool(data.get("hosting"))
        proxy_flag = bool(data.get("proxy"))
        ok = not hosting and not proxy_flag
        return {
            "ok": ok,
            "isp": data.get("isp"),
            "org": data.get("org"),
            "hosting": hosting,
            "proxy": proxy_flag,
        }
    except Exception as exc:
        logger.warning("egress QC failed for %s: %s", host, exc)
        return {"ok": True, "skipped": True, "reason": "qc_unreachable"}


def _run_iproyal_qc(host: str) -> dict[str, Any]:
    """IPRoyal 静态住宅IP增强QC：ip-api.com + ipinfo.io 双源验证。"""
    result: dict[str, Any] = {"provider": "iproyal", "dual_isp": False}
    try:
        with httpx.Client(timeout=15.0) as client:
            # 数据源1: ip-api.com
            resp1 = client.get(
                f"http://ip-api.com/json/{host}",
                params={"fields": "status,message,query,isp,org,proxy,hosting,as"},
            )
            d1 = resp1.json()
            if d1.get("status") != "success":
                result["ok"] = False
                result["raw_ipapi"] = d1
                return result

            hosting = bool(d1.get("hosting"))
            proxy_flag = bool(d1.get("proxy"))
            result["isp"] = d1.get("isp")
            result["org"] = d1.get("org")
            result["as_info"] = d1.get("as")
            result["hosting"] = hosting
            result["proxy"] = proxy_flag
            if hosting or proxy_flag:
                result["ok"] = False
                result["reason"] = f"hosting={hosting} proxy={proxy_flag}"
                return result

        # 数据源2: ipinfo.io（免费100K/月）
        try:
            with httpx.Client(timeout=10.0) as client:
                resp2 = client.get(f"https://ipinfo.io/{host}/json")
                d2 = resp2.json()
                result["ipinfo_org"] = d2.get("org", "")
                result["ipinfo_hostname"] = d2.get("hostname", "")
                # 双ISP检测：两个数据源的ASN/ISP不同 = 更可能是真实双ISP
                isp1 = (d1.get("isp") or "").lower()
                org2 = (d2.get("org") or "").lower()
                if isp1 and org2 and isp1 not in org2 and org2 not in isp1:
                    result["dual_isp"] = True
                    result["isp_source2"] = org2
        except Exception:
            result["ipinfo_skipped"] = True

        result["ok"] = True
        return result

    except Exception as exc:
        logger.warning("IPRoyal QC failed for %s: %s", host, exc)
        return {"ok": True, "skipped": True, "reason": "qc_unreachable"}


def get_egress_provisioner() -> EgressProvisioner:
    """实现 获取egressprovisioner 的功能。
    
    :return: 返回 EgressProvisioner 结果
    :raises EgressProvisionerError: 当操作失败时抛出 EgressProvisionerError 异常
    """
    name = active_egress_provider()
    if name == "mock":
        return MockProvisioner(delay_sec=float(settings.EGRESS_MOCK_DELAY_SEC or 0))
    if name == "asocks":
        api_key = (settings.ASOCKS_API_KEY or "").strip()
        list_url = (settings.ASOCKS_LIST_URL or "").strip() or None
        if not api_key and not list_url:
            raise EgressProvisionerError(
                "EGRESS_PROVIDER=asocks 时需配置 ASOCKS_API_KEY 或 ASOCKS_LIST_URL"
            )
        type_id = settings.ASOCKS_TYPE_ID
        proxy_type_id = settings.ASOCKS_PROXY_TYPE_ID
        return AsocksProvisioner(
            api_key=api_key,
            api_base=(settings.ASOCKS_API_BASE or ASOCKS_API_BASE_DEFAULT).strip(),
            traffic_limit_gb=int(settings.ASOCKS_TRAFFIC_LIMIT_GB or 10),
            type_id=int(type_id) if type_id is not None else None,
            proxy_type_id=int(proxy_type_id) if proxy_type_id is not None else None,
            list_url=list_url,
            list_type=(settings.ASOCKS_LIST_TYPE or "res").strip(),
        )
    if name == "iproyal":
        from app.services.egress.iproyal_provisioner import IPRoyalProvisioner
        if not (settings.IPROYAL_API_TOKEN or "").strip():
            raise EgressProvisionerError(
                "EGRESS_PROVIDER=iproyal 时需配置 IPROYAL_API_TOKEN"
            )
        return IPRoyalProvisioner()
    raise EgressProvisionerError(
        "当前为运营人工配置模式，不调用第三方 API。"
        "自动开通请设置 EGRESS_PROVIDER=asocks / mock / iproyal"
    )

