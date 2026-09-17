# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes ECC 专家人格评审 — 对齐 docs/技术栈-智能体-MCP-调度表，只读测试、不装依赖。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_ecc_expert_panel")

SECURITY_PATTERNS = (r"cve-\d", r"security", r"vulnerability", r"漏洞", r"rce", r"xss")
BREAKING_PATTERNS = (r"breaking", r"deprecated", r"remove[ds]?", r"major", r"v\d+\.0\.0")


@dataclass(frozen=True)
class EccExpert:
    agent_id: str
    display_name: str
    ecc_gate: str
    categories: frozenset[str]


# 与 ECC 调度表一致的主责 + 门控
EXPERT_ROSTER: tuple[EccExpert, ...] = (
    EccExpert("frontend-architect", "前端架构师", "typescript-reviewer", frozenset({"frontend"})),
    EccExpert("insulation-backend-developer", "后端开发专家", "code-reviewer", frozenset({"backend"})),
    EccExpert("fullstack-developer", "全栈开发", "typescript-reviewer", frozenset({"performance", "unknown"})),
    EccExpert(
        "insulation-material-product-manager",
        "产品/GEO",
        "doc-updater",
        frozenset({"structured_data", "paper", "geo_rank"}),
    ),
    EccExpert("geo-rank-strategist", "GEO排名攻坚", "doc-updater", frozenset({"geo_rank", "paper"})),
    EccExpert("insulation-backend-security-expert", "后端安全专家", "security-reviewer", frozenset({"*"})),
    EccExpert("testing-reality-checker", "QA 现实检验", "e2e-runner", frozenset({"*"})),
    EccExpert("insulation-devops-engineer", "DevOps", "cloudflare", frozenset({"backend", "performance"})),
)


