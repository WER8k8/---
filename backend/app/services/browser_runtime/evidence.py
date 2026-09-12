"""证据回传模型（总纲 §4.7 P5：合规执行须留证）。

每次 Browser Runtime 实际执行（无论成功失败）必须产出 EvidenceRecord
（结构化、append-only、可追溯）；本轮 25-B 落地 dataclass + 序列化方法，
存储与持久化由调用方按需落地（DB/对象存储/日志）。EvidenceEntry 不入 ai_tasks
真相源，仅作为审计附件（与 task_traces.evidence 字段同源）。
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

log = logging.getLogger(__name__)

# 集中落盘目录（env 可覆盖；默认 data/browser_evidence，相对 cwd 或绝对均可）
_EVIDENCE_DIR_ENV = os.environ.get("BROWSER_EVIDENCE_DIR") or "data/browser_evidence"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# 执行结果枚举（与 ai_tasks TASK_STATUSES 解耦——Browser 执行是动作，任务状态是工作状态）
EXEC_PENDING = "pending"
EXEC_RUNNING = "running"
EXEC_SUCCESS = "success"
EXEC_FAILED = "failed"
EXEC_BLOCKED = "blocked"  # Policy 拒绝
EXEC_DEGRADED = "degraded"  # 降级 noop（开关/白名单/依赖缺失）

# 轮25-D：EvidenceRecord 自身对填值净化后文本的裁剪长度
FILL_MAX_LEN = 4000  # 与 Policy FILL_MAX_LENGTH 区分：Evidence 仅留摘要


@dataclass
class EvidenceRecord:
    """Browser Runtime 执行证据（append-only）。"""

    id: str = field(default_factory=_new_uuid)
    tenant_id: Optional[str] = None
    actor: str = ""  # 调用方标识：deerflow / paperclip / wangcai / hermes / manual
    action: str = ""  # 动作标识：navigate / fill / click / extract / screenshot
    target_url: Optional[str] = None
    status: str = EXEC_PENDING
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None
    duration_ms: int = 0
    # 执行输入（已通过 brand_guard 净化——不在本轮）
    input_summary: Optional[str] = None
    # 执行输出（截断存储，正文入对象存储，DB 仅留引用）
    output_ref: Optional[str] = None
    output_summary: Optional[str] = None
    # 轮25-C：截图本地路径（DB 仅留引用，正文入对象存储在调用方层做）
    screenshot_path: Optional[str] = None
    screenshot_size_bytes: int = 0
    # 轮25-D：写动作专用字段
    # fill：填充的 selector + 净化后文本（原文不入库，sanitize 后留证）
    fill_selector: Optional[str] = None
    fill_value_sanitized: Optional[str] = None
    fill_value_original_len: int = 0
    # click：被点击的 selector（去重已通过 check_click_target）
    click_target: Optional[str] = None
    # submit：高阶 Policy 判定
    submit_approval_id: Optional[str] = None
    submit_auto: bool = False
    # 轮25-F：drag 起点/终点 selector
    drag_from_selector: Optional[str] = None
    drag_to_selector: Optional[str] = None
    # 轮25-F：upload 文件路径列表（仅路径摘要，正文不入库）
    upload_file_paths: list[str] = field(default_factory=list)
    upload_count: int = 0
    # 轮25-F：keyboard 文本（截断 4000）+ 按键序列（截断 50）
    keyboard_text: Optional[str] = None
    keyboard_keys: list[str] = field(default_factory=list)
    # 错误/拒绝详情
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    # Policy 裁决（如适用）
    policy_verdict: Optional[dict[str, Any]] = None
    # 扩展元数据（动作相关参数、租户 Profile hash 等）
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_running(self) -> None:
        self.status = EXEC_RUNNING
        self.started_at = _utcnow()

    def mark_success(
        self,
        *,
        output_ref: Optional[str] = None,
        output_summary: Optional[str] = None,
        duration_ms: int = 0,
        screenshot_path: Optional[str] = None,
        screenshot_size_bytes: int = 0,
        fill_selector: Optional[str] = None,
        fill_value_sanitized: Optional[str] = None,
        fill_value_original_len: int = 0,
        click_target: Optional[str] = None,
        submit_approval_id: Optional[str] = None,
        submit_auto: Optional[bool] = None,
    ) -> None:
        self.status = EXEC_SUCCESS
        self.finished_at = _utcnow()
        if output_ref is not None:
            self.output_ref = output_ref
        if output_summary is not None:
            self.output_summary = output_summary[:1000] if output_summary else None
        if screenshot_path is not None:
            self.screenshot_path = screenshot_path
        if screenshot_size_bytes:
            self.screenshot_size_bytes = int(screenshot_size_bytes)
        # 轮25-D 写动作字段
        if fill_selector is not None:
            self.fill_selector = fill_selector
        if fill_value_sanitized is not None:
            self.fill_value_sanitized = fill_value_sanitized[:FILL_MAX_LEN]
        if fill_value_original_len:
            self.fill_value_original_len = int(fill_value_original_len)
        if click_target is not None:
            self.click_target = click_target
        if submit_approval_id is not None:
            self.submit_approval_id = submit_approval_id
        if submit_auto is not None:
            self.submit_auto = bool(submit_auto)
        self.duration_ms = duration_ms or int(
            (self.finished_at - self.started_at).total_seconds() * 1000
        )

    def mark_failed(
        self,
        *,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
    ) -> None:
        self.status = EXEC_FAILED
        self.finished_at = _utcnow()
        self.error_code = error_code
        self.error_message = (error_message or "")[:2000] or None
        self.duration_ms = duration_ms or int(
            (self.finished_at - self.started_at).total_seconds() * 1000
        )

    def mark_blocked(
        self,
        *,
        policy_verdict: dict[str, Any],
        error_code: str = "POLICY_DENIED",
    ) -> None:
        self.status = EXEC_BLOCKED
        self.finished_at = _utcnow()
        self.policy_verdict = dict(policy_verdict)
        self.error_code = error_code
        self.duration_ms = 0

    def mark_degraded(
        self,
        *,
        error_code: str = "BROWSER_RUNTIME_UNAVAILABLE",
        error_message: str = "",
    ) -> None:
        """降级 noop（开关/白名单/依赖缺失均走这条）。"""
        self.status = EXEC_DEGRADED
        self.finished_at = _utcnow()
        self.error_code = error_code
        self.error_message = error_message[:500] or None
        self.duration_ms = 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("started_at", "finished_at"):
            v = d.get(k)
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


# ──────────────────────────────────────────────
# 持久化（打通"仅落盘不入库"断点）
# ──────────────────────────────────────────────
def persist_evidence(
    evidence: "EvidenceRecord",
    *,
    task_id: Optional[str] = None,
    db: Any = None,
) -> dict[str, Any]:
    """集中持久化 Browser 取证。

    解决此前"EvidenceRecord 仅内存构造、调用方散落落盘/不入库"的断点：

    1. **总是**写一条 JSONL 审计行到本地（按 tenant 分目录），可审计、可回溯；
    2. 若 `db` 与 `task_id` 均可用，则把证据以 append-only 方式并入
       `task_traces.artifacts`（**已有 JSON 列，无需新增列/迁移**）。
       特别注意：**按 task_id 精确定位**，绝不写"最新一行"——并发下会把证据
       挂到无关任务上造成数据污染（"每个环节做正确的事"）。
       表/行缺失、DB 不可达 → 降级为仅落盘并记 `db_reason`，**绝不抛异常**，
       不阻断调用方主链路。

    Returns:
        {"disk": bool, "db": bool, "db_reason": str|None} 落地状态，
        便于调用方与运维观测链路是否真正打通。
    """
    result: dict[str, Any] = {"disk": False, "db": False, "db_reason": None}
    record = evidence.to_dict()
    record["_persisted_at"] = _utcnow().isoformat()
    if task_id:
        record["_task_id"] = task_id

    # 1) 集中落盘（JSONL 审计，append-only）
    try:
        tenant = str(evidence.tenant_id or "global")
        # 调用时读取 env（非导入时），保证进程启动后设置的 BROWSER_EVIDENCE_DIR 生效
        base = os.environ.get("BROWSER_EVIDENCE_DIR") or _EVIDENCE_DIR_ENV
        os.makedirs(base, exist_ok=True)
        tenant_dir = os.path.join(base, tenant)
        os.makedirs(tenant_dir, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with open(os.path.join(tenant_dir, "audit.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        result["disk"] = True
    except Exception as exc:  # noqa: BLE001
        log.warning("persist_evidence: 落盘失败 %s", exc)

    # 2) 入库：复用 task_traces.artifacts（已存在的 JSON 列，无需迁移）
    if db is None:
        result["db_reason"] = "no_db"
        return result

    try:
        from sqlalchemy import inspect as sa_inspect

        from app.models.trace import TaskTrace

        insp = sa_inspect(db.bind)
        if not insp.has_table("task_traces"):
            result["db_reason"] = "table_missing"
            return result
        cols = [c["name"] for c in insp.get_columns("task_traces")]
        if "artifacts" not in cols:
            result["db_reason"] = "artifacts_column_missing"
            return result

        row = None
        if task_id:
            row = db.query(TaskTrace).filter(TaskTrace.id == str(task_id)).first()
            if row is None:
                result["db_reason"] = "task_trace_not_found_fallback_created"

        if row is not None:
            current = row.artifacts if isinstance(row.artifacts, list) else []
            current.append(record)
            # 重新赋值以触发 SQLAlchemy dirty tracking（原地 append 不会被检测）
            row.artifacts = current
            db.commit()
            result["db"] = True
            return result

        # 无 task_id（或找不到对应 trace）→ 新建一条独立 trace 承载证据，
        # 保证取证必然入库可追溯，而不是静默丢弃。
        row = TaskTrace(
            trace_type="browser_evidence",
            source_id=str(evidence.id),
            status=str(evidence.status or "success"),
            success=(evidence.status == "success"),
            input_summary=evidence.input_summary,
            output_summary=evidence.output_summary,
            artifacts=[record],
            duration_ms=int(evidence.duration_ms or 0),
            error_code=evidence.error_code,
            error_message=evidence.error_message,
        )
        # tenant_id 为 UUID 列：非法 UUID（如 "global"）会导致 PG 报错，
        # 故先尝试写入，失败则降级为 None 重试一次，不阻断主链路。
        if evidence.tenant_id:
            row.tenant_id = str(evidence.tenant_id)
        try:
            db.add(row)
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            row.tenant_id = None
            db.add(row)
            db.commit()
        result["db"] = True
        result["db_trace_id"] = str(row.id)
    except Exception as exc:  # noqa: BLE001
        # DB 不可达 / 模型变更 → 已降级落盘，绝不阻断主链路
        result["db_reason"] = f"error: {str(exc)[:120]}"
        log.warning("persist_evidence: 入库失败，已降级落盘 %s", exc)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass

    return result
