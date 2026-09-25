# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Buyer Master 身份锁 + 内容归因 的 PG 持久化（本地/生产真源）。

对齐 ``ops_card_pg.py`` 的写法，但纠正其「静默降级」缺陷：

原则：
    · 内存仍是运行缓存；关键变更**写穿** PG
    · 读时：内存 miss → 从 PG 恢复
    · 无库 / 写失败：**显式告警 + 可观测**（``store.persistence_report()``），
      绝不静默 pass、绝不假装已持久化

表（由 Alembic ``121_w4_identity_attribution_persistence`` 建立，此处
``ensure_tables`` 做幂等兜底，兼容历史 bootstrap 建库）：
    acquisition_buyer_masters          身份锁主档
    acquisition_content_touches        内容归因主档
    acquisition_content_inquiry_links  内容 ↔ 询盘 关联
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


DDL = """
CREATE TABLE IF NOT EXISTS acquisition_buyer_masters (
    buyer_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    email TEXT,
    persona_locked BOOLEAN DEFAULT TRUE,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_acq_buyer_masters_tenant
    ON acquisition_buyer_masters (tenant_id);
CREATE INDEX IF NOT EXISTS ix_acq_buyer_masters_tenant_email
    ON acquisition_buyer_masters (tenant_id, lower(email));

CREATE TABLE IF NOT EXISTS acquisition_content_touches (
    content_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    content_title TEXT,
    content_type TEXT,
    channel TEXT,
    published_at TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_acq_content_touches_tenant
    ON acquisition_content_touches (tenant_id);

CREATE TABLE IF NOT EXISTS acquisition_content_inquiry_links (
    inquiry_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    tenant_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (inquiry_id, content_id)
);
CREATE INDEX IF NOT EXISTS ix_acq_content_links_content
    ON acquisition_content_inquiry_links (content_id);
"""


def _db():
    try:
        from app.core.database import SessionLocal
        return SessionLocal()
    except Exception:  # noqa: BLE001
        return None


def _safe_rollback(session: Any) -> None:
    try:
        session.rollback()
    except Exception:  # noqa: BLE001
        pass


def _safe_close(session: Any) -> None:
    try:
        session.close()
    except Exception:  # noqa: BLE001
        pass


def ensure_tables(db: Any = None) -> bool:
    """幂等建表 + 建索引。返回是否成功（失败显式告警）。"""
    session = db or _db()
    if session is None:
        logger.warning("ensure identity tables skipped: db_unavailable")
        return False
    try:
        from sqlalchemy import text
        for stmt in [s.strip() for s in DDL.split(";") if s.strip()]:
            session.execute(text(stmt))
        session.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure identity tables failed: %s", exc)
        _safe_rollback(session)
        return False
    finally:
        if db is None:
            _safe_close(session)


# ═══════════════════════════════════════════════════════════
# 观测：把「是否真落库」记到 store 上，供 /ops/persistence 读出
# ═══════════════════════════════════════════════════════════

def _record_write(store: Any, result: dict[str, Any]) -> None:
    stats = getattr(store, "persistence_stats", None)
    if isinstance(stats, dict):
        if result.get("persisted"):
            stats["writes"] = int(stats.get("writes", 0)) + 1
            stats["last_error"] = None
        else:
            stats["write_failures"] = int(stats.get("write_failures", 0)) + 1
            stats["last_error"] = result.get("reason")
    if result.get("persisted"):
        try:
            store.persistence_backend = "postgres"
        except Exception:  # noqa: BLE001
            pass
    else:
        try:
            store.persistence_backend = "memory"
        except Exception:  # noqa: BLE001
            pass
        logger.warning(
            "%s 未落库（已降级内存，重启会丢）: %s",
            stats.get("table") if isinstance(stats, dict) else "acquisition",
            result.get("reason"),
        )


def _record_load(store: Any, hit: bool) -> None:
    stats = getattr(store, "persistence_stats", None)
    if isinstance(stats, dict):
        stats["loads"] = int(stats.get("loads", 0)) + (1 if hit else 0)
        stats["load_misses"] = int(stats.get("load_misses", 0)) + (0 if hit else 1)


# ═══════════════════════════════════════════════════════════
# Buyer Master
# ═══════════════════════════════════════════════════════════

