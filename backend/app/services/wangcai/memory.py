"""旺财 N3 上下文记忆层（实施指南 §3）。

设计（指南 3.4）：
- SessionStore：get_or_create(visitor_ref, tenant_id) / append_turn / recent_turns；
- build_context(limit=6)：最近 6 轮原文窗口；超出标记 needs_summary
  （摘要由 N4 cost_optimized 档异步生成，写 wangcai_sessions.summary）；
- 会话与租户绑定：(tenant_id, visitor_ref) 唯一——访客串站=数据事故（指南 3.6）；
- 隐私：访客会话属个人数据，90 天清理走现有 gdpr 策略（指南 3.1）。

实现分层：
- 纯逻辑内存实现 InMemorySessionStore（测试 + Redis 不可用兜底）；
- Redis 热缓存（SETEX TTL 1800s）与 DB 持久化（迁移 094 两表）为 S3 接线项，
  接口已按 SessionStore 协议预留，接线不改本层逻辑。
红线：禁止复用 chat_sessions（user_id NOT NULL，实测 models/chat_session.py L18）。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol, Tuple

WINDOW_LIMIT_DEFAULT = 6        # 指南 3.2：最近 6 轮原文
REDIS_TTL_SECONDS = 1800        # 指南 3.2：30 分钟无活动过期（S3 接线用）
SESSION_RETENTION_DAYS = 90     # 指南 3.1：90 天清理（走现有 gdpr 策略）


@dataclass
class Turn:
    role: str                   # user | assistant
    content: str
    intent: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # N8 计量 / N7 证据元数据（迁移 094 qa_log 列）；内存实现忽略，仅落库接线写入（轮14）
    model: Optional[str] = None
    tokens: Optional[int] = None
    citation_refs: Optional[List[str]] = None


@dataclass
class SessionRecord:
    session_id: str
    tenant_id: str
    visitor_ref: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ContextWindow:
    turns: List[Turn]
    needs_summary: bool = False   # 总轮数超窗 → 触发异步摘要（指南 3.2）
    total_turns: int = 0


class SessionStore(Protocol):
    def get_or_create(self, visitor_ref: str, tenant_id: str) -> SessionRecord:
        """get_or_create。

        参数说明：
        :param self: 参数 self
        :param visitor_ref: 参数 visitor_ref
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
    def append_turn(self, session_id: str, turn: Turn) -> None:
        """append_turn。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :param turn: 参数 turn
        :return: 返回处理结果。
        """
    def turns(self, session_id: str) -> List[Turn]:
        """turns。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """


class InMemorySessionStore:
    """内存实现：测试 + Redis 不可用兜底。键=(tenant_id, visitor_ref) 保证租户隔离。"""
    def __init__(self) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._sessions: Dict[str, SessionRecord] = {}
        self._turns: Dict[str, List[Turn]] = {}
        self._by_visitor: Dict[Tuple[str, str], str] = {}

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
        key = (tenant_id, visitor_ref)
        sid = self._by_visitor.get(key)
        if sid and sid in self._sessions:
            rec = self._sessions[sid]
            rec.last_active_at = datetime.now(timezone.utc)
            return rec
        sid = str(uuid.uuid4())
        rec = SessionRecord(session_id=sid, tenant_id=tenant_id, visitor_ref=visitor_ref)
        self._sessions[sid] = rec
        self._turns[sid] = []
        self._by_visitor[key] = sid
        return rec

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
        self._turns.setdefault(session_id, []).append(turn)
        if session_id in self._sessions:
            self._sessions[session_id].last_active_at = datetime.now(timezone.utc)

    def turns(self, session_id: str) -> List[Turn]:
        """turns。

        参数说明：
        :param self: 参数 self
        :param session_id: 参数 session_id
        :return: 返回处理结果。
        """
        return list(self._turns.get(session_id, []))


def build_context(
    store: SessionStore,
    session_id: str,
    limit: int = WINDOW_LIMIT_DEFAULT,
) -> ContextWindow:
    """最近 limit 轮原文窗口；超窗标记 needs_summary（指南 3.2 窗口策略）。"""
    all_turns = store.turns(session_id)
    window = all_turns[-limit:] if len(all_turns) > limit else list(all_turns)
    return ContextWindow(
        turns=window,
        needs_summary=len(all_turns) > limit,
        total_turns=len(all_turns),
    )


def resolve_coreference_hint(turns: List[Turn]) -> Optional[str]:
    """指代解析辅助（指南 3.5 验收："它的密度"关联上一轮"岩棉板"）：
    从最近用户轮中提取产品名词，供 N2 检索补充查询词。纯启发式：
    取最近一轮含实体性名词的内容片段（>1 词/含中文名词段）。
    """
    for turn in reversed(turns):
        if turn.role != "user":
            continue
        text = turn.content.strip()
        if not text:
            continue
        # 简单启发：取上一轮用户问题作为指代上下文
        return text[:120]
    return None
