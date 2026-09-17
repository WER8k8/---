# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GW-L-DC-01 — 询盘 MEDDPICC 字段提取与评分。"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry

MEDDPICC_KEYS = (
    "metrics",
    "economic_buyer",
    "decision_criteria",
    "decision_process",
    "paper_process",
    "identify_pain",
    "champion",
    "competition",
)


def extract_meddpicc_from_text(text: str) -> dict[str, Any]:
    """规则提取 MEDDPICC 片段（无 LLM 依赖）。"""
    t = text or ""
    out: dict[str, Any] = {}
    if re.search(r"(预算|budget|price range|\$\d|USD|MOQ|数量|qty)", t, re.I):
        out["metrics"] = "检测到数量/预算/价格相关表述"
    if re.search(r"(CEO|采购经理|director|owner|decision maker|决策|老板|总经理)", t, re.I):
        out["economic_buyer"] = "可能涉及决策人角色"
    if re.search(r"(认证|ISO|CE|UL|FDA|标准|spec|规格)", t, re.I):
        out["decision_criteria"] = "出现规格/认证要求"
    if re.search(r"(流程|审批|样品|打样|PI|合同|付款|payment terms)", t, re.I):
        out["decision_process"] = "出现采购/付款流程信号"
    if re.search(r"(合同|PO|采购订单|invoice|信用证|L/C)", t, re.I):
        out["paper_process"] = "出现单据/合同流程"
    if re.search(r"(痛点|问题|替代|竞品|目前用|现有供应商|pain)", t, re.I):
        out["identify_pain"] = "出现痛点或竞品对比"
    if re.search(r"(推荐|内部|同事介绍|champion|推动)", t, re.I):
        out["champion"] = "可能出现内部推动者"
    if re.search(r"(竞品|竞争对手|alternative|vs\.|对比)", t, re.I):
        out["competition"] = "提及竞品或对比"

    filled = sum(1 for k in MEDDPICC_KEYS if out.get(k))
    score = min(100, filled * 12 + (10 if filled >= 4 else 0))
    level = "qualified" if filled >= 5 else "developing" if filled >= 3 else "early"
    return {
        **out,
        "fields_filled": filled,
        "score": score,
        "level": level,
        "next_questions": _missing_questions(out),
    }


def _missing_questions(data: dict[str, Any]) -> list[str]:
    """实现 missingquestions 的功能。
    
    :param data: 参数 data（类型: dict[str, Any]）
    :return: 返回 list[str] 结果
    """
    prompts = {
        "metrics": "请确认预计采购量、目标单价或年度 spend。",
        "economic_buyer": "谁拥有最终签字权？能否安排 economic buyer 通话？",
        "decision_criteria": "除价格外，认证/交期/售后的优先级？",
        "decision_process": "从 RFQ 到 PO 的典型步骤与周期？",
        "paper_process": "是否需要样品、验厂或正式合同模板？",
        "identify_pain": "当前供应商最大的痛点是什么？",
        "champion": "公司内部谁在推动这次更换/新供应商？",
        "competition": "正在对比哪些供应商或方案？",
    }
    return [prompts[k] for k in MEDDPICC_KEYS if not data.get(k)]


def load_meddpicc(inquiry: Inquiry) -> dict[str, Any]:
    """实现 加载meddpicc 的功能。
    
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :return: 返回 dict[str, Any] 结果
    """
    raw = getattr(inquiry, "meddpicc_json", None)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def save_meddpicc(db: Session, inquiry: Inquiry, payload: dict[str, Any]) -> dict[str, Any]:
    """实现 保存meddpicc 的功能。
    
    :param db: 参数 db（类型: Session）
    :param inquiry: 参数 inquiry（类型: Inquiry）
    :param payload: 参数 payload（类型: dict[str, Any]）
    :return: 返回 dict[str, Any] 结果
    """
    merged = {**load_meddpicc(inquiry), **{k: v for k, v in payload.items() if v is not None}}
    if "meddpicc_json" in {c.key for c in Inquiry.__table__.columns}:
        inquiry.meddpicc_json = json.dumps(merged, ensure_ascii=False)
        db.commit()
        db.refresh(inquiry)
    return merged


def score_inquiry_meddpicc(
    inquiry: Inquiry | dict[str, Any],
    *,
    auto_extract: bool = True,
) -> dict[str, Any]:
    """实现 评分inquirymeddpicc 的功能。
    
    :param inquiry: 参数 inquiry（类型: Inquiry | dict[str, Any]）
    :param auto_extract: 参数 auto_extract（类型: bool）
    :return: 返回 dict[str, Any] 结果
    """
    if isinstance(inquiry, Inquiry):
        stored = load_meddpicc(inquiry)
        message = inquiry.message or ""
        inquiry_id = str(inquiry.id)
        source_channel = inquiry.source_channel
    else:
        stored = inquiry.get("meddpicc") or {}
        message = inquiry.get("message") or ""
        inquiry_id = inquiry.get("id")
        source_channel = inquiry.get("source_channel")

    extracted = extract_meddpicc_from_text(message) if auto_extract else {}
    merged = {**extracted, **stored}
    filled = sum(1 for k in MEDDPICC_KEYS if merged.get(k))
    score = int(merged.get("score") or min(100, filled * 12 + (10 if filled >= 4 else 0)))
    level = merged.get("level") or (
        "qualified" if filled >= 5 else "developing" if filled >= 3 else "early"
    )
    return {
        "inquiry_id": inquiry_id,
        "source_channel": source_channel,
        "meddpicc": {k: merged.get(k) for k in MEDDPICC_KEYS},
        "fields_filled": filled,
        "score": score,
        "level": level,
        "next_questions": _missing_questions(merged),
        "gw_task": "GW-L-DC-01",
    }
