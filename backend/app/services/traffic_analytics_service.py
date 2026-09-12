"""流量看板：埋点落库、日 UV/PV、点击排行、询盘/电话归因。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry
from app.models.agent_tree import AgentNode
from app.models.site_analytics import SiteAnalyticsEvent
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.services.agent_aggregation_service import AgentAggregationService
from app.services.finance_honesty import (
    is_excluded_inquiry,
    is_probe_analytics_row,
)

CLICK_TYPES = frozenset(
    {"link_click", "im_click", "phone_click", "cta_click", "form_open"}
)
VIEW_TYPES = frozenset({"page_view"})
CONVERSION_TYPES = frozenset({"inquiry_submit", "phone_submit"})


def _period_start(period: str) -> datetime:
    """_period_start。

    参数说明：
    :param period: 参数 period
    :return: 返回处理结果。
    """
    now = datetime.now(timezone.utc)
    days = 7
    if period == "1d":
        days = 1
    elif period == "30d":
        days = 30
    elif period == "90d":
        days = 90
    return now - timedelta(days=days)


def _dt_gte(value: datetime, since: datetime) -> bool:
    """_dt_gte。

    参数说明：
    :param value: 参数 value
    :param since: 参数 since
    :return: 返回处理结果。
    """
    if value is None:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value >= since


def resolve_tenant_from_host(db: Session, host: str) -> Optional[str]:
    """从访问 Host 解析租户 ID（子域名或完整域名）。"""
    raw = (host or "").strip().lower().split(":")[0]
    if not raw:
        return None
    subdomain = raw
    for suffix in (".youding-saas.com", ".localhost"):
        if raw.endswith(suffix):
            subdomain = raw[: -len(suffix)]
            break
    if subdomain in ("www", "api", "admin", "localhost", ""):
        return None
    tenant = (
        db.query(Tenant)
        .filter(Tenant.domain == subdomain, Tenant.is_active.is_(True))
        .first()
    )
    if tenant:
        return str(tenant.id)
    tenant = (
        db.query(Tenant)
        .filter(Tenant.domain == raw, Tenant.is_active.is_(True))
        .first()
    )
    if tenant:
        return str(tenant.id)
    return None


def resolve_tenant_id(
    db: Session,
    *,
    merchant_id: Optional[str] = None,
    host: Optional[str] = None,
    user: Optional[User] = None,
) -> Optional[str]:
    """resolve_tenant_id。

    参数说明：
    :param db: 参数 db
    :param merchant_id: 参数 merchant_id
    :param host: 参数 host
    :param user: 参数 user
    :return: 返回处理结果。
    """
    if host:
        tid = resolve_tenant_from_host(db, host)
        if tid:
            return tid
    if merchant_id:
        mid = str(merchant_id).strip()
        if mid and mid not in ("default",):
            tenant = db.query(Tenant).filter(Tenant.id == mid).first()
            if tenant:
                return str(tenant.id)
            by_slug = (
                db.query(Tenant)
                .filter(Tenant.domain == mid, Tenant.is_active.is_(True))
                .first()
            )
            if by_slug:
                return str(by_slug.id)
            link = (
                db.query(UserTenant)
                .filter(UserTenant.user_id == mid, UserTenant.is_active.is_(True))
                .first()
            )
            if link:
                return str(link.tenant_id)
    if user and user.role in ("tenant_admin", "sales"):
        link = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
            .first()
        )
        if link:
            return str(link.tenant_id)
    return None


class TrafficAnalyticsService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def _is_real_event(self, row: SiteAnalyticsEvent, *, scope: str) -> bool:
        """_is_real_event。

        参数说明：
        :param self: 参数 self
        :param row: 参数 row
        :param scope: 参数 scope
        :return: 返回处理结果。
        """
        if is_probe_analytics_row(
            session_id=row.session_id,
            meta_json=row.meta_json,
        ):
            return False
        # 平台/代理汇总仅统计已归属租户的访问，排除匿名探针埋点
        if scope in ("platform", "agent") and not row.tenant_id:
            return False
        return True

    def _filter_inquiries(self, inquiries: list[Inquiry]) -> list[Inquiry]:
        """_filter_inquiries。

        参数说明：
        :param self: 参数 self
        :param inquiries: 参数 inquiries
        :return: 返回处理结果。
        """
        return [i for i in inquiries if not is_excluded_inquiry(i)]

    def record_event(
        self,
        *,
        event_type: str,
        session_id: str,
        tenant_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        agent_node_id: Optional[str] = None,
        page_path: Optional[str] = None,
        page_title: Optional[str] = None,
        element_id: Optional[str] = None,
        element_label: Optional[str] = None,
        content_ref: Optional[str] = None,
        product_id: Optional[str] = None,
        visitor_country: Optional[str] = None,
        visitor_language: Optional[str] = None,
        inquiry_id: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> SiteAnalyticsEvent:
        """record_event。

        参数说明：
        :param self: 参数 self
        :param event_type: 参数 event_type
        :param session_id: 参数 session_id
        :param tenant_id: 参数 tenant_id
        :param merchant_id: 参数 merchant_id
        :param agent_node_id: 参数 agent_node_id
        :param page_path: 参数 page_path
        :param page_title: 参数 page_title
        :param element_id: 参数 element_id
        :param element_label: 参数 element_label
        :param content_ref: 参数 content_ref
        :param product_id: 参数 product_id
        :param visitor_country: 参数 visitor_country
        :param visitor_language: 参数 visitor_language
        :param inquiry_id: 参数 inquiry_id
        :param meta: 参数 meta
        :return: 返回处理结果。
        """
        tid = tenant_id or resolve_tenant_id(
            self.db, merchant_id=merchant_id
        )
        row = SiteAnalyticsEvent(
            tenant_id=tid,
            agent_node_id=agent_node_id,
            session_id=session_id[:64] or "anonymous",
            event_type=event_type[:64],
            page_path=(page_path or "")[:500] or None,
            page_title=(page_title or "")[:300] or None,
            element_id=(element_id or "")[:200] or None,
            element_label=(element_label or "")[:300] or None,
            content_ref=(content_ref or "")[:200] or None,
            product_id=(product_id or "")[:64] or None,
            merchant_id=(merchant_id or "")[:64] or None,
            visitor_country=visitor_country,
            visitor_language=visitor_language,
            inquiry_id=inquiry_id,
            meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _base_query(
        self,
        since: datetime,
        *,
        tenant_id: Optional[str] = None,
        agent_node_ids: Optional[list[str]] = None,
    ):
        """_base_query。

        参数说明：
        :param self: 参数 self
        :param since: 参数 since
        :param tenant_id: 参数 tenant_id
        :param agent_node_ids: 参数 agent_node_ids
        :return: 返回处理结果。
        """
        q = self.db.query(SiteAnalyticsEvent).filter(
            SiteAnalyticsEvent.created_at >= since
        )
        if tenant_id:
            q = q.filter(SiteAnalyticsEvent.tenant_id == tenant_id)
        if agent_node_ids:
            q = q.filter(SiteAnalyticsEvent.agent_node_id.in_(agent_node_ids))
        return q

    def _load_board_events(
        self,
        *,
        since: datetime,
        tenant_id: Optional[str],
        agent_node_ids: Optional[list[str]],
        scope: str,
    ) -> list[SiteAnalyticsEvent]:
        """加载事件行并过滤探针与未归属租户的数据。"""
        q = self._base_query(
            since, tenant_id=tenant_id, agent_node_ids=agent_node_ids
        )
        return [r for r in q.all() if self._is_real_event(r, scope=scope)]

    def _load_board_inquiries(
        self,
        *,
        since: datetime,
        tenant_id: Optional[str],
        agent_node_ids: Optional[list[str]],
        rows: list[SiteAnalyticsEvent],
    ) -> list[Inquiry]:
        """按租户/代理范围加载询盘列表。"""
        inquiry_q = self.db.query(Inquiry).filter(Inquiry.is_active.is_(True))
        if tenant_id and hasattr(Inquiry, "tenant_id"):
            inquiry_q = inquiry_q.filter(Inquiry.tenant_id == tenant_id)
        elif agent_node_ids:
            scoped_tenant_ids = {
                r.tenant_id for r in rows if getattr(r, "tenant_id", None)
            }
            if not scoped_tenant_ids:
                return []
            inquiry_q = inquiry_q.filter(
                Inquiry.tenant_id.in_(list(scoped_tenant_ids))
            )
        return self._filter_inquiries(
            [i for i in inquiry_q.all() if _dt_gte(i.created_at, since)]
        )

    @staticmethod
    def _compute_summary(
        rows: list[SiteAnalyticsEvent],
        inquiries: list[Inquiry],
    ) -> dict[str, Any]:
        """计算核心汇总指标（访客/浏览/点击/转化率）。"""
        inquiry_count = len(inquiries)
        sessions_all = {r.session_id for r in rows if r.session_id}
        page_views = sum(1 for r in rows if r.event_type in VIEW_TYPES)
        clicks = sum(1 for r in rows if r.event_type in CLICK_TYPES)
        form_opens = sum(1 for r in rows if r.event_type == "form_open")
        conversions = sum(1 for r in rows if r.event_type in CONVERSION_TYPES)
        if inquiry_count > conversions:
            conversions = inquiry_count
        visitors = len(
            {
                r.session_id
                for r in rows
                if r.event_type in VIEW_TYPES and r.session_id
            }
        ) or len(sessions_all)
        conv_rate = round(
            (inquiry_count / visitors * 100) if visitors else 0.0, 2
        )
        return {
            "unique_visitors": visitors,
            "page_views": page_views,
            "total_clicks": clicks,
            "form_opens": form_opens,
            "inquiries": inquiry_count,
            "conversion_rate": conv_rate,
        }

    @staticmethod
    def _build_daily_series(
        rows: list[SiteAnalyticsEvent],
        inquiries: list[Inquiry],
        since: datetime,
    ) -> list[dict[str, Any]]:
        """按日期聚合访客/浏览/点击/询盘趋势。"""
        daily_map: dict[str, dict[str, Any]] = {}
        for r in rows:
            day = (
                r.created_at.date().isoformat()
                if r.created_at
                else since.date().isoformat()
            )
            bucket = daily_map.setdefault(
                day,
                {"visitors": set(), "page_views": 0, "clicks": 0, "inquiries": 0},
            )
            if r.event_type in VIEW_TYPES and r.session_id:
                bucket["visitors"].add(r.session_id)
            if r.event_type in VIEW_TYPES:
                bucket["page_views"] += 1
            if r.event_type in CLICK_TYPES:
                bucket["clicks"] += 1
        for inv in inquiries:
            day = (
                inv.created_at.date().isoformat()
                if inv.created_at
                else since.date().isoformat()
            )
            bucket = daily_map.setdefault(
                day,
                {"visitors": set(), "page_views": 0, "clicks": 0, "inquiries": 0},
            )
            bucket["inquiries"] += 1
        daily = []
        for day in sorted(daily_map.keys()):
            b = daily_map[day]
            daily.append(
                {
                    "date": day,
                    "visitors": len(b["visitors"]),
                    "page_views": b["page_views"],
                    "clicks": b["clicks"],
                    "inquiries": b["inquiries"],
                }
            )
        return daily

    @staticmethod
    def _build_click_ranking(
        rows: list[SiteAnalyticsEvent],
    ) -> list[dict[str, Any]]:
        """聚合点击元素排行（TOP 15）。"""
        click_counts: dict[str, dict[str, Any]] = {}
        for r in rows:
            if r.event_type not in CLICK_TYPES:
                continue
            key = r.element_label or r.element_id or r.page_path or "unknown"
            entry = click_counts.setdefault(
                key,
                {
                    "label": key,
                    "path": r.page_path,
                    "clicks": 0,
                    "inquiries": 0,
                },
            )
            entry["clicks"] += 1
            if not entry.get("path") and r.page_path:
                entry["path"] = r.page_path
        return sorted(
            click_counts.values(), key=lambda x: x["clicks"], reverse=True
        )[:15]

    @staticmethod
    def _build_content_ranking(
        rows: list[SiteAnalyticsEvent],
        inquiries: list[Inquiry],
    ) -> list[dict[str, Any]]:
        """聚合内容浏览量/点击/询盘排行（TOP 15）。"""
        content_stats: dict[str, dict[str, Any]] = {}
        for r in rows:
            ref = r.content_ref or r.product_id or r.page_path
            if not ref:
                continue
            entry = content_stats.setdefault(
                ref,
                {
                    "content_ref": ref,
                    "page_path": r.page_path,
                    "views": 0,
                    "clicks": 0,
                    "inquiries": 0,
                },
            )
            if r.event_type in VIEW_TYPES:
                entry["views"] += 1
            if r.event_type in CLICK_TYPES:
                entry["clicks"] += 1
        for inv in inquiries:
            ref = getattr(inv, "product", None) or getattr(
                inv, "landing_path", None
            )
            if not ref:
                continue
            entry = content_stats.setdefault(
                str(ref),
                {
                    "content_ref": str(ref),
                    "page_path": getattr(inv, "landing_path", None),
                    "views": 0,
                    "clicks": 0,
                    "inquiries": 0,
                },
            )
            entry["inquiries"] += 1
        return sorted(
            content_stats.values(),
            key=lambda x: (x["inquiries"], x["views"]),
            reverse=True,
        )[:15]

    @staticmethod
    def _build_recent_conversions(
        inquiries: list[Inquiry],
        since: datetime,
    ) -> list[dict[str, Any]]:
        """最近 20 条询盘转化记录。"""
        recent = []
        for inv in sorted(
            inquiries,
            key=lambda x: x.created_at or since,
            reverse=True,
        )[:20]:
            recent.append(
                {
                    "inquiry_id": str(inv.id),
                    "name": getattr(inv, "name", None),
                    "phone": getattr(inv, "phone", None),
                    "product": getattr(inv, "product", None),
                    "source_channel": getattr(inv, "source_channel", None),
                    "landing_path": getattr(inv, "landing_path", None),
                    "last_click_label": getattr(inv, "last_click_label", None),
                    "session_id": getattr(inv, "session_id", None),
                    "created_at": inv.created_at.isoformat()
                    if inv.created_at
                    else None,
                }
            )
        return recent

    def build_board(
        self,
        *,
        period: str = "7d",
        tenant_id: Optional[str] = None,
        agent_node_ids: Optional[list[str]] = None,
        scope: str = "tenant",
    ) -> dict[str, Any]:
        """构建流量看板：汇总指标、日趋势、点击/内容排行、转化漏斗。"""
        since = _period_start(period)
        rows = self._load_board_events(
            since=since,
            tenant_id=tenant_id,
            agent_node_ids=agent_node_ids,
            scope=scope,
        )
        inquiries = self._load_board_inquiries(
            since=since,
            tenant_id=tenant_id,
            agent_node_ids=agent_node_ids,
            rows=rows,
        )
        inquiry_count = len(inquiries)
        summary = self._compute_summary(rows, inquiries)
        visitors = summary["unique_visitors"]
        clicks = summary["total_clicks"]
        form_opens = summary["form_opens"]
        funnel = [
            {"stage": "访问", "count": visitors},
            {"stage": "点击", "count": clicks},
            {"stage": "打开表单", "count": form_opens},
            {"stage": "提交询盘/电话", "count": inquiry_count},
        ]
        return {
            "period": period,
            "scope": scope,
            "tenant_id": tenant_id,
            "summary": summary,
            "daily": self._build_daily_series(rows, inquiries, since),
            "top_clicks": self._build_click_ranking(rows),
            "top_content": self._build_content_ranking(rows, inquiries),
            "conversion_funnel": funnel,
            "recent_conversions": self._build_recent_conversions(inquiries, since),
        }

    def build_data_honesty(self, board: dict[str, Any]) -> dict[str, Any]:
        """build_data_honesty。

        参数说明：
        :param self: 参数 self
        :param board: 参数 board
        :return: 返回处理结果。
        """
        from app.models.inquiry import Inquiry
        from app.models.site_analytics import SiteAnalyticsEvent
        inquiries_total = self.db.query(Inquiry).filter(Inquiry.is_active.is_(True)).count()
        excluded_inquiries = sum(
            1
            for i in self.db.query(Inquiry).filter(Inquiry.is_active.is_(True)).yield_per(500)
            if is_excluded_inquiry(i)
        )
        events_total = self.db.query(SiteAnalyticsEvent).count()
        excluded_events = sum(
            1
            for e in self.db.query(SiteAnalyticsEvent).yield_per(500)
            if is_probe_analytics_row(session_id=e.session_id, meta_json=e.meta_json)
            or not e.tenant_id
        )
        summary = board.get("summary") or {}
        has_production_activity = any(
            int(summary.get(key) or 0) > 0
            for key in ("unique_visitors", "page_views", "inquiries", "total_clicks")
        )
        return {
            "has_production_activity": has_production_activity,
            "excluded_inquiries": excluded_inquiries,
            "excluded_analytics_events": excluded_events,
            "raw_inquiries": inquiries_total,
            "raw_analytics_events": events_total,
        }

    def build_board_with_honesty(self, **kwargs: Any) -> dict[str, Any]:
        """build_board_with_honesty。

        参数说明：
        :param self: 参数 self
        :param **kwargs: 参数 **kwargs
        :return: 返回处理结果。
        """
        board = self.build_board(**kwargs)
        board["data_honesty"] = self.build_data_honesty(board)
        return board

    def build_platform_board(self, period: str = "7d") -> dict[str, Any]:
        """build_platform_board。

        参数说明：
        :param self: 参数 self
        :param period: 参数 period
        :return: 返回处理结果。
        """
        board = self.build_board(period=period, scope="platform")
        board["data_honesty"] = self.build_data_honesty(board)
        since = _period_start(period)
        tenants = self.db.query(Tenant).all()
        by_tenant = []
        for t in tenants:
            tid = str(t.id)
            child = self.build_board(period=period, tenant_id=tid, scope="tenant")
            if child["summary"]["unique_visitors"] or child["summary"]["inquiries"]:
                by_tenant.append(
                    {
                        "tenant_id": tid,
                        "tenant_name": t.name,
                        "domain": t.domain,
                        **child["summary"],
                    }
                )
        by_tenant.sort(
            key=lambda x: (x.get("inquiries", 0), x.get("unique_visitors", 0)),
            reverse=True,
        )
        agent_rows = []
        agent_nodes = (
            self.db.query(AgentNode)
            .filter(AgentNode.is_active.is_(True))
            .all()
        )
        for node in agent_nodes:
            subtree = list(
                AgentAggregationService.collect_subtree_node_ids(self.db, node.id)
            )
            child = self.build_board(
                period=period,
                agent_node_ids=subtree,
                scope="agent",
            )
            agent_rows.append(
                {
                    "node_id": node.id,
                    "node_name": node.name,
                    "level": node.level,
                    **child["summary"],
                }
            )
        agent_rows.sort(key=lambda x: x.get("inquiries", 0), reverse=True)
        board["by_tenant"] = by_tenant[:50]
        board["by_agent_node"] = agent_rows[:30]
        board["active_tenants"] = len(by_tenant)
        return board

    @staticmethod
    def agent_subtree_node_ids(db: Session, node_id: str) -> list[str]:
        """agent_subtree_node_ids。

        参数说明：
        :param db: 参数 db
        :param node_id: 参数 node_id
        :return: 返回处理结果。
        """
        return list(AgentAggregationService.collect_subtree_node_ids(db, node_id))

    def attach_inquiry_attribution(
        self,
        inquiry: Inquiry,
        *,
        session_id: Optional[str],
        landing_path: Optional[str],
        last_click_label: Optional[str],
        tenant_id: Optional[str],
    ) -> None:
        """attach_inquiry_attribution。

        参数说明：
        :param self: 参数 self
        :param inquiry: 参数 inquiry
        :param session_id: 参数 session_id
        :param landing_path: 参数 landing_path
        :param last_click_label: 参数 last_click_label
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        cols = {c.key for c in Inquiry.__table__.columns}
        if session_id and "session_id" in cols:
            inquiry.session_id = session_id[:64]
        if landing_path and "landing_path" in cols:
            inquiry.landing_path = landing_path[:500]
        if last_click_label and "last_click_label" in cols:
            inquiry.last_click_label = last_click_label[:300]
        if tenant_id and "tenant_id" in cols:
            inquiry.tenant_id = tenant_id
