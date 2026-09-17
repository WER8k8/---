# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""SaaS多租户服务层"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.tenant import Tenant, TenantInvoice, TenantPlan, TenantSubscription
from app.repositories.tenant_repository import (
    TenantInvoiceRepository,
    TenantPlanRepository,
    TenantRepository,
    TenantSubscriptionRepository,
)
from app.schemas.tenant import (
    TenantBrandConfig,
    TenantCreate,
    TenantOverviewResponse,
    TenantPlanCreate,
    TenantPlanUpdate,
    TenantPublicResponse,
    TenantResponse,
    TenantStatsResponse,
    TenantUpdate,
    WhiteLabelConfig,
    WhiteLabelUpdate,
)


class TenantPlanService:
    """套餐服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.plan_repo = TenantPlanRepository(db)

    def list_plans(self) -> list[TenantPlan]:
        """获取所有套餐"""
        return self.plan_repo.get_active_plans()

    def get_plan(self, plan_id: str) -> Optional[TenantPlan]:
        """获取单个套餐"""
        return self.plan_repo.get_by_id(plan_id)

    def create_plan(self, data: TenantPlanCreate) -> TenantPlan:
        """创建套餐"""
        if self.plan_repo.exists(code=data.code):
            raise ValueError(f"套餐编码 '{data.code}' 已存在")
        return self.plan_repo.create(**data.model_dump())

    def update_plan(self, plan_id: str, data: TenantPlanUpdate) -> Optional[TenantPlan]:
        """更新套餐"""
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            return None
        return self.plan_repo.update(plan_id, **data.model_dump(exclude_unset=True))


class TenantService:
    """租户服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.tenant_repo = TenantRepository(db)
        self.plan_repo = TenantPlanRepository(db)
        self.sub_repo = TenantSubscriptionRepository(db)
        self.invoice_repo = TenantInvoiceRepository(db)

    def get_overview(self) -> dict[str, Any]:
        """获取租户概览（统计 + 最近租户）"""
        stats = self.tenant_repo.get_stats()
        recent, _ = self.tenant_repo.get_paginated_with_filters(page=1, page_size=10)
        return {
            "stats": stats,
            "recent_tenants": [TenantResponse.model_validate(t) for t in recent],
        }

    def list_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = None,
        status: str = None,
        plan_id: str = None,
    ) -> Tuple[list[Tenant], int]:
        """分页获取租户列表"""
        return self.tenant_repo.get_paginated_with_filters(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            plan_id=plan_id,
        )

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """获取单个租户"""
        return self.tenant_repo.get_by_id(tenant_id)

    def create_tenant(self, data: TenantCreate) -> Tenant:
        """创建租户"""
        # 校验套餐存在
        plan = self.plan_repo.get_by_id(data.plan_id)
        if not plan:
            raise ValueError("套餐不存在")

        # 校验domain唯一
        if self.tenant_repo.exists(domain=data.domain):
            raise ValueError(f"子域名 '{data.domain}' 已被使用")

        return self.tenant_repo.create(**data.model_dump())

    def update_tenant(self, tenant_id: str, data: TenantUpdate) -> Optional[Tenant]:
        """更新租户"""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            return None

        update_data = data.model_dump(exclude_unset=True)
        # 校验domain唯一
        if "domain" in update_data:
            existing = self.tenant_repo.get_by_domain(update_data["domain"])
            if existing and existing.id != tenant_id:
                raise ValueError(f"子域名 '{update_data['domain']}' 已被使用")

        return self.tenant_repo.update(tenant_id, **update_data)

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        return self.tenant_repo.delete(tenant_id)

    def get_tenant_stats(self) -> dict[str, Any]:
        """获取租户统计"""
        return self.tenant_repo.get_stats()

    def list_invoices(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[list[TenantInvoice], int]:
        """分页获取租户账单"""
        return self.invoice_repo.get_paginated_by_tenant(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
        )

    def create_monthly_invoice(self, tenant_id: str, period: str) -> TenantInvoice:
        """生成指定月份 SaaS 账单草案（非增值税发票）。"""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("租户不存在")
        try:
            year_s, month_s = period.split("-", 1)
            year, month = int(year_s), int(month_s)
        except (ValueError, AttributeError):
            raise ValueError("period 格式须为 YYYY-MM")

        from sqlalchemy import extract
        existing = (
            self.db.query(TenantInvoice)
            .filter(
                TenantInvoice.tenant_id == tenant_id,
                extract("year", TenantInvoice.created_at) == year,
                extract("month", TenantInvoice.created_at) == month,
            )
            .first()
        )
        if existing:
            return existing

        sub = (
            self.db.query(TenantSubscription)
            .filter(
                TenantSubscription.tenant_id == tenant_id,
                TenantSubscription.status == "active",
            )
            .order_by(TenantSubscription.created_at.desc())
            .first()
        )
        amount = int(sub.amount) if sub and sub.amount else 0
        if amount <= 0 and tenant.plan:
            amount = int(tenant.plan.price_monthly or 0)

        due = datetime(year, month, 28, tzinfo=timezone.utc) + timedelta(days=4)
        inv = TenantInvoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subscription_id=sub.id if sub else None,
            amount=amount,
            status="pending",
            due_at=due,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def update_invoice_status(
        self,
        tenant_id: str,
        invoice_id: str,
        status: str,
    ) -> TenantInvoice:
        """update_invoice_status。

        参数说明：
        :param self: 参数 self
        :param tenant_id: 参数 tenant_id
        :param invoice_id: 参数 invoice_id
        :param status: 参数 status
        :return: 返回处理结果。
        """
        inv = (
            self.db.query(TenantInvoice)
            .filter(TenantInvoice.id == invoice_id, TenantInvoice.tenant_id == tenant_id)
            .first()
        )
        if not inv:
            raise ValueError("账单不存在")
        if status not in ("pending", "paid", "overdue", "cancelled"):
            raise ValueError("无效状态")
        inv.status = status
        if status == "paid":
            inv.paid_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    def get_white_label_config(self, tenant_id: str) -> WhiteLabelConfig:
        """获取白标配置"""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("租户不存在")

        settings = {}
        if tenant.settings:
            try:
                settings = json.loads(tenant.settings)
            except (json.JSONDecodeError, TypeError):
                settings = {}

        wl = settings.get("white_label", {})
        return WhiteLabelConfig(
            brand_name=wl.get("brand_name", tenant.name),
            logo_url=wl.get("logo_url", ""),
            domain=wl.get("domain", tenant.domain),
            custom_css=wl.get("custom_css", ""),
            primary_color=wl.get("primary_color", "#1890ff"),
            footer_text=wl.get("footer_text", ""),
        )

    def get_tenant_public_info(self, domain: str) -> Optional[dict]:
        """
        获取租户公开品牌信息（供租户独立站点使用）。

        根据子域名前缀查询激活租户，聚合 brand + white_label 配置，
        返回脱敏的公开信息（不含任何敏感业务数据）。

        Args:
            domain: 子域名前缀 (如 "customer1") 或完整自定义域名

        Returns:
            包含品牌信息的字典，或 None（未找到租户）
        """
        tenant = self.tenant_repo.get_by_domain(domain)
        if not tenant or not tenant.is_active:
            return None

        settings_dict = {}
        if tenant.settings:
            try:
                settings_dict = json.loads(tenant.settings)
            except (json.JSONDecodeError, TypeError):
                settings_dict = {}

        brand_data = settings_dict.get("brand", {})
        white_label = settings_dict.get("white_label", {})
        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "domain": tenant.domain,
            "status": tenant.status,
            "plan_code": tenant.plan.code if tenant.plan else None,
            "brand": {
                "site_title": brand_data.get(
                    "site_title", white_label.get("brand_name", tenant.name)
                ),
                "logo_url": brand_data.get(
                    "logo_url", white_label.get("logo_url", "")
                ),
                "brand_colors": {
                    "primary": brand_data.get("brand_colors", {}).get(
                        "primary", white_label.get("primary_color", "#1890ff")
                    ),
                    "secondary": brand_data.get("brand_colors", {}).get(
                        "secondary", "#6b7280"
                    ),
                    "accent": brand_data.get("brand_colors", {}).get(
                        "accent", "#f59e0b"
                    ),
                },
                "product_categories": brand_data.get("product_categories", []),
                "company_name": brand_data.get("company_name", tenant.name),
                "slogan": brand_data.get("slogan", ""),
                "about_summary": brand_data.get("about_summary", ""),
                "contact_phone": brand_data.get(
                    "contact_phone",
                    white_label.get("contact_phone", tenant.contact_phone or ""),
                ),
                "contact_email": brand_data.get(
                    "contact_email",
                    white_label.get("contact_email", tenant.contact_email or ""),
                ),
                "footer_text": brand_data.get(
                    "footer_text", white_label.get("footer_text", "")
                ),
                "custom_css": brand_data.get(
                    "custom_css", white_label.get("custom_css", "")
                ),
            },
            "is_online": tenant.is_active
            and tenant.status in ("active", "trial"),
        }

    def update_white_label(self, tenant_id: str, data: WhiteLabelUpdate) -> WhiteLabelConfig:
        """更新白标配置"""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("租户不存在")

        settings = {}
        if tenant.settings:
            try:
                settings = json.loads(tenant.settings)
            except (json.JSONDecodeError, TypeError):
                settings = {}

        wl = settings.get("white_label", {})
        update_data = data.model_dump(exclude_unset=True)
        wl.update(update_data)
        settings["white_label"] = wl
        self.tenant_repo.update(tenant_id, settings=json.dumps(settings, ensure_ascii=False))
        return WhiteLabelConfig(
            brand_name=wl.get("brand_name", tenant.name),
            logo_url=wl.get("logo_url", ""),
            domain=wl.get("domain", tenant.domain),
            custom_css=wl.get("custom_css", ""),
            primary_color=wl.get("primary_color", "#1890ff"),
            footer_text=wl.get("footer_text", ""),
        )
