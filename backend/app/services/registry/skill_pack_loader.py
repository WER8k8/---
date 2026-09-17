# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""技能包扫描解析器 —— 把磁盘上的 SKILL.md 技能包变成编排可消费的索引。

背景（本文件存在的理由）：
    项目内有大量**真实技能资产**躺在磁盘上，但后端代码此前**从不读取**它们：
      - ``<worktree>/skills``           76 个业务技能（customer-research / ai-seo /
                                        cold-email / ads / programmatic-seo ...）
      - ``_external/ecc/skills``        286 个工程技能（backend-patterns ...）
    结果是 ``skills`` 表长期为 0 条，Hermes/DeerFlow 的"技能路由"无内容可路由，
    链路看着通、实际是空转。本模块负责把这部分资产解析成结构化索引，
    供 :func:`app.services.registry.skill_service.seed_skill_pack` 入库、
    供 :func:`match_skill_pack` 做意图 → 技能的自动匹配。

设计原则：
    - **零新增依赖**：优先用 PyYAML（若环境已装），否则回退到自带的最小
      frontmatter 解析器（只支持 ``key: value`` 与一级 ``metadata:`` 嵌套，
      足够覆盖 SKILL.md 的 frontmatter 形态）。
    - **失败可降级**：单个技能解析失败只跳过该文件并计数，不影响整体发现。
    - **来源可配置**：``SKILL_PACK_SOURCES`` 环境变量控制扫描哪些来源，
      默认只扫业务技能包（避免 286 个工程技能稀释外贸业务匹配质量）。

环境变量：
    SKILL_PACK_SOURCES  逗号分隔，可选值 business / ecc，默认 ``business``
    SKILL_PACK_DIRS     额外绝对路径（逗号分隔），优先级最高
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

log = logging.getLogger(__name__)

# backend/app/services/registry/skill_pack_loader.py
# parents: [0]=registry [1]=services [2]=app [3]=backend [4]=<worktree>
_WORKTREE_ROOT = Path(__file__).resolve().parents[4]

#: 来源名 → 目录（相对 worktree 根）
_SOURCE_DIRS: dict[str, str] = {
    "business": "skills",
    "ecc": "_external/ecc/skills",
}

#: 中文/业务意图 → 技能包 name 的别名，用于提高匹配命中率。
#: key 为场景/意图词（小写），value 为候选技能名（按顺序优先）。
INTENT_ALIASES: dict[str, list[str]] = {
    "buyer_research": ["customer-research", "prospecting", "lead-research-assistant"],
    "customer_research": ["customer-research", "prospecting"],
    "outreach_letter": ["cold-email", "emails", "sales-enablement"],
    "cold_email": ["cold-email", "emails"],
    "email_dispatch": ["emails", "cold-email", "internal-comms"],
    "email_send": ["emails", "cold-email", "internal-comms"],
    "keyword_research": ["programmatic-seo", "seo-audit", "content-research-writer"],
    "seo_publish": ["ai-seo", "seo-audit", "programmatic-seo", "schema"],
    "seo_metadata": ["ai-seo", "seo-audit", "schema"],
    "multi_channel_publish": ["social", "ads", "marketing-loops", "referrals"],
    "content_creation": ["copywriting", "content-research-writer", "content-strategy"],
    "page_creation": ["site-architecture", "cro", "copywriting"],
    "site_build": ["site-architecture", "ai-seo", "copywriting", "schema"],
    "建站": ["site-architecture", "ai-seo", "copywriting"],
    "独立站": ["site-architecture", "ai-seo", "copywriting"],
    "广告": ["ads", "ad-creative", "paywalls"],
    "社媒": ["social", "marketing-loops"],
    "定价": ["pricing", "offers", "paywalls"],
    "竞品": ["competitors", "competitor-profiling", "competitive-ads-extractor"],
}

#: 从 description 中抽取触发词的正则：优先取引号包裹的短语
_QUOTED = re.compile(r"[\"']([^\"']{2,60})[\"']")
#: 引号不足时，退化为按逗号/顿号切分
_SPLIT = re.compile(r"[,，、;；]")
#: 清理触发词首尾残留标点（如 "a/b test," → "a/b test"），否则入库的触发词永远匹配不上
_PUNCT = " \t\r\n.,;:!?()[]{}\"'`~*_-–—"


@dataclass
class SkillPackEntry:
    """一个被发现的技能包条目（纯数据，可入库、可匹配）。"""

    name: str
    description: str
    path: str
    source: str
    version: str = "0.0.0"
    display_name: str = ""
    category: str = ""
    triggers: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    body: str = ""
    parse_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name or self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "source": self.source,
            "path": self.path,
            "triggers": self.triggers,
            "keywords": self.keywords,
            "parse_ok": self.parse_ok,
        }


