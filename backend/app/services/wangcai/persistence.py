"""旺财 N3/N7 持久化接线（迁移 094：wangcai_sessions + wangcai_qa_log，轮14）。

设计纪律（对齐总纲 §7A.3 / 实施指南 3.4、4.4-4）：
- 特性开关 `WANGCAI_QA_PERSIST_ENABLED` 默认关（零回归；目标库 `alembic upgrade head`
  落库前开关不开启，DbSessionStore 对缺表/故障自身也有降级保护）；
- **任何 DB 故障不得阻断回复**（公开挂件入口红线）：
  get_or_create 失败 → 内存会话降级；append_turn 失败 → 仅内存留痕；
  turns 失败 → 内存窗口兜底；
- 一表两用：每轮对话写 `wangcai_qa_log`（user/assistant），assistant 轮附
  model/tokens/citation_refs（N8 计量供数 + N7 证据，Evidence 留痕）；
- 会话与租户绑定：(tenant_id, visitor_ref) 唯一——访客串站=数据事故（指南 3.6）；
- 内容截断（访客输入不可信，R9）：user ≤500 字 / assistant ≤4000 字。
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from app.services.wangcai.memory import (
    InMemorySessionStore,
    SessionRecord,
    Turn,
)

logger = logging.getLogger(__name__)

USER_CONTENT_MAX = 500        # 访客问题截断（防超长/注入语料大体积写库）
ASSISTANT_CONTENT_MAX = 4000  # 回复截断
TURNS_FETCH_LIMIT = 20        # turns() 回读上限（上下文窗口只用最近 6 轮，留余量）


def qa_persist_enabled() -> bool:
    """qa_log 落库开关（默认关，零回归）。"""
    return os.environ.get("WANGCAI_QA_PERSIST_ENABLED", "0") == "1"


class DbSessionStore:
    """迁移 094 两表的 SessionStore 实现（协议同 memory.SessionStore）。

    内存影子存储 `_shadow` 保证 DB 故障时上下文窗口仍可用（降级不丢会话）。
    模型类可注入（`models=(SessionModel, QaLogModel)`），便于纯逻辑测试。
    """
    def __init__(self, db, models: Optional[Tuple[Any, Any]] = None) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param models: 参数 models
        :return: 返回处理结果。
        """
        self.db = db
        self._shadow = InMemorySessionStore()
        if models is None:
            from app.models.wangcai import WangcaiQaLog, WangcaiSession  # noqa: PLC0415
            models = (WangcaiSession, WangcaiQaLog)
        self.SessionModel, self.QaLogModel = models

    # ------------------------------------------------------------------
    def get_or_create(self, visitor_ref: str, tenant_id: str) -> SessionRecord:
        """get_or_create。

        参数说明：
        :param self: 参数 self
        :param visitor_ref: 参数 visitor_ref
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        if not visitor_ref or not tenant_id:
            raise ValueError("visitor_ref 与 tenant_id 必填（租户隔离红线，指南 3.6）")
        try:
            SM = self.SessionModel
            row = (
                self.db.query(SM)
                .filter(SM.tenant_id == tenant_id, SM.visitor_ref == visitor_ref)
                .first()
            )
            now = datetime.now(timezone.utc)
            if row is None:
                row = SM(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    visitor_ref=visitor_ref,
                    turn_count=0,
                    created_at=now,
                    last_active_at=now,
                )
                self.db.add(row)
            else:
                row.last_active_at = now
            self.db.commit()
            rec = SessionRecord(
                session_id=row.id,
                tenant_id=tenant_id,
                visitor_ref=visitor_ref,
            )
            self._shadow._sessions[rec.session_id] = rec  # noqa: SLF001 — 影子登记（降级兜底）
            self._shadow._turns.setdefault(rec.session_id, [])  # noqa: SLF001
            return rec
        except Exception:  # noqa: BLE001 — DB 故障降级内存会话，不阻断回复
            logger.warning("wangcai DbSessionStore.get_or_create 失败，降级内存会话")
            self._safe_rollback()
            return self._shadow.get_or_create(visitor_ref, tenant_id)

    def append_turn(self, session_id: str, turn: Turn) -> None:
        """append_turn。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :param turn: 参数 turn
        :return: 返回处理结果。
        """
        if turn.role not in ("user", "assistant"):
            raise ValueError("role 必须为 user|assistant（迁移 094 约束）")
        # 内存影子先行：DB 故障时 turns() 窗口仍可用
        self._shadow.append_turn(session_id, turn)
        try:
            QM = self.QaLogModel
            self.db.add(QM(
                id=str(uuid.uuid4()),
                tenant_id=self._tenant_of(session_id),
                session_id=session_id,
                role=turn.role,
                intent=(turn.intent or "")[:40] or None,
                content=self._clip(turn.content, turn.role),
                citation_refs=json.dumps(turn.citation_refs, ensure_ascii=False)
                if turn.citation_refs else None,
                model=(turn.model or "")[:60] or None,
                tokens=turn.tokens,
                created_at=datetime.now(timezone.utc),
            ))
            self._bump_session(session_id)
            self.db.commit()
        except Exception:  # noqa: BLE001 — 落库失败不影响回复（内存影子已留痕）
            logger.warning("wangcai qa_log 落库失败（内存窗口不受影响）")
            self._safe_rollback()

    def turns(self, session_id: str) -> List[Turn]:
        """turns。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        try:
            QM = self.QaLogModel
            rows = (
                self.db.query(QM)
                .filter(QM.session_id == session_id)
                .order_by(QM.created_at.asc())
                .limit(TURNS_FETCH_LIMIT)
                .all()
            )
            if not rows:
                return self._shadow.turns(session_id)
            out: List[Turn] = []
            for r in rows:
                refs = None
                if getattr(r, "citation_refs", None):
                    try:
                        refs = json.loads(r.citation_refs)
                    except Exception:
                        refs = None
                out.append(Turn(
                    role=r.role,
                    content=r.content or "",
                    intent=r.intent,
                    model=getattr(r, "model", None),
                    tokens=getattr(r, "tokens", None),
                    citation_refs=refs,
                ))
            return out
        except Exception:  # noqa: BLE001 — 读失败回内存窗口
            logger.warning("wangcai qa_log 读取失败，回退内存窗口")
            return self._shadow.turns(session_id)

    # ------------------------------------------------------------------
    def _tenant_of(self, session_id: str) -> str:
        """_tenant_of。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        rec = self._shadow._sessions.get(session_id)  # noqa: SLF001
        return rec.tenant_id if rec else ""

    def _bump_session(self, session_id: str) -> None:
        """_bump_session。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        SM = self.SessionModel
        row = self.db.query(SM).filter(SM.id == session_id).first()
        if row is not None:
            row.turn_count = int(getattr(row, "turn_count", 0) or 0) + 1
            row.last_active_at = datetime.now(timezone.utc)

    def _safe_rollback(self) -> None:
        """_safe_rollback。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        try:
            self.db.rollback()
        except Exception:
            pass

    @staticmethod
    def _clip(content: str, role: str) -> str:
        """_clip。

        参数说明：
        :param content: 参数 content
        :param role: 参数 role
        :return: 返回处理结果。
        """
        limit = USER_CONTENT_MAX if role == "user" else ASSISTANT_CONTENT_MAX
        text = content or ""
        return text[:limit]
