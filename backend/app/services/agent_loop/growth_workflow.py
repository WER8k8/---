# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""增长工具 Agent 工作流 — 热词 → 成稿 → 质检 → 引流监测快照。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.agent_loop.run_repository import sync_run, upsert_run
from app.services.agent_loop.session_store import load_run, new_run_id, patch_run, patch_task, save_run
from app.services.agent_loop.workflow_presets import preset_by_id
from app.services.growth_tools_service import (
    ai_traffic_overview,
    create_keyword_entry,
    hot_keywords_overview,
    inspect_content_quality,
    list_keyword_library,
)

logger = logging.getLogger(__name__)

FULL_TASK_SPECS: tuple[tuple[str, str], ...] = (
    ("scan_keywords", "扫描热门关键词与词库"),
    ("pick_keyword", "选定本轮主攻关键词"),
    ("prepare_draft", "生成待检草稿"),
    ("quality_inspect", "内容质检（合规/SEO/GEO）"),
    ("traffic_snapshot", "刷新 AI 引流监测快照"),
    ("summarize", "汇总跑盘结论"),
)

MODE_TASKS: dict[str, frozenset[str]] = {
    "full": frozenset(t[0] for t in FULL_TASK_SPECS),
    "quality_only": frozenset({"quality_inspect", "traffic_snapshot", "summarize"}),
    "keyword_only": frozenset({"scan_keywords", "pick_keyword", "summarize"}),
    "traffic_only": frozenset({"traffic_snapshot", "summarize"}),
}


def _now_iso() -> str:
    """实现 nowiso 的功能。
    
    :return: 返回 str 结果
    """
    return datetime.now(timezone.utc).isoformat()


def _tasks_for_mode(mode: str) -> list[tuple[str, str]]:
    """实现 任务for模式 的功能。
    
    :param mode: 参数 mode（类型: str）
    :return: 返回 list[tuple[str, str]] 结果
    """
    allowed = MODE_TASKS.get(mode, MODE_TASKS["full"])
    tasks = [(tid, label) for tid, label in FULL_TASK_SPECS if tid in allowed]
    if mode == "full" and "save_keyword" not in allowed:
        pass
    return tasks