# ──────────────────────────────────────────────
# frontmatter 解析
# ──────────────────────────────────────────────
def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """把 SKILL.md 文本切成 (frontmatter dict, 正文)。

    只截取开头被 ``---`` 包裹的 YAML 块。解析优先用 PyYAML；不可用时回退
    到最小解析器（支持 ``key: value``、``metadata:`` 一级嵌套、``|>-`` 折叠
    在本项目的 SKILL.md 中未出现，故不处理）。
    """
    body = text
    fm: dict[str, Any] = {}
    if not text.startswith("---"):
        return fm, body
    parts = text.split("---", 2)
    if len(parts) < 3:
        return fm, body
    raw, body = parts[1], parts[2]

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(raw)
        if isinstance(loaded, dict):
            return loaded, body
    except Exception:  # noqa: BLE001  PyYAML 缺失或 YAML 不合法 → 回落
        pass

    # 最小解析器：key: value + metadata 一级嵌套
    cur: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and cur:
            kv = line.strip().split(":", 1)
            if len(kv) == 2:
                fm.setdefault(cur, {})[kv[0].strip()] = kv[1].strip().strip("\"'")
            continue
        kv = line.split(":", 1)
        if len(kv) == 2:
            key = kv[0].strip()
            val = kv[1].strip().strip("\"'")
            if val == "":
                cur = key
                fm[key] = {}
            else:
                cur = None
                fm[key] = val
    return fm, body


def _extract_triggers(description: str, name: str) -> tuple[list[str], list[str]]:
    """从 description 抽取触发词与关键词。

    SKILL.md 的 description 里通常塞满了 ``"customer research"``、``"ICP research"``
    这类触发短语，这正是官方设计时留给"自动判断何时调用"的信号，必须利用起来。
    """
    def _clean(s: str) -> str:
        return s.strip().strip(_PUNCT).strip().lower()

    triggers: list[str] = []
    for m in _QUOTED.findall(description or ""):
        t = _clean(m)
        if t and t not in triggers:
            triggers.append(t)
    # 引号不足 → 按分隔符退化切分，取短片段
    if len(triggers) < 3:
        for seg in _SPLIT.split(description or ""):
            t = _clean(seg)
            if 2 <= len(t) <= 40 and t not in triggers:
                triggers.append(t)
    keywords: list[str] = [name.lower()]
    keywords.extend(name.replace("-", " ").split())
    for t in triggers[:40]:  # 控制规模，避免入库字段过大
        for w in re.split(r"[\s/]+", t):
            w = w.strip(_PUNCT)
            if len(w) >= 3 and w not in keywords:
                keywords.append(w)
    return triggers[:60], keywords[:60]


def _infer_category(name: str, source: str) -> str:
    """按技能名推断业务分类，供注册表分组与前端筛选。"""
    n = name.lower()
    mapping = [
        (("seo", "aso", "schema", "programmatic"), "seo"),
        (("ads", "ad-creative", "paywalls", "pricing", "offers"), "growth"),
        (("email", "cold-email", "outreach", "sms"), "outreach"),
        (("customer", "prospect", "lead", "research"), "research"),
        (("copy", "content", "writing", "brand"), "content"),
        (("social", "community", "referral", "co-marketing"), "social"),
        (("analytics", "ab-testing", "cro", "revops"), "analytics"),
        (("site", "webapp", "architecture"), "site"),
    ]
    for keys, cat in mapping:
        if any(k in n for k in keys):
            return cat
    return source if source != "business" else "general"


# ──────────────────────────────────────────────
# 发现
# ──────────────────────────────────────────────
def resolve_skill_pack_dirs() -> list[tuple[str, Path]]:
    """解析要扫描的技能包目录：[(source_name, dir), ...]。

    优先级：``SKILL_PACK_DIRS``（绝对路径，source 记为 ``custom``）
    > ``SKILL_PACK_SOURCES``（business / ecc）。
    """
    custom = (os.environ.get("SKILL_PACK_DIRS") or "").strip()
    if custom:
        out: list[tuple[str, Path]] = []
        for p in custom.split(","):
            p = p.strip()
            if p and Path(p).is_dir():
                out.append(("custom", Path(p)))
        if out:
            return out

    sources = (os.environ.get("SKILL_PACK_SOURCES") or "business").strip().lower()
    picked = [s.strip() for s in sources.split(",") if s.strip()] or ["business"]
    dirs: list[tuple[str, Path]] = []
    for s in picked:
        rel = _SOURCE_DIRS.get(s)
        if not rel:
            continue
        d = _WORKTREE_ROOT / rel
        if d.is_dir():
            dirs.append((s, d))
        else:
            log.debug("技能包来源 %s 目录不存在: %s", s, d)
    return dirs


