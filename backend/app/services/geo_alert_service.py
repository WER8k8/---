"""
GEO Alert Service - 预警服务层（SQLAlchemy 版本）
使用 UJ 项目的 SQLAlchemy session 模式
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy import select, update, insert, func, desc
from sqlalchemy.orm import Session

from app.models.geo_alert_db_models import GEOAlertRule, GEOAlert, GEOAlertHistory
from app.models.geo_alert_models import (
    AlertSeverity,
    AlertType,
    AlertStatus,
    AlertRuleCreate,
    AlertCreate,
    AlertAcknowledge,
    AlertResolve,
)


class AlertRuleEngine:
    """
    预警规则引擎 - 评估规则是否触发
    支持多种检查器：threshold、time_based、rate_based、geo_rank、geo_inquiry
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._checkers: dict[str, Callable] = {}
        self._register_default_checkers()

    def _register_default_checkers(self):
        """注册默认检查器"""
        self._checkers["always_true"] = lambda _: True
        self._checkers["threshold"] = self._check_threshold
        self._checkers["time_based"] = self._check_time_based
        self._checkers["rate_based"] = self._check_rate_based
        # GEO 专用检查器
        self._checkers["geo_rank_drop"] = self._check_geo_rank_drop
        self._checkers["geo_inquiry_drop"] = self._check_geo_inquiry_drop

    def _check_threshold(self, config: dict[str, Any]) -> bool:
        """阈值检查"""
        current = config.get("current_value", 0)
        threshold = config.get("threshold", 0)
        operator = config.get("operator", ">")
        if operator == ">":
            return current > threshold
        elif operator == "<":
            return current < threshold
        elif operator == ">=":
            return current >= threshold
        elif operator == "<=":
            return current <= threshold
        elif operator == "==":
            return current == threshold
        return False

    def _check_time_based(self, config: dict[str, Any]) -> bool:
        """基于时间的检查"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        check_hour = config.get("hour")
        if check_hour is not None and hour == check_hour:
            return True

        check_minute = config.get("minute")
        if check_minute is not None and now.minute == check_minute:
            return True

        return False

    def _check_rate_based(self, config: dict[str, Any]) -> bool:
        """基于速率的检查"""
        count = config.get("count", 0)
        max_count = config.get("max_count", 100)
        return count > max_count

    def _check_geo_rank_drop(self, config: dict[str, Any]) -> bool:
        """
        GEO 排名骤降检查
        config: {keyword, current_rank, baseline_rank, drop_threshold}
        """
        current_rank = config.get("current_rank", 999)
        baseline_rank = config.get("baseline_rank", 10)
        drop_threshold = config.get("drop_threshold", 5)  # 排名下降超过5位
        return (current_rank - baseline_rank) > drop_threshold

    def _check_geo_inquiry_drop(self, config: dict[str, Any]) -> bool:
        """
        GEO 询盘转化率骤降检查
        config: {current_rate, baseline_rate, drop_threshold}
        """
        current_rate = config.get("current_rate", 0)
        baseline_rate = config.get("baseline_rate", 0.1)
        drop_threshold = config.get("drop_threshold", 0.05)  # 转化率下降超过5%
        return (baseline_rate - current_rate) > drop_threshold

    def register_checker(self, name: str, checker: Callable[[dict[str, Any]], bool]):
        """注册自定义检查器"""
        self._checkers[name] = checker

    def check_rule(self, rule_config: dict[str, Any], context: dict[str, Any]) -> bool:
        """检查规则是否触发"""
        checker_type = rule_config.get("type", "always_true")
        checker = self._checkers.get(checker_type)
        if checker is None:
            return False

        merged_config = {**rule_config, **context}
        return checker(merged_config)


class GeoAlertService:
    """
    GEO 预警服务 - 管理预警规则和预警实例
    使用 SQLAlchemy Session（与 UJ 项目一致）
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.engine = AlertRuleEngine()

    # ── 规则管理 ──
    def create_rule(self, db: Session, rule_create: AlertRuleCreate) -> GEOAlertRule:
        """创建预警规则"""
        rule_data = rule_create.model_dump()
        rule = GEOAlertRule(**rule_data)
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def list_rules(self, db: Session, enabled_only: bool = False) -> list[GEOAlertRule]:
        """列出预警规则"""
        query = select(GEOAlertRule)
        if enabled_only:
            query = query.where(GEOAlertRule.enabled == True)
        query = query.order_by(desc(GEOAlertRule.created_at))
        return db.execute(query).scalars().all()

    def get_rule(self, db: Session, rule_id: int) -> Optional[GEOAlertRule]:
        """获取单个预警规则"""
        return db.execute(
            select(GEOAlertRule).where(GEOAlertRule.id == rule_id)
        ).scalar_one_or_none()

    def update_rule(self, db: Session, rule_id: int, rule_data: dict[str, Any]) -> Optional[GEOAlertRule]:
        """更新预警规则"""
        rule = self.get_rule(db, rule_id)
        if not rule:
            return None

        allowed_fields = ["name", "description", "alert_type", "severity",
                          "enabled", "rule_config", "check_interval_seconds"]
        for field in allowed_fields:
            if field in rule_data:
                setattr(rule, field, rule_data[field])

        rule.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rule)
        return rule

    def update_rule_trigger(self, db: Session, rule_id: int) -> None:
        """更新规则触发计数和时间"""
        db.execute(
            update(GEOAlertRule)
            .where(GEOAlertRule.id == rule_id)
            .values(
                last_triggered_at=datetime.now(timezone.utc),
                trigger_count=GEOAlertRule.trigger_count + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    # ── 预警管理 ──
    def create_alert(self, db: Session, alert_create: AlertCreate) -> GEOAlert:
        """创建预警"""
        alert_data = alert_create.model_dump()
        alert = GEOAlert(**alert_data)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        # 记录历史
        history = GEOAlertHistory(
            alert_id=alert.id,
            action_type="created",
            action_by=None,
            action_notes=None,
            old_status=None,
            new_status=alert.status,
            extra_data={"source": "system"},
        )
        db.add(history)
        db.commit()
        # 更新规则触发计数
        if alert.rule_id:
            self.update_rule_trigger(db, alert.rule_id)

        return alert

    def trigger_rule(self, db: Session, rule_id: int, context: dict[str, Any]) -> Optional[GEOAlert]:
        """
        触发规则检查 - 如果规则触发则创建预警
        """
        rule = self.get_rule(db, rule_id)
        if not rule or not rule.enabled:
            return None

        rule_config = rule.rule_config or {}
        if self.engine.check_rule(rule_config, context):
            alert_create = AlertCreate(
                rule_id=rule_id,
                alert_type=AlertType(rule.alert_type),
                severity=AlertSeverity(rule.severity),
                title=rule_config.get("alert_title", f"预警: {rule.name}"),
                description=rule_config.get("alert_description", rule.description or ""),
                impact_scope=rule_config.get("impact_scope", ""),
                proposed_solution=rule_config.get("proposed_solution", ""),
                extra_data=context,
            )
            return self.create_alert(db, alert_create)

        return None

    def list_alerts(
        self,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """列出预警"""
        query = select(GEOAlert)
        if status:
            query = query.where(GEOAlert.status == status)
        if severity:
            query = query.where(GEOAlert.severity == severity)
        if alert_type:
            query = query.where(GEOAlert.alert_type == alert_type)

        # 统计总数
        count_query = select(func.count()).select_from(GEOAlert)
        if status:
            count_query = count_query.where(GEOAlert.status == status)
        if severity:
            count_query = count_query.where(GEOAlert.severity == severity)
        if alert_type:
            count_query = count_query.where(GEOAlert.alert_type == alert_type)
        total = db.execute(count_query).scalar() or 0
        # 分页
        query = query.order_by(desc(GEOAlert.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = db.execute(query).scalars().all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    def get_alert(self, db: Session, alert_id: int) -> Optional[GEOAlert]:
        """获取单个预警"""
        return db.execute(
            select(GEOAlert).where(GEOAlert.id == alert_id)
        ).scalar_one_or_none()

    def acknowledge(self, db: Session, alert_id: int, ack: AlertAcknowledge) -> Optional[GEOAlert]:
        """确认预警"""
        alert = self.get_alert(db, alert_id)
        if not alert:
            return None

        old_status = alert.status
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = ack.acknowledged_by
        alert.updated_at = datetime.now(timezone.utc)
        db.commit()
        # 记录历史
        history = GEOAlertHistory(
            alert_id=alert_id,
            action_type="acknowledged",
            action_by=ack.acknowledged_by,
            action_notes=ack.notes,
            old_status=old_status,
            new_status="acknowledged",
            extra_data={"source": "user"},
        )
        db.add(history)
        db.commit()
        return alert

    def resolve(self, db: Session, alert_id: int, resolve: AlertResolve) -> Optional[GEOAlert]:
        """解决预警"""
        alert = self.get_alert(db, alert_id)
        if not alert:
            return None

        old_status = alert.status
        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolved_by = resolve.resolved_by
        alert.resolution_notes = resolve.resolution_notes
        alert.updated_at = datetime.now(timezone.utc)
        db.commit()
        # 记录历史
        history = GEOAlertHistory(
            alert_id=alert_id,
            action_type="resolved",
            action_by=resolve.resolved_by,
            action_notes=resolve.resolution_notes,
            old_status=old_status,
            new_status="resolved",
            extra_data={"source": "user"},
        )
        db.add(history)
        db.commit()
        return alert

    def get_histories(self, db: Session, alert_id: int) -> list[GEOAlertHistory]:
        """获取预警历史"""
        query = select(GEOAlertHistory).where(
            GEOAlertHistory.alert_id == alert_id
        ).order_by(GEOAlertHistory.created_at.asc())
        return db.execute(query).scalars().all()

    def get_statistics(self, db: Session) -> dict[str, Any]:
        """获取预警统计"""
        from collections import defaultdict
        # 获取所有预警
        alerts = db.execute(select(GEOAlert)).scalars().all()
        total_alerts = len(alerts)
        active_alerts = len([a for a in alerts if a.status == "active"])
        today = datetime.now(timezone.utc).date().isoformat()
        resolved_today = 0
        for a in alerts:
            if a.status == "resolved" and a.resolved_at:
                resolved_date = a.resolved_at.date().isoformat()
                if resolved_date == today:
                    resolved_today += 1

        by_severity = defaultdict(int)
        by_type = defaultdict(int)
        for a in alerts:
            by_severity[a.severity] += 1
            by_type[a.alert_type] += 1

        # 最近7天趋势
        trend_last_7_days = []
        seven_days_ago = datetime.now(timezone.utc) - __import__('datetime').timedelta(days=7)
        for i in range(7):
            current_date = seven_days_ago + __import__('datetime').timedelta(days=i)
            date_str = current_date.date().isoformat()
            day_count = 0
            critical_count = 0
            error_count = 0
            warning_count = 0
            info_count = 0
            for a in alerts:
                alert_date = a.created_at.date().isoformat()
                if alert_date == date_str:
                    day_count += 1
                    if a.severity == "critical":
                        critical_count += 1
                    elif a.severity == "error":
                        error_count += 1
                    elif a.severity == "warning":
                        warning_count += 1
                    elif a.severity == "info":
                        info_count += 1

            trend_last_7_days.append({
                "date": date_str,
                "count": day_count,
                "critical_count": critical_count,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
            })

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_today": resolved_today,
            "by_severity": dict(by_severity),
            "by_type": dict(by_type),
            "trend_last_7_days": trend_last_7_days,
        }

    def check_all_rules(self, db: Session, context: dict[str, Any]) -> list[GEOAlert]:
        """
        检查所有启用的规则 - 批量触发
        用于定时任务或手动触发
        """
        rules = self.list_rules(db, enabled_only=True)
        triggered_alerts = []
        for rule in rules:
            alert = self.trigger_rule(db, rule.id, context)
            if alert:
                triggered_alerts.append(alert)

        return triggered_alerts

    # ── 快捷创建 GEO 专用规则 ──
    def create_geo_rank_rule(
        self,
        db: Session,
        keyword: str,
        baseline_rank: int = 10,
        drop_threshold: int = 5
    ) -> GEOAlertRule:
        """
        创建 GEO 排名监控规则（快捷方法）
        """
        rule_create = AlertRuleCreate(
            name=f"GEO排名监控 - {keyword}",
            description=f"监控关键词 '{keyword}' 的排名变化，排名下降超过 {drop_threshold} 位时预警",
            alert_type=AlertType.GEO_RANK,
            severity=AlertSeverity.WARNING,
            enabled=True,
            rule_config={
                "type": "geo_rank_drop",
                "keyword": keyword,
                "baseline_rank": baseline_rank,
                "drop_threshold": drop_threshold,
                "alert_title": f"⚠️ GEO排名骤降: {keyword}",
                "alert_description": f"关键词 '{keyword}' 的排名从 {baseline_rank} 位下降到当前位置，下降超过 {drop_threshold} 位",
                "impact_scope": f"关键词: {keyword}",
                "proposed_solution": "1. 检查内容质量评分\n2. 检查竞品内容变化\n3. 更新或重新生成内容",
            },
        )
        return self.create_rule(db, rule_create)

    def create_geo_inquiry_rule(
        self,
        db: Session,
        baseline_rate: float = 0.1,
        drop_threshold: float = 0.05
    ) -> GEOAlertRule:
        """
        创建 GEO 询盘转化率监控规则（快捷方法）
        """
        rule_create = AlertRuleCreate(
            name="GEO询盘转化率监控",
            description=f"监控询盘转化率变化，转化率下降超过 {drop_threshold*100}% 时预警",
            alert_type=AlertType.GEO_INQUIRY,
            severity=AlertSeverity.ERROR,
            enabled=True,
            rule_config={
                "type": "geo_inquiry_drop",
                "baseline_rate": baseline_rate,
                "drop_threshold": drop_threshold,
                "alert_title": "⚠️ GEO询盘转化率骤降",
                "alert_description": f"询盘转化率从 {baseline_rate*100}% 下降超过 {drop_threshold*100}%，可能影响业务",
                "impact_scope": "全站",
                "proposed_solution": "1. 检查RankGuard指标\n2. 检查内容质量\n3. 检查竞品动态",
            },
        )
        return self.create_rule(db, rule_create)


# 全局服务实例
geo_alert_service = GeoAlertService()