def save_buyer_master(buyer: Any) -> dict[str, Any]:
    buyer_id = str(getattr(buyer, "buyer_id", "") or "")
    if not buyer_id:
        return {"persisted": False, "reason": "missing_buyer_id"}
    session = _db()
    if session is None:
        return {"persisted": False, "reason": "db_unavailable"}
    try:
        from sqlalchemy import text
        ensure_tables(session)
        payload = buyer.to_dict() if hasattr(buyer, "to_dict") else {}
        session.execute(
            text(
                """
                INSERT INTO acquisition_buyer_masters
                    (buyer_id, tenant_id, email, persona_locked, payload, created_at, updated_at)
                VALUES (:bid, :tid, :email, :locked, CAST(:payload AS JSONB), now(), now())
                ON CONFLICT (buyer_id) DO UPDATE
                SET tenant_id = EXCLUDED.tenant_id,
                    email = EXCLUDED.email,
                    persona_locked = EXCLUDED.persona_locked,
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """
            ),
            {
                "bid": buyer_id,
                "tid": str(getattr(buyer, "tenant_id", "") or ""),
                "email": str(getattr(buyer, "email", "") or ""),
                "locked": bool(getattr(buyer, "persona_locked", True)),
                "payload": json.dumps(payload, ensure_ascii=False, default=str),
            },
        )
        session.commit()
        return {"persisted": True, "table": "acquisition_buyer_masters", "buyer_id": buyer_id}
    except Exception as exc:  # noqa: BLE001
        _safe_rollback(session)
        logger.warning("save_buyer_master failed: %s", exc)
        return {"persisted": False, "reason": str(exc)[:200]}
    finally:
        _safe_close(session)


def load_buyer_master(buyer_id: str, tenant_id: str = "") -> Optional[dict[str, Any]]:
    if not buyer_id:
        return None
    session = _db()
    if session is None:
        return None
    try:
        from sqlalchemy import text
        if tenant_id:
            row = session.execute(
                text(
                    "SELECT payload FROM acquisition_buyer_masters "
                    "WHERE buyer_id = :bid AND tenant_id = :tid"
                ),
                {"bid": buyer_id, "tid": tenant_id},
            ).scalar()
        else:
            row = session.execute(
                text("SELECT payload FROM acquisition_buyer_masters WHERE buyer_id = :bid"),
                {"bid": buyer_id},
            ).scalar()
        return _as_dict(row)
    except Exception as exc:  # noqa: BLE001
        logger.debug("load_buyer_master miss: %s", exc)
        return None
    finally:
        _safe_close(session)


def load_buyer_master_by_email(tenant_id: str, email: str) -> Optional[dict[str, Any]]:
    if not email:
        return None
    session = _db()
    if session is None:
        return None
    try:
        from sqlalchemy import text
        row = session.execute(
            text(
                "SELECT payload FROM acquisition_buyer_masters "
                "WHERE tenant_id = :tid AND lower(email) = lower(:email)"
            ),
            {"tid": tenant_id or "", "email": email},
        ).scalar()
        return _as_dict(row)
    except Exception as exc:  # noqa: BLE001
        logger.debug("load_buyer_master_by_email miss: %s", exc)
        return None
    finally:
        _safe_close(session)


def list_buyer_masters(tenant_id: str = "") -> list[dict[str, Any]]:
    session = _db()
    if session is None:
        return []
    try:
        from sqlalchemy import text
        if tenant_id:
            rows = session.execute(
                text(
                    "SELECT payload FROM acquisition_buyer_masters WHERE tenant_id = :tid"
                ),
                {"tid": tenant_id},
            ).scalars().all()
        else:
            rows = session.execute(
                text("SELECT payload FROM acquisition_buyer_masters")
            ).scalars().all()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = _as_dict(r)
            if d:
                out.append(d)
        return out
    except Exception as exc:  # noqa: BLE001
        logger.debug("list_buyer_masters miss: %s", exc)
        return []
    finally:
        _safe_close(session)


def _as_dict(row: Any) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if isinstance(row, (str, bytes)):
        try:
            data = json.loads(row)
            return data if isinstance(data, dict) else None
        except Exception:  # noqa: BLE001
            return None
    try:
        data = dict(row)
        return data if data else None
    except Exception:  # noqa: BLE001
        return None