def _ecc_review_enabled() -> bool:
    """_ecc_review_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "HERMES_ECC_EXPERT_REVIEW_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return (settings.ENVIRONMENT or "").strip().lower() == "production"


def _llm_review_enabled() -> bool:
    """_llm_review_enabled。
    :return: 返回处理结果。
    """
    flag = getattr(settings, "HERMES_ECC_LLM_REVIEW_ENABLED", None)
    if flag is not None:
        return bool(flag)
    return True


def _pick_experts(category: str, title: str, body: str) -> list[EccExpert]:
    """_pick_experts。

    参数说明：
    :param category: 参数 category
    :param title: 参数 title
    :param body: 参数 body
    :return: 返回处理结果。
    """
    text = f"{title} {body}".lower()
    picked: list[EccExpert] = []
    for expert in EXPERT_ROSTER:
        if "*" in expert.categories or category in expert.categories:
            picked.append(expert)
    if any(re.search(p, text, re.I) for p in SECURITY_PATTERNS):
        sec = next(e for e in EXPERT_ROSTER if e.agent_id == "insulation-backend-security-expert")
        if sec not in picked:
            picked.insert(0, sec)
    # 去重保序
    seen: set[str] = set()
    out: list[EccExpert] = []
    for e in picked:
        if e.agent_id not in seen:
            seen.add(e.agent_id)
            out.append(e)
    return out[:4]


def _verdict_rank(v: str) -> int:
    """_verdict_rank。

    参数说明：
    :param v: 参数 v
    :return: 返回处理结果。
    """
    return {"pass": 0, "skip": 1, "warn": 2, "fail": 3}.get(v, 1)


def _merge_verdict(current: str, new: str) -> str:
    """_merge_verdict。

    参数说明：
    :param current: 参数 current
    :param new: 参数 new
    :return: 返回处理结果。
    """
    return new if _verdict_rank(new) > _verdict_rank(current) else current


def _rule_review(expert: EccExpert, candidate: dict[str, Any]) -> dict[str, Any]:
    """_rule_review。

    参数说明：
    :param expert: 参数 expert
    :param candidate: 参数 candidate
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    title = (candidate.get("title") or "").strip()
    body = (candidate.get("body_preview") or "")[:500]
    text = f"{title} {body}".lower()
    impact = candidate.get("impact") or "low"
    checks: list[str] = []
    verdict = "pass"
    if expert.agent_id == "insulation-backend-security-expert":
        if any(re.search(p, text, re.I) for p in SECURITY_PATTERNS):
            verdict = "fail"
            checks.append("命中安全/CVE 关键词，禁止 Hermes 自动升级")
        else:
            checks.append("未发现明显安全告警词")

    elif expert.agent_id == "frontend-architect":
        if any(re.search(p, text, re.I) for p in BREAKING_PATTERNS):
            verdict = "warn"
            checks.append("前端 Breaking/主版本信号 — 需 admin + pages 回归")
        if "vue" in text or "nuxt" in text or "vite" in text:
            checks.append("栈匹配：Vue/Nuxt/Vite 生态")
        else:
            checks.append("非前端栈主更新，低优先级")

    elif expert.agent_id == "insulation-backend-developer":
        if "fastapi" in text or "github:fastapi" in (candidate.get("source") or "").lower():
            checks.append("栈匹配：FastAPI 后端")
            if any(re.search(p, text, re.I) for p in BREAKING_PATTERNS):
                verdict = "warn"
                checks.append("后端主版本/Breaking — 需 pytest + 隔离环境")
        else:
            checks.append("非后端主栈更新")

    elif expert.agent_id == "testing-reality-checker":
        if impact == "high":
            verdict = _merge_verdict(verdict, "warn")
            checks.append("高影响项 — 需 cert:gate / 关键 pytest 回归后再合并")
        checks.append("Hermes 仅做只读探测，不替代 E2E")

    elif expert.agent_id == "insulation-devops-engineer":
        if impact in ("high", "medium"):
            checks.append("部署相关变更须走 staging → 生产，禁止热更依赖")
        else:
            checks.append("运维面影响低，可归档观察")

    elif expert.agent_id == "fullstack-developer":
        if "web.dev" in text or "vitals" in text or "lcp" in text:
            checks.append("性能/CWV 信号 — 需 Lighthouse 或 web-perf 抽检")
        else:
            checks.append("全栈只读评审通过")

    elif expert.agent_id == "insulation-material-product-manager":
        if "schema" in text or "json-ld" in text:
            verdict = _merge_verdict(verdict, "warn")
            checks.append("结构化数据变更 — 需 SEO/GEO 模板回归")
        else:
            checks.append("内容/GEO 面影响有限")

    if candidate.get("validation_status") == "fail":
        verdict = _merge_verdict(verdict, "fail")
        checks.append("链接探测失败，专家测试中止自动采纳")

    recommendation = {
        "pass": "观察即可，写入技术雷达快照",
        "warn": "隔离分支评估 + 人工确认后再合入",
        "fail": "立即飞书/微信通知创始人，等待指令",
        "skip": "跳过",
    }.get(verdict, "人工评审")
    return {
        "agent_id": expert.agent_id,
        "display_name": expert.display_name,
        "ecc_gate": expert.ecc_gate,
        "verdict": verdict,
        "checks": checks,
        "recommendation": recommendation,
        "mode": "rule",
    }


def _build_llm_prompt(expert: EccExpert, candidate: dict[str, Any]) -> str:
    """_build_llm_prompt。

    参数说明：
    :param expert: 参数 expert
    :param candidate: 参数 candidate
    :return: 返回处理结果。
    """
    return (
        f"你是 ECC 专家「{expert.display_name}」（agent_id={expert.agent_id}，"
        f"门控={expert.ecc_gate}）。\n"
        "Hermes 7×24 运维：你只能做只读评审，禁止建议直接升级生产依赖或删数据。\n\n"
        f"技术候选：\n"
        f"- 标题: {candidate.get('title')}\n"
        f"- URL: {candidate.get('url')}\n"
        f"- 分类: {candidate.get('category')}\n"
        f"- 影响: {candidate.get('impact')}\n"
        f"- 摘要: {(candidate.get('body_preview') or '')[:300]}\n\n"
        "请输出单行 JSON："
        '{"verdict":"pass|warn|fail","summary":"一句话","test_plan":"隔离测试步骤≤80字"}'
    )


def _parse_llm_verdict(content: str) -> dict[str, Any]:
    """_parse_llm_verdict。

    参数说明：
    :param content: 参数 content
    :return: 返回处理结果。
    """
    text = (content or "").strip()
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {"verdict": "warn", "summary": text[:160], "test_plan": "人工复核 LLM 输出"}
    try:
        data = json.loads(match.group(0))
        v = str(data.get("verdict") or "warn").lower()
        if v not in ("pass", "warn", "fail", "skip"):
            v = "warn"
        return {
            "verdict": v,
            "summary": str(data.get("summary") or "")[:200],
            "test_plan": str(data.get("test_plan") or "")[:120],
        }
    except (json.JSONDecodeError, TypeError):
        return {"verdict": "warn", "summary": text[:160], "test_plan": "解析失败，人工复核"}


