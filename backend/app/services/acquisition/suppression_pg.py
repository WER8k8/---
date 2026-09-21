# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P3-5 抑制名单 PG 持久化（合规真源）。

为什么必须落库：
    退订/投诉抑制属于**合规义务**（GDPR/CAN-SPAM：用户退订后不得再发）。
    原实现是进程内 dict（suppression_list.py 的 _by_key），进程重启/多副本部署即丢失，
    会导致「用户已退订但系统又发了一遍」——这是可被投诉定责的事故。

设计（与 ops_card_pg.py 同范式，最小侵入）：
    · 结构化列存储，便于合规审计与按租户查询
    · 主键 (tenant_id, email)：同租户同邮箱唯一，天然幂等
    · 无库/失败诚实降级（返回 False / 空列表），由上层决定行为

红线保持：解除抑制仍必须 confirm=true（在 suppression_list.py 层强制）。
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS acquisition_suppression (
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    reason TEXT DEFAULT '',
    source TEXT DEFAULT '',
    created_by TEXT DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (tenant_id, email)
);
CREATE INDEX IF NOT EXISTS ix_acq_suppression_tenant
    ON acquisition_suppression (tenant_id);
"""


def _db():
    try:
        from app.core.database import SessionLocal

        return SessionLocal()
    except Exception:  # noqa: BLE001
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
        logger.warning("ensure suppression table: %s", exc)
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


def save_entry(
    *,
    tenant_id: str,
    email: str,
    reason: str = "",
    source: str = "",
    created_by: str = "system",
) -> bool:
    """写入抑制记录（主键冲突则忽略，保持「只增」语义）。"""
    session = _db()
    if session is None:
        return False
    try:
        from sqlalchemy import text

        session.execute(text(DDL))
        session.execute(
            text(
                """
                INSERT INTO acquisition_suppression
                    (tenant_id, email, reason, source, created_by, created_at)
                VALUES (:t, :e, :r, :s, :cb, now())
                ON CONFLICT (tenant_id, email) DO NOTHING
                """
            ),
            {"t": tenant_id, "e": email, "r": reason, "s": source, "cb": created_by},
        )
        session.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        try:
            session.rollback()
        except Exception:
            pass
        logger.warning("save suppression entry failed: %s", exc)
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def delete_entry(*, tenant_id: str, email: str) -> bool:
    """删除抑制记录（仅人工 confirm 后调用）。"""
    session = _db()
    if session is None:
        return False
    try:
        from sqlalchemy import text

        session.execute(
            text("DELETE FROM acquisition_suppression WHERE tenant_id = :t AND email = :e"),
            {"t": tenant_id, "e": email},
        )
        session.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        try:
            session.rollback()
        except Exception:
            pass
        logger.warning("delete suppression entry failed: %s", exc)
        return False
    finally:
        try:
            session.close()
        except Exception:
            pass


def get_entry(*, tenant_id: str, email: str) -> Optional[dict[str, Any]]:
    session = _db()
    if session is None:
        return None
    try:
        from sqlalchemy import text

        row = session.execute(
            text(
                "SELECT tenant_id, email, reason, source, created_by, created_at "
                "FROM acquisition_suppression WHERE tenant_id = :t AND email = :e"
            ),
            {"t": tenant_id, "e": email},
        ).first()
        return _row_to_dict(row)
    except Exception as exc:  # noqa: BLE001
        logger.debug("get suppression entry miss: %s", exc)
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


def list_entries(tenant_id: str = "") -> list[dict[str, Any]]:
    """按租户列出抑制记录；tenant_id 为空则列全部（跨租户审计用）。"""
    session = _db()
    if session is None:
        return []
    try:
        from sqlalchemy import text

        if tenant_id:
            rows = session.execute(
                text(
                    "SELECT tenant_id, email, reason, source, created_by, created_at "
                    "FROM acquisition_suppression WHERE tenant_id = :t ORDER BY created_at DESC"
                ),
                {"t": tenant_id},
            ).fetchall()
        else:
            rows = session.execute(
                text(
                    "SELECT tenant_id, email, reason, source, created_by, created_at "
                    "FROM acquisition_suppression ORDER BY created_at DESC"
                )
            ).fetchall()
        return [d for d in (_row_to_dict(r) for r in rows) if d]
    except Exception as exc:  # noqa: BLE001
        logger.debug("list suppression miss: %s", exc)
        return []
    finally:
        try:
            session.close()
        except Exception:
            pass


def _row_to_dict(row) -> Optional[dict[str, Any]]:
    if not row:
        return None
    created = row[5]
    return {
        "email": row[1],
        "tenant_id": row[0],
        "reason": row[2] or "",
        "source": row[3] or "",
        "created_by": row[4] or "system",
        "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created or ""),
    }