def discover_skill_packs(
    dirs: Iterable[tuple[str, Path]] | None = None,
) -> list[SkillPackEntry]:
    """扫描技能包目录，返回解析后的条目列表（按 name 排序）。

    单个文件解析失败不会中断整体发现，仅记 debug 日志并在条目中标记
    ``parse_ok=False``（若连 name 都取不到则跳过）。
    """
    targets = list(dirs) if dirs is not None else resolve_skill_pack_dirs()
    entries: list[SkillPackEntry] = []
    seen: set[str] = set()

    for source, base in targets:
        for md in sorted(base.glob("*/SKILL.md")):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                log.debug("技能包读取失败 %s: %s", md, exc)
                continue
            fm, body = _parse_frontmatter(text)
            name = str(fm.get("name") or md.parent.name).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            meta = fm.get("metadata") or {}
            version = str(meta.get("version", "0.0.0") if isinstance(meta, dict) else "0.0.0")
            desc = str(fm.get("description") or "").strip()
            trig, kw = _extract_triggers(desc, name)
            entries.append(
                SkillPackEntry(
                    name=name,
                    description=desc,
                    path=str(md),
                    source=source,
                    version=version,
                    display_name=name,
                    category=_infer_category(name, source),
                    triggers=trig,
                    keywords=kw,
                    body=body.strip(),
                    parse_ok=bool(desc),
                )
            )
    entries.sort(key=lambda e: e.name)
    return entries


def load_skill_body(name: str, dirs: Iterable[tuple[str, Path]] | None = None) -> str:
    """按技能名取回 SKILL.md 正文（SOP 内容），供 LLM 执行时注入。"""
    for e in discover_skill_packs(dirs):
        if e.name == name:
            return e.body
    return ""


# ──────────────────────────────────────────────
# 意图 → 技能 自动匹配
# ──────────────────────────────────────────────
def score_skill(entry: Any, query: str) -> int:
    """给「查询意图」与「技能」的相关度打分（越高越相关）。

    入参采用 **duck typing**：同时接受 :class:`SkillPackEntry` 与 ORM 对象
    ``RegistrySkill``（两者都具备 name/description/triggers/keywords）。
    ORM 字段可能为 None，故统一做空值兜底。

    打分维度：
      - 别名表直接命中（INTENT_ALIASES）      +100 / 位次递减
      - name 相等 / 包含                      +80 / +45
      - 触发词完全相等 / 包含                  +30 / +12
      - description 命中                      +8
    关键词（keywords）命中给较低分，避免单词噪声主导结果。
    """
    q = (query or "").strip().lower()
    if not q:
        return 0
    score = 0

    # 别名表按**位次递减**给分（第 0 位 100，其后 75/55/40/30...）。
    # 若所有候选同分，排序会退化成字母序，别名表表达的优先级就失效了
    # （曾出现 site_build 选出 ai-seo 而非 site-architecture 的问题）。
    for idx, alias_skill in enumerate(INTENT_ALIASES.get(q, [])):
        base = 100 if idx == 0 else max(30, 75 - (idx - 1) * 20)
        if alias_skill == entry.name:
            score += base
        elif alias_skill in entry.name or entry.name in alias_skill:
            score += base // 2

    n = (entry.name or "").lower()
    if q == n:
        score += 80
    elif q and (q in n or n in q):
        score += 45

    for t in entry.triggers or []:
        t = str(t).lower()
        if q == t:
            score += 30
        elif q and (q in t or t in q):
            score += 12

    if q and q in (entry.description or "").lower():
        score += 8

    for k in entry.keywords or []:
        if q == str(k).lower():
            score += 6
    return score


def match_skill_pack(
    query: str,
    entries: Iterable[SkillPackEntry] | None = None,
    top_k: int = 3,
) -> list[tuple[SkillPackEntry, int]]:
    """按意图自动匹配技能包，返回 [(entry, score), ...]（按分数降序，已过滤 0 分）。

    这是「自动智能判断调用哪个 skill」的核心：调用方只需给出意图字符串
    （如 ``buyer_research`` / ``ai_site_build`` / ``建站``），即可拿到最相关技能。
    """
    pool = list(entries) if entries is not None else discover_skill_packs()
    scored = [(e, score_skill(e, query)) for e in pool]
    scored = [(e, s) for e, s in scored if s > 0]
    scored.sort(key=lambda x: (-x[1], x[0].name))
    return scored[:top_k]