def _pick_focus_keyword(hot: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """实现 pickfocus关键词 的功能。
    
    :param hot: 参数 hot（类型: dict[str, Any]）
    :param context: 参数 context（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    manual = (context.get("focus_keyword") or "").strip()
    if manual:
        return {"keyword": manual, "source": "manual", "search_volume": 0}

    buckets = hot.get("buckets") or {}
    priority = ("demand", "industry", "brand", "competitor")
    for wc in priority:
        items = buckets.get(wc) or []
        if items:
            top = items[0]
            return {
                "keyword": top.get("keyword") or "",
                "source": wc,
                "search_volume": top.get("search_volume") or 0,
            }
    return {"keyword": "B2B 外贸推广", "source": "fallback", "search_volume": 0}


def _build_draft(keyword: str, title: str | None = None) -> dict[str, str]:
    """实现 构建draft 的功能。
    
    :param keyword: 参数 keyword（类型: str）
    :param title: 参数 title（类型: str | None）
    :return: 返回 dict[str, str] 结果
    """
    kw = keyword.strip() or "行业解决方案"
    t = (title or "").strip() or f"{kw}：选型要点与厂家对接指南"
    body = (
        f"{kw} 是不少采购方在比价阶段会重点检索的方向。\n\n"
        f"一、常见应用场景\n"
        f"- 工程项目批量采购与长期供货\n"
        f"- 出口订单对规格、交期与质检文件的硬性要求\n\n"
        f"二、选型建议\n"
        f"- 明确规格等级、检测标准与包装运输要求\n"
        f"- 对比 2–3 家具备同类项目案例的厂家\n\n"
        f"三、下一步\n"
        f"如需报价、样品或技术参数表，欢迎联系我们的业务团队获取方案与交期评估。"
    )
    return {"title": t, "body": body}


def create_growth_run(
    *,
    goal: str,
    tenant_id: str | None,
    user_id: str | None,
    context: dict[str, Any] | None = None,
    preset_id: str | None = None,
) -> dict[str, Any]:
    """实现 创建growth执行 的功能。
    
    :param goal: 参数 goal（类型: str）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :param user_id: 参数 user_id（类型: str | None）
    :param context: 参数 context（类型: dict[str, Any] | None）
    :param preset_id: 参数 preset_id（类型: str | None）
    :return: 返回 dict[str, Any] 结果
    """
    ctx = dict(context or {})
    preset = preset_by_id(preset_id)
    mode = ctx.get("mode") or (preset.get("mode") if preset else None) or "full"
    ctx["mode"] = mode
    if preset and not goal.strip():
        goal = preset.get("goal") or goal

    run_id = new_run_id()
    task_specs = _tasks_for_mode(mode)
    tasks = [
        {
            "id": tid,
            "title": label,
            "status": "pending",
            "summary": None,
            "error": None,
            "output": None,
            "started_at": None,
            "finished_at": None,
        }
        for tid, label in task_specs
    ]
    run = {
        "id": run_id,
        "workflow": "growth_autopilot",
        "preset_id": preset_id,
        "mode": mode,
        "goal": (goal or "跑一轮增长诊断").strip()[:500],
        "status": "pending",
        "progress": 0,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "context": ctx,
        "tasks": tasks,
        "artifacts": {},
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "finished_at": None,
    }
    save_run(run)
    return run


def get_growth_run(db: Session, run_id: str) -> dict[str, Any] | None:
    """实现 获取growth执行 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run_id: 参数 run_id（类型: str）
    :return: 返回 dict[str, Any] | None 结果
    """
    from app.services.agent_loop.run_repository import get_run
    return get_run(db, run_id)


class _GrowthRunExecutor:
    def __init__(self, db: Session, run_id: str, *, tenant_id: str | None) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param run_id: 参数 run_id
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        self.db = db
        self.run_id = run_id
        self.tenant_id = tenant_id
        self.ctx: dict[str, Any] = {}
        self.artifacts: dict[str, Any] = {}
        self.mode = "full"
        self._hot: dict[str, Any] | None = None
        self._focus: dict[str, Any] | None = None
        self._draft: dict[str, Any] | None = None
        self._report: dict[str, Any] | None = None
        self._traffic_summary: dict[str, Any] = {}

    def _sync(self) -> None:
        """_sync。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        sync_run(self.db, self.run_id)

    def _start(self, task_id: str) -> None:
        """_start。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :return: 返回处理结果。
        """
        patch_task(self.run_id, task_id, status="running", started_at=_now_iso())
        self._sync()

    def _done(self, task_id: str, summary: str, output: Any = None) -> None:
        """_done。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :param summary: 参数 summary
        :param output: 参数 output
        :return: 返回处理结果。
        """
        patch_task(
            self.run_id,
            task_id,
            status="completed",
            summary=summary,
            output=output,
            finished_at=_now_iso(),
        )
        self._sync()

    def _skip(self, task_id: str, reason: str) -> None:
        """_skip。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :param reason: 参数 reason
        :return: 返回处理结果。
        """
        patch_task(
            self.run_id,
            task_id,
            status="skipped",
            summary=reason,
            finished_at=_now_iso(),
        )
        self._sync()

    def _fail(self, task_id: str, message: str) -> None:
        """_fail。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :param message: 参数 message
        :return: 返回处理结果。
        """
        patch_task(
            self.run_id,
            task_id,
            status="failed",
            error=message,
            finished_at=_now_iso(),
        )
        patch_run(self.run_id, status="failed", finished_at=_now_iso(), error=message)
        self._sync()

    def _task_enabled(self, task_id: str) -> bool:
        """_task_enabled。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :return: 返回处理结果。
        """
        run = load_run(self.run_id) or {}
        return any(t.get("id") == task_id for t in (run.get("tasks") or []))

    def _run_if_enabled(self, task_id: str, fn: Callable[[], None]) -> None:
        """_run_if_enabled。

        参数说明：
        :param self: 参数 self
        :param task_id: 参数 task_id
        :param fn: 参数 fn
        :return: 返回处理结果。
        """
        if not self._task_enabled(task_id):
            return
        fn()

    def step_scan_keywords(self) -> None:
        """step_scan_keywords。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("scan_keywords"):
            return
        self._start("scan_keywords")
        self._hot = hot_keywords_overview(self.db, tenant_id=self.tenant_id)
        library = list_keyword_library(self.db, tenant_id=self.tenant_id)
        payload = {
            "total": self._hot.get("total"),
            "totals": self._hot.get("totals"),
            "library_count": len(library),
        }
        self.artifacts["hot_keywords"] = payload
        self._done(
            "scan_keywords",
            f"热词 {self._hot.get('total', 0)} 条 · 专属词库 {len(library)} 条",
            payload,
        )

    def step_pick_keyword(self) -> None:
        """step_pick_keyword。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("pick_keyword"):
            return
        self._start("pick_keyword")
        hot = self._hot or hot_keywords_overview(self.db, tenant_id=self.tenant_id)
        focus = _pick_focus_keyword(hot, self.ctx)
        if not focus.get("keyword"):
            self._fail("pick_keyword", "未找到可用关键词，请手动指定 focus_keyword")
            raise RuntimeError("pick_keyword failed")
        self._focus = focus
        self.ctx["focus_keyword"] = focus["keyword"]
        self.artifacts["focus_keyword"] = focus
        self._done(
            "pick_keyword",
            f"主攻词：{focus['keyword']}（来源 {focus['source']}）",
            focus,
        )

    def step_prepare_draft(self) -> None:
        """step_prepare_draft。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("prepare_draft"):
            return
        self._start("prepare_draft")
        focus = self._focus or {"keyword": self.ctx.get("focus_keyword") or "行业词"}
        user_body = (self.ctx.get("content_body") or "").strip()
        user_title = (self.ctx.get("content_title") or "").strip()
        if len(user_body) >= 10:
            draft = {
                "title": user_title or focus.get("keyword") or "待检稿件",
                "body": user_body,
                "source": "user",
            }
        else:
            draft = {**_build_draft(str(focus.get("keyword") or ""), user_title or None), "source": "template"}
        self._draft = draft
        self.artifacts["draft"] = {
            "title": draft["title"],
            "body": draft["body"],
            "source": draft["source"],
            "length": len(draft["body"]),
        }
        self._done(
            "prepare_draft",
            f"草稿就绪（{draft['source']}，{len(draft['body'])} 字）",
            self.artifacts["draft"],
        )

    def step_quality_inspect(self) -> None:
        """step_quality_inspect。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("quality_inspect"):
            return
        self._start("quality_inspect")
        if self.mode == "quality_only":
            user_body = (self.ctx.get("content_body") or "").strip()
            if len(user_body) < 10:
                self._fail("quality_inspect", "质检模式需填写至少 10 字的待检正文")
                raise RuntimeError("quality_inspect missing body")
            if not self._draft:
                kw = (self.ctx.get("focus_keyword") or "行业词").strip()
                self._draft = {
                    "title": (self.ctx.get("content_title") or kw).strip(),
                    "body": user_body,
                    "source": "user",
                }
                self._focus = {"keyword": kw, "source": "manual", "search_volume": 0}
        if not self._draft:
            self.step_prepare_draft()
        draft = self._draft or {}
        focus_kw = (self._focus or {}).get("keyword") or self.ctx.get("focus_keyword") or ""
        keywords = [focus_kw] if focus_kw else []
        extra = self.ctx.get("extra_keywords") or []
        if isinstance(extra, list):
            keywords.extend(str(k).strip() for k in extra if str(k).strip())
        report = inspect_content_quality(
            self.db,
            title=draft.get("title") or "",
            body=draft.get("body") or "",
            keywords=keywords,
        )
        self._report = report
        self.artifacts["inspect_report"] = report
        grade = report.get("grade", "-")
        passed = report.get("passed")
        self._done(
            "quality_inspect",
            f"质检 {'通过' if passed else '需修改'} · 等级 {grade}",
            {
                "passed": passed,
                "grade": grade,
                "summary": report.get("summary"),
                "blockers": (report.get("blockers") or [])[:8],
            },
        )

    def step_traffic_snapshot(self) -> None:
        """step_traffic_snapshot。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("traffic_snapshot"):
            return
        self._start("traffic_snapshot")
        traffic = ai_traffic_overview(self.db)
        self._traffic_summary = traffic.get("summary") or {}
        self.artifacts["traffic"] = self._traffic_summary
        self.artifacts["traffic_detail"] = {
            "ai_platforms": (traffic.get("ai_platforms") or [])[:5],
            "probe_idle_count": sum(
                1
                for c in (traffic.get("ai_platforms") or []) + (traffic.get("search_platforms") or [])
                if c.get("traffic_signal") == "idle"
            ),
        }
        s = self._traffic_summary
        self._done(
            "traffic_snapshot",
            (
                f"监测 {s.get('platforms', 0)} 通道 · "
                f"API探针 {s.get('probe_ready', 0)} · "
                f"收录率 {s.get('overall_inclusion_rate', 0)}%"
            ),
            self._traffic_summary,
        )

    def step_summarize(self) -> None:
        """step_summarize。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if not self._task_enabled("summarize"):
            return
        self._start("summarize")
        focus_kw = (self._focus or {}).get("keyword") or self.ctx.get("focus_keyword") or "-"
        report = self._report or self.artifacts.get("inspect_report") or {}
        summary = self._traffic_summary or self.artifacts.get("traffic") or {}
        conclusion = {
            "focus_keyword": focus_kw,
            "quality_grade": report.get("grade"),
            "quality_passed": report.get("passed"),
            "platforms_monitored": summary.get("platforms"),
            "probe_ready": summary.get("probe_ready"),
            "mode": self.mode,
            "next_actions": [],
            "links": [
                {"label": "SEO 矩阵发布", "path": "/seo-matrix/publish"},
                {"label": "收录监控", "path": "/seo-matrix/inclusion"},
                {"label": "GEO 引擎", "path": "/admin/geo-engine"},
            ],
        }
        if report and not report.get("passed"):
            for b in (report.get("blockers") or [])[:3]:
                conclusion["next_actions"].append(f"质检：{b}")
        if (summary.get("probe_ready") or 0) < (summary.get("platforms") or 0):
            conclusion["next_actions"].append("为「探索中/待接入」通道配置 API Key 或收录探针")
        if self.mode == "keyword_only":
            conclusion["next_actions"].append("确认主攻词后，可运行「全链路诊断」生成草稿并质检")
        if not conclusion["next_actions"]:
            conclusion["next_actions"].append("草稿可进入 SEO 矩阵发布队列")

        if self.ctx.get("save_focus_keyword") and self._focus and self._focus.get("source") not in ("manual",):
            wc = self._focus.get("source") or "industry"
            if wc not in ("industry", "brand", "competitor", "demand"):
                wc = "industry"
            try:
                create_keyword_entry(
                    self.db,
                    keyword=self._focus["keyword"],
                    word_class=wc,
                    tenant_id=self.tenant_id,
                    search_volume=int(self._focus.get("search_volume") or 0),
                    source="agent_run",
                )
                conclusion["next_actions"].insert(0, f"已将「{focus_kw}」写入专属词库")
            except ValueError:
                pass

        self.artifacts["conclusion"] = conclusion
        grade = report.get("grade", "-")
        self._done(
            "summarize",
            f"跑盘完成 · {focus_kw} · 质检 {grade}",
            conclusion,
        )

    def execute(self) -> None:
        """execute。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        run = load_run(self.run_id)
        if not run:
            return
        self.ctx = dict(run.get("context") or {})
        self.mode = str(self.ctx.get("mode") or "full")
        if self.mode == "quality_only" and len((self.ctx.get("content_body") or "").strip()) < 10:
            self._fail("quality_inspect", "质检模式需至少 10 字正文")
            return

        steps = [
            self.step_scan_keywords,
            self.step_pick_keyword,
            self.step_prepare_draft,
            self.step_quality_inspect,
            self.step_traffic_snapshot,
            self.step_summarize,
        ]
        for step in steps:
            current = load_run(self.run_id) or {}
            if current.get("status") == "failed":
                return
            try:
                step()
            except RuntimeError:
                return

        patch_run(
            self.run_id,
            status="completed",
            artifacts=self.artifacts,
            context=self.ctx,
            finished_at=_now_iso(),
        )
        self._sync()


def execute_growth_run(db: Session, run_id: str, *, tenant_id: str | None = None) -> None:
    """实现 执行growth执行 的功能。
    
    :param db: 参数 db（类型: Session）
    :param run_id: 参数 run_id（类型: str）
    :param tenant_id: 参数 tenant_id（类型: str | None）
    :return: 返回 None 结果
    """
    run = load_run(run_id)
    if not run or run.get("status") not in ("pending", "running"):
        return

    patch_run(run_id, status="running")
    upsert_run(db, load_run(run_id) or run)
    try:
        _GrowthRunExecutor(db, run_id, tenant_id=tenant_id).execute()
    except Exception as exc:
        logger.exception("growth agent run failed run_id=%s", run_id)
        current = load_run(run_id) or {}
        pending = next(
            (t for t in (current.get("tasks") or []) if t.get("status") in ("pending", "running")),
            None,
        )
        if pending:
            patch_task(
                run_id,
                pending["id"],
                status="failed",
                error=str(exc),
                finished_at=_now_iso(),
            )
        patch_run(run_id, status="failed", finished_at=_now_iso(), error=str(exc))
        sync_run(db, run_id)