def restore_buyer_master(store: Any, buyer_id: str, tenant_id: str = "") -> Optional[Any]:
    data = load_buyer_master(buyer_id, tenant_id=tenant_id)
    if not data:
        _record_load(store, hit=False)
        return None
    try:
        from app.services.acquisition import BuyerMaster
        fields = {f for f in BuyerMaster.__dataclass_fields__}  # type: ignore[attr-defined]
        buyer = BuyerMaster(**{k: v for k, v in data.items() if k in fields})
        store._by_id[buyer.buyer_id] = buyer
        if buyer.email:
            store._by_email[(buyer.tenant_id, buyer.email.lower())] = buyer.buyer_id
        _record_load(store, hit=True)
        return buyer
    except Exception as exc:  # noqa: BLE001
        logger.warning("restore_buyer_master failed: %s", exc)
        _record_load(store, hit=False)
        return None


def restore_buyer_masters_for_tenant(store: Any, tenant_id: str = "") -> int:
    restored = 0
    for data in list_buyer_masters(tenant_id=tenant_id):
        try:
            from app.services.acquisition import BuyerMaster
            fields = {f for f in BuyerMaster.__dataclass_fields__}  # type: ignore[attr-defined]
            buyer = BuyerMaster(**{k: v for k, v in data.items() if k in fields})
            store._by_id[buyer.buyer_id] = buyer
            if buyer.email:
                store._by_email[(buyer.tenant_id, buyer.email.lower())] = buyer.buyer_id
            restored += 1
        except Exception:  # noqa: BLE001
            continue
    return restored


def patch_buyer_store_persistence(store: Any) -> Any:
    """给 BuyerMasterStore 打补丁：upsert 写穿 PG；get/by_email 内存 miss 则回源。"""
    if getattr(store, "_pg_patched", False):
        return store
    orig_upsert = store.upsert
    orig_get = store.get
    orig_get_by_email = store.get_by_email
    orig_list_by_tenant = store.list_by_tenant

    def upsert(buyer):
        out, is_new, alerts = orig_upsert(buyer)
        _record_write(store, save_buyer_master(out))
        return out, is_new, alerts

    def get(buyer_id):
        b = orig_get(buyer_id)
        if b is None:
            b = restore_buyer_master(store, buyer_id)
        return b

    def get_by_email(tenant_id, email):
        b = orig_get_by_email(tenant_id, email)
        if b is None:
            data = load_buyer_master_by_email(tenant_id, email)
            if data:
                try:
                    from app.services.acquisition import BuyerMaster
                    fields = {f for f in BuyerMaster.__dataclass_fields__}  # type: ignore[attr-defined]
                    b = BuyerMaster(**{k: v for k, v in data.items() if k in fields})
                    store._by_id[b.buyer_id] = b
                    if b.email:
                        store._by_email[(b.tenant_id, b.email.lower())] = b.buyer_id
                    _record_load(store, hit=True)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("restore buyer by email failed: %s", exc)
                    b = None
            else:
                _record_load(store, hit=False)
        return b

    def list_by_tenant(tenant_id):
        out = orig_list_by_tenant(tenant_id)
        if not out:
            restore_buyer_masters_for_tenant(store, tenant_id)
            out = orig_list_by_tenant(tenant_id)
        return out

    store.upsert = upsert  # type: ignore[method-assign]
    store.get = get  # type: ignore[method-assign]
    store.get_by_email = get_by_email  # type: ignore[method-assign]
    store.list_by_tenant = list_by_tenant  # type: ignore[method-assign]
    store._pg_patched = True  # type: ignore[attr-defined]
    store.ensure_pg_table = ensure_tables  # type: ignore[attr-defined]
    ok = False
    try:
        ok = ensure_tables()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure buyer tables failed: %s", exc)
    store.persistence_backend = "postgres" if ok else "memory"  # type: ignore[attr-defined]
    if not ok:
        logger.warning(
            "BuyerMasterStore PG 不可用，已降级为内存存储（重启会丢）；"
            "自述见 store.persistence_report()"
        )
    return store


# ═══════════════════════════════════════════════════════════
# 内容归因（ContentAttribution）
# ═══════════════════════════════════════════════════════════

