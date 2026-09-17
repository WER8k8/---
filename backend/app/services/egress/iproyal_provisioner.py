# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""IPRoyal 缓冲池适配器 — 从预购池中分配IP，非实时下单。"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.egress import EgressEndpoint
from app.services.egress.provisioner import (
    EgressProvisionerError,
    PurchasedProxy,
)

logger = logging.getLogger(__name__)


class PoolExhaustedError(EgressProvisionerError):
    """缓冲池已空，需要触发批量补充。"""
    pass


class IPRoyalProvisioner:
    """从缓冲池分配 IPRoyal 静态住宅IP。

    与 MockProvisioner / AsocksProvisioner 不同：
    - 不直接调用第三方API下单
    - 从数据库中查找 status=available + provider=iproyal 的 EgressEndpoint
    - 找到 → 更新为 assigned 并返回 PurchasedProxy
    - 无可用 → 抛出 PoolExhaustedError，由上层触发补充
    """
    def purchase_one(self, *, country: str, region: str) -> PurchasedProxy:
        """purchase_one。

        参数说明：
        :param self: 参数 self
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """
        db: Session = SessionLocal()
        try:
            return self._allocate_from_pool(db, country=country, region=region)
        finally:
            db.close()

    def _allocate_from_pool(
        self,
        db: Session,
        *,
        country: str,
        region: str,
    ) -> PurchasedProxy:
        """_allocate_from_pool。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param country: 参数 country
        :param region: 参数 region
        :return: 返回处理结果。
        """
        # 优先分配可用的 IPRoyal IP
        endpoint = (
            db.query(EgressEndpoint)
            .filter(
                EgressEndpoint.slot_status == "available",
                EgressEndpoint.provider == "iproyal",
            )
            .order_by(EgressEndpoint.created_at.asc())  # FIFO
            .first()
        )
        if not endpoint:
            raise PoolExhaustedError(
                "IPRoyal 缓冲池已空，请触发补充或等待批量采购完成。"
            )

        # 标记为 provisioning，上层 JIT 服务会进一步设置为 assigned
        host = endpoint.host
        port = endpoint.port
        username = endpoint.proxy_username or ""
        password = endpoint.proxy_password or ""
        upstream_ref = endpoint.upstream_ref or str(endpoint.id)
        if not host or not username:
            raise EgressProvisionerError(
                f"IPRoyal endpoint {endpoint.id} 字段不完整"
            )

        return PurchasedProxy(
            host=host,
            port=port or 12323,
            proxy_username=username,
            proxy_password=password,
            upstream_ref=upstream_ref,
            provider="iproyal",
            label=f"IPRoyal 住宅ISP · {country}",
            raw={
                "endpoint_id": str(endpoint.id),
                "iproyal_order_id": endpoint.iproyal_order_id,
                "expire_date": endpoint.expire_date.isoformat() if endpoint.expire_date else None,
            },
        )
