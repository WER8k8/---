# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""清除历史演示 IP 槽位（禁止假数据进入平台池统计）。"""

from __future__ import annotations

import ipaddress

from sqlalchemy.orm import Session

from app.models.egress import EgressEndpoint

_DEMO_PROVIDERS = frozenset({"演示供应商 A", "Demo Provider B", "mock", "demo"})
_DEMO_ID_PREFIX = "egress-demo-"
_RFC5737_NETWORKS = (
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
)


def _is_rfc5737_host(host: str) -> bool:
    """实现 isrfc5737host 的功能。
    
    :param host: 参数 host（类型: str）
    :return: 返回 bool 结果
    """
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(addr in net for net in _RFC5737_NETWORKS)


def is_demo_egress_endpoint(row: EgressEndpoint) -> bool:
    """实现 isdemoegressendpoint 的功能。
    
    :param row: 参数 row（类型: EgressEndpoint）
    :return: 返回 bool 结果
    """
    host = (row.host or "").strip().lower()
    provider = (row.provider or "").strip()
    eid = str(row.id or "")
    if eid.startswith(_DEMO_ID_PREFIX):
        return True
    if host in {"(待运营配置)", "(开通中)", ""}:
        return False
    if host.endswith(".mock-egress.local"):
        return True
    if _is_rfc5737_host(host):
        return True
    if provider in _DEMO_PROVIDERS:
        return True
    if provider.lower() in {"mock", "demo"}:
        return True
    return False


def purge_demo_egress_endpoints(db: Session) -> int:
    """删除平台池中标记为演示/占位的 egress 行（幂等）。"""
    rows = db.query(EgressEndpoint).all()
    removed = 0
    for row in rows:
        if not is_demo_egress_endpoint(row):
            continue
        db.delete(row)
        removed += 1
    if removed:
        db.flush()
    return removed