def save_content_touch(touch: Any) -> dict[str, Any]:
    content_id = str(getattr(touch, "content_id", "") or "")
    if not content_id:
        return {"persisted": False, "reason": "missing_content_id"}
    session = _db()
    if session is None:
        return {"persisted": False, "reason": "db_unavailable"}
    try:
        from sqlalchemy import text
        ensure_tables(session)
        payload = touch.to_dict() if hasattr(touch, "to_dict") else _touch_dict(touch)
        session.execute(
            text(
                """
                INSERT INTO acquisition_content_touches
                    (content_id, tenant_id, content_title, content_type, channel,
                     published_at, payload, created_at, updated_at)
                VALUES (:cid, :tid, :title, :ctype, :channel,
                        :published, CAST(:payload AS JSONB), now(), now())
                ON CONFLICT (content_id) DO UPDATE
                SET tenant_id = EXCLUDED.tenant_id,
                    content_title = EXCLUDED.content_title,
                    content_type = EXCLUDED.content_type,
                    channel = EXCLUDED.channel,
                    published_at = EXCLUDED.published_at,
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """
            ),
            {
                "cid": content_id,
                "tid": str(getattr(touch, "tenant_id", "") or ""),
                "title": str(getattr(touch, "content_title", "") or ""),
                "ctype": str(getattr(touch, "content_type", "") or ""),
                "channel": str(getattr(touch, "channel", "") or ""),
                "published": str(getattr(touch, "published_at", "") or ""),
                "payload": json.dumps(payload, ensure_ascii=False, default=str),
            },
        )
        session.commit()
        return {"persisted": True, "table": "acquisition_content_touches", "content_id": content_id}
    except Exception as exc:  # noqa: BLE001
        _safe_rollback(session)
        logger.warning("save_content_touch failed: %s", exc)
        return {"persisted": False, "reason": str(exc)[:200]}
    finally:
        _safe_close(session)


def _touch_dict(touch: Any) -> dict[str, Any]:
    return {
        "content_id": getattr(touch, "content_id", ""),
        "content_title": getattr(touch, "content_title", ""),
        "content_type": getattr(touch, "content_type", ""),
        "channel": getattr(touch, "channel", ""),
        "tenant_id": getattr(touch, "tenant_id", ""),
        "published_at": getattr(touch, "published_at", ""),
        "inquiry_ids": list(getattr(touch, "inquiry_ids", []) or []),
        "created_at": getattr(touch, "created_at", ""),
    }


def link_content_inquiry(content_id: str, inquiry_id: str, tenant_id: str = "") -> dict[str, Any]:
    if not content_id or not inquiry_id:
        return {"persisted": False, "reason": "content_id/inquiry_id required"}
    session = _db()
    if session is None:
        return {"persisted": False, "reason": "db_unavailable"}
    try:
        from sqlalchemy import text
        ensure_tables(session)
        session.execute(
            text(
                """
                INSERT INTO acquisition_content_inquiry_links
                    (inquiry_id, content_id, tenant_id, created_at)
                VALUES (:iid, :cid, :tid, now())
                ON CONFLICT (inquiry_id, content_id) DO NOTHING
                """
            ),
            {"iid": inquiry_id, "cid": content_id, "tid": tenant_id or ""},
        )
        session.commit()
        return {"persisted": True, "table": "acquisition_content_inquiry_links"}
    except Exception as exc:  # noqa: BLE001
        _safe_rollback(session)
        logger.warning("link_content_inquiry failed: %s", exc)
        return {"persisted": False, "reason": str(exc)[:200]}
    finally:
        _safe_close(session)


def load_content_touch(content_id: str) -> Optional[dict[str, Any]]:
    if not content_id:
        return None
    session = _db()
    if session is None:
        return None
    try:
        from sqlalchemy import text
        row = session.execute(
            text(
                "SELECT payload FROM acquisition_content_touches WHERE content_id = :cid"
            ),
            {"cid": content_id},
        ).scalar()
        return _as_dict(row)
    except Exception as exc:  # noqa: BLE001
        logger.debug("load_content_touch miss: %s", exc)
        return None
    finally:
        _safe_close(session)


def list_content_touches(tenant_id: str = "") -> list[dict[str, Any]]:
    session = _db()
    if session is None:
        return []
    try:
        from sqlalchemy import text
        if tenant_id:
            rows = session.execute(
                text(
                    "SELECT payload FROM acquisition_content_touches WHERE tenant_id = :tid"
                ),
                {"tid": tenant_id},
            ).scalars().all()
        else:
            rows = session.execute(
                text("SELECT payload FROM acquisition_content_touches")
            ).scalars().all()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = _as_dict(r)
            if d:
                out.append(d)
        return out
    except Exception as exc:  # noqa: BLE001
        logger.debug("list_content_touches miss: %s", exc)
        return []
    finally:
        _safe_close(session)


