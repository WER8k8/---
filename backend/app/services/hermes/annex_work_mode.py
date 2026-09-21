# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""本项目能力域工作模式契约 · 双平面 + Hermes 原生直驱 + 黄金路径.

设计出处：docs/GoodJob整仓融入施工总案-2026-09-19.md §3（优化版）。
主理人拍板：TradeAI=本项目拓客、goodjob_crm=本项目 CRM；
由爱马仕 Hermes **进程内直驱**（无外挂桥）；交互走 UJ API；
DSH 非每单必经；SYSTEM-LOCK=能力域逻辑锁。
"""
from __future__ import annotations

from typing import Any, FrozenSet, Iterable

# ── 双平面 ──────────────────────────────────────────────
PLANE_INTERACTIVE = "interactive"  # 列表/详情/CRUD → UJ API 同步
PLANE_TASK = "task"  # 多步/外发/单证/跨系统 → Hermes

INTERACTIVE_PLANE_RULES: tuple[str, ...] = (
    "列表、详情、字段编辑、会话查看走优丁 API 同步返回",
    "禁止强制经过 DSH 或完整 TaskGraph",
    "鉴权=UJ RBAC；数据真相=优丁 PG",
)

TASK_PLANE_RULES: tuple[str, ...] = (
    "多步拓客/外发/PI·CI·PL/履约走 Hermes 编排",
    "默认 source=L1_template（DSH 非必经）",
    "DSH 仅用于模糊/复杂意图，失败降级 L1 或 L3_minimal",
    "TradeAI/GoodJob 已并入优丁能力域，禁止第二套调度面",
    "执行器诚实 failed/degraded，禁止假成功",
    "执行路径=优丁原生服务层（native_fulfillment / native_acquisition），无外挂 HTTP 桥",
)

# ── 分层位置（法定，防设计漂移）────────────────────────
LAYER_STACK: tuple[tuple[str, str], ...] = (
    ("user", "优丁唯一 UI + 唯一 /login"),
    ("dsh_optional", "外层 DSH① 认知/技能包（非每单必经）"),
    ("hermes", "内层爱马仕② 调度主权（L1 默认，进程内直驱执行器）"),
    ("executors_parallel", "并列能力域：本项目拓客⑤ · 本项目CRM⑥ · DeerFlow④ · Site③ · n8n⑧ · 资产⑦"),
    ("truth", "优丁 PG 真相 + 证据 + 经验反哺"),
)

ANNEX_EXECUTORS: FrozenSet[str] = frozenset({"trade_ai_agent", "goodjob_crm"})

# ── 黄金路径 ────────────────────────────────────────────
GOLDEN_PATH_A = {
    "id": "GP-A",
    "name": "履约 PI（本项目 CRM）",
    "priority": "P0",
    "plane": PLANE_TASK,
    "default_source": "L1_template",
    "intent_hints": ("履约", "订单", "跟单", "发货", "物流", "生产", "fulfillment", "pi", "形式发票"),
    "required_executors": ("inquiry", "order", "goodjob_crm", "billing"),
    "required_capabilities": (
        "inquiry.capture",
        "order.create",
        "document.generate_pi",
        "billing.meter",
    ),
    "acceptance": (
        "仅从优丁发起，Hermes 原生直驱（无外挂桥/无第二管理台）",
        "Hermes 任务中心可见节点/状态",
        "优丁 PG 有订单/单证行；收款账户未配置时单证 degraded，不编造银行号",
    ),
}

GOLDEN_PATH_B = {
    "id": "GP-B",
    "name": "拓客触达（本项目拓客）",
    "priority": "P1",
    "plane": PLANE_TASK,
    "default_source": "L1_template",
    "intent_hints": ("拓客", "社媒", "whatsapp", "私域", "社交媒体", "outreach", "prospect"),
    "required_executors": ("trade_ai_agent",),
    "required_capabilities": (
        "prospect.scrape",
        "outreach.whatsapp",
        "inbox.classify",
    ),
    "acceptance": (
        "仅从优丁发起，Hermes 原生直驱（无外挂管理台）",
        "无 WA Key/SMTP → 诚实 failed，禁止假 sent",
        "线索/触达记录回写优丁 PG（prospect_leads/inquiries/contact_events）",
    ),
}

GOLDEN_PATHS: tuple[dict[str, Any], ...] = (GOLDEN_PATH_A, GOLDEN_PATH_B)

# 常见交互动作（不应强制进任务平面）
INTERACTIVE_ACTION_HINTS: FrozenSet[str] = frozenset(
    {
        "list",
        "detail",
        "get",
        "search",
        "update_field",
        "read_conversation",
        "settings",
        "列表",
        "详情",
        "查询",
        "修改字段",
        "配置",
    }
)


def classify_plane(action_or_intent: str) -> str:
    """粗分双平面：交互 vs 任务（按钮/菜单接线用）。

    任务平面关键词命中则 task；否则含交互词则 interactive；
    默认：明确业务动词倾向 task，纯查询倾向 interactive。
    """
    raw = (action_or_intent or "").strip().lower()
    if not raw:
        return PLANE_INTERACTIVE
    task_hints: set[str] = set()
    for gp in GOLDEN_PATHS:
        task_hints.update(str(x).lower() for x in gp.get("intent_hints", ()))
    task_hints.update(
        {
            "履约",
            "pi",
            "形式发票",
            "拓客",
            "触达",
            "whatsapp",
            "发货",
            "生成单证",
            "find_customer",
            "fulfill",
        }
    )
    for h in task_hints:
        if h and h in raw:
            return PLANE_TASK
    for h in INTERACTIVE_ACTION_HINTS:
        if h and h in raw:
            return PLANE_INTERACTIVE
    return PLANE_INTERACTIVE


def preferred_decompose_source(intent_or_action: str) -> str:
    """任务平面默认走 L1；DSH 非必经（优化拍板）。"""
    if classify_plane(intent_or_action) != PLANE_TASK:
        return "n/a_interactive"
    return "L1_template"


def golden_path_for_executors(executors: Iterable[str]) -> dict[str, Any] | None:
    """若图中执行器覆盖某黄金路径的必需执行器，返回该路径定义。"""
    have = {str(e) for e in executors}
    for gp in GOLDEN_PATHS:
        need = set(gp["required_executors"])
        if need and need.issubset(have):
            return gp
    return None


def work_mode_report() -> dict[str, Any]:
    """供门禁/驾驶舱展示的契约快照。"""
    return {
        "planes": {
            PLANE_INTERACTIVE: list(INTERACTIVE_PLANE_RULES),
            PLANE_TASK: list(TASK_PLANE_RULES),
        },
        "layer_stack": [{"layer": a, "desc": b} for a, b in LAYER_STACK],
        "annex_executors": sorted(ANNEX_EXECUTORS),
        "dsh_required_every_task": False,
        "default_task_source": "L1_template",
        "golden_paths": [
            {
                "id": gp["id"],
                "name": gp["name"],
                "priority": gp["priority"],
                "executors": list(gp["required_executors"]),
            }
            for gp in GOLDEN_PATHS
        ],
        "system_lock_note": "SYSTEM-LOCK-02=能力域逻辑锁，不要求附属独立登录/管理台",
        "seamless_body": SEAMLESS_BODY,
    }


# ── 完整体 · 无隔阂（主理人铁律）────────────────────────
SEAMLESS_BODY: dict[str, Any] = {
    "principle": "GoodJob 与 TradeAI 是优丁完整体：不能突兀、不能有隔阂、无缝衔接驱动",
    "menu_principle": "功能域菜单（无特权）：与客户/订单等业务模块同级，走 UJ RBAC；禁附属特权/第二产品入口",
    "function_domains": [
        {"key": "trade-ai", "label": "社媒拓客", "menu_group": "获客转化", "privileged": False},
        {"key": "goodjob", "label": "外贸履约", "menu_group": "履约与账户", "privileged": False},
    ],
    "standards": [
        {"id": "S1", "name": "身份与壳", "rule": "唯一 UJ 登录与角色壳；禁 iframe 附属产品台"},
        {"id": "S2", "name": "导航信息架构", "rule": "菜单用业务功能域（社媒拓客/外贸履约），禁附属品牌墙与特权分组"},
        {"id": "S3", "name": "数据与搜索", "rule": "优丁 PG 唯一真相；全局搜索覆盖线索/订单/单证/任务"},
        {"id": "S4", "name": "任务与通知", "rule": "Hermes 任务/通知/证据在优丁任务中心可见"},
        {"id": "S5", "name": "交互语义", "rule": "响应/文案/空态/权限提示与优丁同构"},
        {"id": "S6", "name": "驱动闭环", "rule": "任务面按钮→Hermes L1→回写优丁页；可重试/人审"},
        {"id": "S7", "name": "菜单无特权", "rule": "GoodJob/TradeAI 功能域菜单与其它模块同级，无特权分组/无第二超管壳"},
    ],
    "anti_patterns": [
        "打开 GoodJob/TradeAI 独立域名或第二套登录完成业务",
        "菜单分组叫「附属执行台」或暗示特权/外挂",
        "进度与失败只出现在附属日志/附属页",
        "同一客户在附属库与优丁库重复建档且搜不到",
        "英文裸栈/另一套 UI 语言造成突兀感",
    ],
}


def seamless_gap_score(observed: dict[str, bool]) -> dict[str, Any]:
    """按 S1–S6 给完整体缺口分。observed: 标准 id → 是否达标。"""
    details = []
    passed = 0
    for std in SEAMLESS_BODY["standards"]:
        ok = bool(observed.get(std["id"]))
        passed += 1 if ok else 0
        details.append({"id": std["id"], "name": std["name"], "ok": ok, "rule": std["rule"]})
    total = len(SEAMLESS_BODY["standards"])
    return {
        "passed": passed,
        "total": total,
        "pct": round(passed / max(total, 1) * 100, 1),
        "seamless": passed == total,
        "details": details,
        "principle": SEAMLESS_BODY["principle"],
    }
