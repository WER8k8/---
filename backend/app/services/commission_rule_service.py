"""多级分润规则：加载、种子、校验。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.agent_commission_rule import AgentCommissionRule

# 首单合计 3000bp=30%，续费合计 1000bp=10%（L1 平台留存，不参与代理分润）
DEFAULT_RULES: list[dict] = [
    {"payment_kind": "first", "agent_level": "l5", "rate_bp": 1500, "label": "街道/业务员首单15%"},
    {"payment_kind": "first", "agent_level": "l4", "rate_bp": 600, "label": "区代首单6%"},
    {"payment_kind": "first", "agent_level": "l3", "rate_bp": 500, "label": "市代首单5%"},
    {"payment_kind": "first", "agent_level": "l2", "rate_bp": 400, "label": "省代首单4%"},
    {"payment_kind": "renewal", "agent_level": "l5", "rate_bp": 500, "label": "街道续费5%"},
    {"payment_kind": "renewal", "agent_level": "l4", "rate_bp": 200, "label": "区代续费2%"},
    {"payment_kind": "renewal", "agent_level": "l3", "rate_bp": 200, "label": "市代续费2%"},
    {"payment_kind": "renewal", "agent_level": "l2", "rate_bp": 100, "label": "省代续费1%"},
]


class CommissionRuleService:
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    def ensure_seeded(self) -> int:
        """ensure_seeded。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        existing = self.db.query(AgentCommissionRule.id).limit(1).first()
        if existing:
            return 0
        for row in DEFAULT_RULES:
            self.db.add(AgentCommissionRule(**row))
        self.db.commit()
        return len(DEFAULT_RULES)

    def rules_map(self) -> dict[tuple[str, str], int]:
        """rules_map。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.ensure_seeded()
        rows = (
            self.db.query(AgentCommissionRule)
            .filter(AgentCommissionRule.is_active.is_(True))
            .all()
        )
        return {(r.payment_kind, r.agent_level): int(r.rate_bp) for r in rows}

    def list_rules(self) -> list[dict]:
        """list_rules。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.ensure_seeded()
        rows = (
            self.db.query(AgentCommissionRule)
            .order_by(AgentCommissionRule.payment_kind, AgentCommissionRule.agent_level)
            .all()
        )
        return [
            {
                "id": r.id,
                "payment_kind": r.payment_kind,
                "agent_level": r.agent_level,
                "rate_bp": r.rate_bp,
                "rate_pct": round(r.rate_bp / 100, 2),
                "label": r.label,
                "is_active": r.is_active,
            }
            for r in rows
        ]

    def update_rule(
        self,
        rule_id: str,
        *,
        rate_bp: int | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """update_rule。

        参数说明：
        :param self: 参数 self
        :param rule_id: 参数 rule_id
        :param rate_bp: 参数 rate_bp
        :param label: 参数 label
        :param is_active: 参数 is_active
        :return: 返回处理结果。
        """
        row = self.db.query(AgentCommissionRule).filter(AgentCommissionRule.id == rule_id).first()
        if not row:
            raise ValueError("规则不存在")
        if rate_bp is not None:
            if rate_bp < 0 or rate_bp > 10000:
                raise ValueError("rate_bp 须在 0～10000 之间")
            row.rate_bp = rate_bp
        if label is not None:
            row.label = label.strip()[:100] if label.strip() else row.label
        if is_active is not None:
            row.is_active = is_active
        self.db.flush()
        self._validate_kind_totals(row.payment_kind)
        self.db.commit()
        self.db.refresh(row)
        return {
            "id": row.id,
            "payment_kind": row.payment_kind,
            "agent_level": row.agent_level,
            "rate_bp": row.rate_bp,
            "rate_pct": round(row.rate_bp / 100, 2),
            "label": row.label,
            "is_active": row.is_active,
        }

    def _validate_kind_totals(self, kind: str) -> None:
        """同 payment_kind 代理层级合计不超过平台设定上限。"""
        limits = {"first": 3000, "renewal": 1000}
        total = sum(
            int(r.rate_bp)
            for r in self.db.query(AgentCommissionRule)
            .filter(
                AgentCommissionRule.payment_kind == kind,
                AgentCommissionRule.is_active.is_(True),
            )
            .all()
        )
        cap = limits.get(kind, 10000)
        if total > cap:
            raise ValueError(f"{kind} 类型分润合计 {total}bp 超过上限 {cap}bp")