def list_inquiry_content_ids(inquiry_id: str) -> list[str]:
    if not inquiry_id:
        return []
    session = _db()
    if session is None:
        return []
    try:
        from sqlalchemy import text
        rows = session.execute(
            text(
                "SELECT content_id FROM acquisition_content_inquiry_links "
                "WHERE inquiry_id = :iid"
            ),
            {"iid": inquiry_id},
        ).scalars().all()
        return [str(r) for r in rows if r]
    except Exception as exc:  # noqa: BLE001
        logger.debug("list_inquiry_content_ids miss: %s", exc)
        return []
    finally:
        _safe_close(session)


def _restore_touch(store: Any, data: dict[str, Any]) -> Optional[Any]:
    try:
        from app.services.acquisition.growth_ops import ContentTouch
        fields = {f for f in ContentTouch.__dataclass_fields__}  # type: ignore[attr-defined]
        item = ContentTouch(**{k: v for k, v in data.items() if k in fields})
        store._by_content[item.content_id] = item
        for iid in item.inquiry_ids:
            ids = store._by_inquiry.setdefault(str(iid), [])
            if item.content_id not in ids:
                ids.append(item.content_id)
        return item
    except Exception as exc:  # noqa: BLE001
        logger.warning("restore content touch failed: %s", exc)
        return None


def restore_content_for_tenant(store: Any, tenant_id: str = "") -> int:
    restored = 0
    for data in list_content_touches(tenant_id=tenant_id):
        if _restore_touch(store, data) is not None:
            restored += 1
    return restored


def patch_content_attr_persistence(store: Any) -> Any:
    """给 ContentAttributionStore 打补丁：登记/关联写穿 PG；查询内存 miss 则回源。"""
    if getattr(store, "_pg_patched", False):
        return store
    orig_upsert = store.upsert_content
    orig_link = store.link_inquiry
    orig_list = store.list_contents
    orig_sources = store.inquiry_sources

    def upsert_content(**kwargs):
        item = orig_upsert(**kwargs)
        _record_write(store, save_content_touch(item))
        return item

    def link_inquiry(**kwargs):
        out = orig_link(**kwargs)
        if out.get("linked"):
            _record_write(
                store,
                link_content_inquiry(
                    content_id=out.get("content_id", ""),
                    inquiry_id=out.get("inquiry_id", ""),
                    tenant_id=kwargs.get("tenant_id", "") or "",
                ),
            )
            # 同步更新 content touch 的 inquiry_ids
            cid = out.get("content_id", "")
            item = store._by_content.get(cid)
            if item is not None:
                _record_write(store, save_content_touch(item))
        return out

    def list_contents(tenant_id=""):
        out = orig_list(tenant_id=tenant_id)
        if not out:
            if restore_content_for_tenant(store, tenant_id):
                out = orig_list(tenant_id=tenant_id)
        return out

    def inquiry_sources(inquiry_id):
        out = orig_sources(inquiry_id)
        if not out:
            ids = list_inquiry_content_ids(inquiry_id)
            if ids:
                for cid in ids:
                    if cid in store._by_content:
                        continue
                    data = load_content_touch(cid)
                    if data:
                        _restore_touch(store, data)
                out = orig_sources(inquiry_id)
        return out

    store.upsert_content = upsert_content  # type: ignore[method-assign]
    store.link_inquiry = link_inquiry  # type: ignore[method-assign]
    store.list_contents = list_contents  # type: ignore[method-assign]
    store.inquiry_sources = inquiry_sources  # type: ignore[method-assign]
    store._pg_patched = True  # type: ignore[attr-defined]
    store.ensure_pg_table = ensure_tables  # type: ignore[attr-defined]
    ok = False
    try:
        ok = ensure_tables()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ensure content tables failed: %s", exc)
    store.persistence_backend = "postgres" if ok else "memory"  # type: ignore[attr-defined]
    if not ok:
        logger.warning(
            "ContentAttributionStore PG 不可用，已降级为内存存储（重启会丢）；"
            "自述见 store.persistence_report()"
        )
    return store