def _llm_review(db: Session | None, expert: EccExpert, candidate: dict[str, Any]) -> dict[str, Any] | None:
    """_llm_review。

    参数说明：
    :param db: 参数 db
    :param expert: 参数 expert
    :param candidate: 参数 candidate
    :return: 返回处理结果。
    """
    if not _llm_review_enabled():
        return None
    try:
        from app.services.ai_key_probe import ai_key_status
        if db is not None and not ai_key_status(db).get("has_real_key"):
            return None
    except Exception:
        return None

    try:
        from app.services.ai_invocation_service import invoke_llm
        prompt = _build_llm_prompt(expert, candidate)
        result = asyncio.run(
            invoke_llm(
                db,
                prompt=prompt,
                scenario="hermes_tech_radar",
                max_tokens=400,
                task_type="hermes_ecc_expert_review",
                enable_fallback=True,
                lane="ops",
            )
        )
        parsed = _parse_llm_verdict(result.get("content") or "")
        return {
            "agent_id": expert.agent_id,
            "display_name": expert.display_name,
            "ecc_gate": expert.ecc_gate,
            "verdict": parsed["verdict"],
            "checks": [parsed.get("summary") or "", f"测试计划: {parsed.get('test_plan') or ''}"],
            "recommendation": parsed.get("test_plan") or "见 LLM 摘要",
            "mode": "llm",
            "model_name": result.get("model_name"),
        }
    except Exception as exc:
        logger.info("ECC LLM review skipped: %s", exc)
        return None


def review_candidate(
    db: Session | None,
    candidate: dict[str, Any],
    *,
    allow_llm: bool = True,
) -> dict[str, Any]:
    """单候选：规则专家 + 可选 LLM（仅 high）。"""
    if not _ecc_review_enabled():
        return {**candidate, "expert_reviews": [], "expert_verdict": "skip"}

    category = candidate.get("category") or "unknown"
    title = candidate.get("title") or ""
    body = candidate.get("body_preview") or ""
    experts = _pick_experts(category, title, body)
    reviews: list[dict[str, Any]] = []
    verdict = "pass"
    for expert in experts:
        row = _rule_review(expert, candidate)
        reviews.append(row)
        verdict = _merge_verdict(verdict, row["verdict"])

    primary = experts[0] if experts else EXPERT_ROSTER[4]
    if (
        allow_llm
        and candidate.get("impact") == "high"
        and candidate.get("validation_status") == "pass"
    ):
        llm_row = _llm_review(db, primary, candidate)
        if llm_row:
            reviews.append(llm_row)
            verdict = _merge_verdict(verdict, llm_row["verdict"])

    row = {**candidate, "expert_reviews": reviews, "expert_verdict": verdict}
    if verdict == "fail":
        row["hermes_action"] = "notify_human_review"
        row["impact"] = "high"
    elif verdict == "warn" and row.get("impact") == "low":
        row["impact"] = "medium"
    return row


def review_all(db: Session | None, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """review_all。

    参数说明：
    :param db: 参数 db
    :param candidates: 参数 candidates
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    max_llm = int(getattr(settings, "HERMES_ECC_LLM_REVIEW_MAX_CANDIDATES", 3) or 3)
    llm_used = 0
    out: list[dict[str, Any]] = []
    for c in candidates:
        allow_llm = c.get("impact") == "high" and llm_used < max_llm
        row = review_candidate(db, c, allow_llm=allow_llm)
        if allow_llm and row.get("impact") == "high":
            llm_used += 1
        out.append(row)
    return out


def panel_meta() -> dict[str, Any]:
    """panel_meta。
    :return: 返回处理结果。
    """
    return {
        "roster_count": len(EXPERT_ROSTER),
        "experts": [
            {
                "agent_id": e.agent_id,
                "display_name": e.display_name,
                "ecc_gate": e.ecc_gate,
                "categories": sorted(e.categories),
            }
            for e in EXPERT_ROSTER
        ],
        "ecc_review_enabled": _ecc_review_enabled(),
        "llm_review_enabled": _llm_review_enabled(),
    }
