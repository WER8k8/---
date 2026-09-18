# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""跟单卡 PG 持久化（本地/生产真源）。

原则：
    · 内存仍作运行缓存；关键变更写 PG
    · 读时：内存 miss → 从 PG 恢复
    · 无库/失败诚实返回，不假装已持久化
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS acquisition_ops_cards (
    inquiry_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);
"""


def _db():
    try:
        from app.core.database import SessionLocal
        return SessionLocal()
    except Exception:
        return None


def ensure_table(db: Any = None) -> bool:
    session = db or _db()
    if session is None:
        return False
    try:
        from sqlalchemy import text
        session.execute(text(DDL))
        session.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure ops_cards table: %s", exc)
        try:
            session.rollback()
        except Exception:
            pass
        return False
    finally:
        if db is None:
            try:
                session.close()
            except Exception:
                pass


def save_ops_card(card: Any) -> dict[str, Any]:
    """把 OpsCard 序列化写入 PG。"""
    inquiry_id = getattr(card, "inquiry_id", "") or ""
    if not inquiry_id:
        return {"persisted": False, "reason": "missing_inquiry_id"}
    session = _db()
    if session is None:
        return {"persisted": False, "reason": "db_unavailable"}
    try:
        from sqlalchemy import text
        session.execute(text(DDL))
        payload = card.to_dict() if hasattr(card, "to_dict") else {}
        session.execute(
            text(
                """
                INSERT INTO acquisition_ops_cards (inquiry_id, tenant_id, payload, updated_at)
                VALUES (:iid, :tid, CAST(:payload AS JSONB), now())
                ON CONFLICT (inquiry_id) DO UPDATE
                SET payload = EXCLUDED.payload,
                    tenant_id = EXCLUDED.tenant_id,
                    updated_at = now()
                """
            ),
            {
                "iid": inquiry_id,
                "tid": str(getattr(card, "tenant_id", "") or ""),
                "payload": json.dumps(payload, ensure_ascii=False, default=str),
            },
        )
        session.commit()
        return {"persisted": True, "table": "acquisition_ops_cards", "inquiry_id": inquiry_id}
    except Exception as exc:  # noqa: BLE001
        try:
            session.rollback()
        except Exception:
            pass
        logger.warning("save_ops_card failed: %s", exc)
        return {"persisted": False, "reason": str(exc)[:200]}
    finally:
        try:
            session.close()
        except Exception:
            pass


def load_ops_card(inquiry_id: str, tenant_id: str = "") -> Optional[dict[str, Any]]:
    """按 inquiry_id 读跟单卡；若提供 tenant_id 则强制租户过滤（防越权）。"""
    session = _db()
    if session is None or not inquiry_id:
        return None
    try:
        from sqlalchemy import text
        if tenant_id:
            row = session.execute(
                text(
                    "SELECT payload FROM acquisition_ops_cards "
                    "WHERE inquiry_id = :iid AND tenant_id = :tid"
                ),
                {"iid": inquiry_id, "tid": tenant_id},
            ).scalar()
        else:
            # inquiry_id 为 UUID 时全局唯一；调用方应尽量传 tenant_id
            row = session.execute(
                text("SELECT payload FROM acquisition_ops_cards WHERE inquiry_id = :iid"),
                {"iid": inquiry_id},
            ).scalar()
        if not row:
            return None
        if isinstance(row, str):
            return json.loads(row)
        data = dict(row)
        if tenant_id and str(data.get("tenant_id") or "") not in ("", str(tenant_id)):
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        logger.debug("load_ops_card miss: %s", exc)
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


def restore_ops_card(store: Any, inquiry_id: str) -> Optional[Any]:
    """从 PG 恢复到内存 store。"""
    data = load_ops_card(inquiry_id)
    if not data:
        return None
    try:
        from app.services.acquisition import (
            OpsCard,
            OpsCardLogistics,
            OpsCardNote,
            OpsCardPayment,
            OpsCardSample,
            OpsCardSkuLine,
            default_fulfillment_nodes,
        )

        def _dict(x):
            return x if isinstance(x, dict) else {}

        payment = _dict(data.get("payment"))
        logistics = _dict(data.get("logistics"))
        sample = _dict(data.get("sample"))
        card = OpsCard(
            card_id=str(data.get("card_id") or ""),
            inquiry_id=str(data.get("inquiry_id") or inquiry_id),
            buyer_id=str(data.get("buyer_id") or ""),
            tenant_id=str(data.get("tenant_id") or ""),
            stage=str(data.get("stage") or "new"),
            owner_user_id=str(data.get("owner_user_id") or ""),
            buyer_display=str(data.get("buyer_display") or ""),
            buyer_grade=str(data.get("buyer_grade") or ""),
            buyer_grade_reason=str(data.get("buyer_grade_reason") or ""),
            buyer_score=int(data.get("buyer_score") or 0),
            research_level=str(data.get("research_level") or "none"),
            loss_reasons=list(data.get("loss_reasons") or []),
            loss_note=str(data.get("loss_note") or ""),
            won_at=str(data.get("won_at") or ""),
            won_amount=float(data.get("won_amount") or 0),
            quote_at=str(data.get("quote_at") or ""),
            last_touch_at=str(data.get("last_touch_at") or ""),
            last_summary=str(data.get("last_summary") or ""),
            next_action=str(data.get("next_action") or ""),
            next_action_at=str(data.get("next_action_at") or ""),
        )
        card.payment = OpsCardPayment(**{k: payment.get(k, getattr(OpsCardPayment(), k)) for k in payment} if payment else OpsCardPayment())
        try:
            card.logistics = OpsCardLogistics(**logistics) if logistics else OpsCardLogistics()
        except Exception:
            pass
        try:
            card.sample = OpsCardSample(**sample) if sample else OpsCardSample()
        except Exception:
            pass
        notes = []
        for n in data.get("notes") or []:
            try:
                notes.append(OpsCardNote(**{k: n.get(k, "") for k in ("author", "body", "at", "pinned")}))
            except Exception:
                continue
        card.notes = notes
        skus = []
        for s in data.get("sku_lines") or []:
            try:
                skus.append(OpsCardSkuLine(**{k: s.get(k) for k in s}))
            except Exception:
                continue
        card.sku_lines = skus
        card.playbook_tips = list(data.get("playbook_tips") or [])
        try:
            from app.services.acquisition import OpsCardFulfillmentNode
            fns = []
            for n in data.get("fulfillment_nodes") or []:
                try:
                    fns.append(OpsCardFulfillmentNode(**{k: n.get(k) for k in n}))
                except Exception:
                    continue
            card.fulfillment_nodes = fns or default_fulfillment_nodes()
        except Exception:
            pass
        store._by_inquiry[inquiry_id] = card
        store._by_id[card.card_id] = card
        return card
    except Exception as exc:  # noqa: BLE001
        logger.warning("restore_ops_card failed: %s", exc)
        return None


def patch_store_persistence(store: Any) -> Any:
    """给 OpsCardStore 打补丁：update 时写 PG；get 时 miss 则恢复。"""
    if getattr(store, "_pg_patched", False):
        return store
    orig_update = store.update
    orig_get = store.get_by_inquiry

    def update(card):
        out = orig_update(card)
        try:
            save_ops_card(out)
        except Exception:
            pass
        return out

    def get_by_inquiry(inquiry_id):
        card = orig_get(inquiry_id)
        if card is None:
            try:
                card = restore_ops_card(store, inquiry_id)
            except Exception:
                card = None
        return card

    store.update = update  # type: ignore[method-assign]
    store.get_by_inquiry = get_by_inquiry  # type: ignore[method-assign]
    store._pg_patched = True
    store.ensure_pg_table = ensure_table  # type: ignore[attr-defined]
    try:
        ensure_table()
    except Exception:
        pass
    return store
