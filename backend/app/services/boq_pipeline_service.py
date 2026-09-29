# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""BOQ 管道服务 —— 修正设计稿 模块3 / Production Gate G6。

把既有 22 参数核价引擎（services/boq_calculator.py）补上完整前置管道：

    上传 → 抽取(extract) → 单位归一(normalize) → 产品匹配(match)
         → 人工复核(review) → 22 参数计算(calculate) → 核价单 → approve

语义红线（设计稿 3.4/3.5）：
- **禁止 extracted → quote 跳步**：calculate 前强制 normalize + match + 复核齐全；
- 置信度门控：≥0.85 auto_selected；0.60~0.85 review_required；<0.60 manual_required；
- 硬条件优先（材料不兼容/单位无法确认 → 直接 rejected）——LLM 只能解释，不能覆盖；
- 视觉抽取（moss_vl）未接时**诚实 not_configured**，不伪造抽取结果。

对外话术（模块 20）：用户视图只看到「上传 → AI 识别 → 需要确认 N 项 → 核价单」，
本服务输出 human_view() 专门生成该话术。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.boq_import import (
    JOB_STATUSES,
    LEGAL_JOB_TRANSITIONS,
    BoqImportJob,
    BoqLineItem,
)
from app.models.product import Product
from app.services.boq_calculator import BOQCalculator
from app.services.industry_profile_service import resolve_boq_overrides_for_tenant

logger = logging.getLogger(__name__)


class PipelineError(ValueError):
    """携带 HTTP 语义的管道错误（状态门控/输入校验）。"""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── 状态机 ───────────────────────────────────────────────────


def transition(job: BoqImportJob, to_status: str, *, error_code: Optional[str] = None) -> None:
    """严格状态跃迁（非法跃迁 = 管道跳步，一律拒绝）。"""
    from_status = job.status
    if to_status not in LEGAL_JOB_TRANSITIONS.get(from_status, ()):
        raise PipelineError(
            409,
            "illegal_job_transition",
            f"BOQ 作业 {job.id}: {from_status} → {to_status} 非法（阶段门控）",
        )
    job.status = to_status
    if to_status in ("calculated", "approved", "failed"):
        job.finished_at = _utcnow()
    if error_code:
        job.error_code = error_code


# ── 单位归一（纯函数） ───────────────────────────────────────

_UNIT_ALIASES: dict[str, str] = {}
for canonical, aliases in {
    "sqm": ("sqm", "m2", "㎡", "平米", "平方米", "平方", "sm", "sq.m", "sq m"),
    "cbm": ("cbm", "m3", "㎥", "立方", "立方米", "cubic"),
    "ton": ("ton", "t", "吨", "tons"),
    "pcs": ("pcs", "pc", "支", "只", "个", "件", "piece", "pieces"),
    "box": ("box", "箱", "boxes", "盒"),
    "sheet": ("sheet", "张", "片", "sheets"),
    "kg": ("kg", "千克", "公斤", "kgs"),
    "m": ("m", "米", "延米", "lm", "linear meter"),
    "set": ("set", "套", "sets", "组"),
}.items():
    for alias in aliases:
        _UNIT_ALIASES[alias.lower().replace(" ", "")] = canonical


def normalize_unit(raw: Optional[str]) -> Optional[str]:
    """单位归一：无法确认返回 None（设计稿 3.5 硬拒条件之一）。"""
    if not raw:
        return None
    key = str(raw).strip().lower().replace(" ", "").replace(".", "")
    return _UNIT_ALIASES.get(key)


def normalize_quantity(raw: Optional[str]) -> Optional[float]:
    """数量解析：容忍千分位/单位粘连；解析失败返回 None。"""
    if raw is None:
        return None
    s = str(raw).strip().replace(",", "").replace("，", "")
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:  # noqa: BLE001
        return None


# ── 材料硬冲突（纯函数；词表可被 Industry Profile 覆盖） ───────

# 默认建材材料词表（Industry Profile 未提供 material_tokens 时的兜底）
_MATERIAL_TOKENS: dict[str, tuple[str, ...]] = {
    "marble": ("marble", "大理石"),
    "granite": ("granite", "花岗岩", "花岗石"),
    "ceramic": ("ceramic", "瓷砖", "瓷片", "瓷质砖"),
    "porcelain": ("porcelain", "陶瓷"),
    "wood": ("wood", "木质", "木纹", "木"),
    "metal": ("metal", "金属", "钢", "铝", "steel", "aluminum"),
}

# 默认材料（Industry Profile 未提供 default_material 时的兜底）；原为 run_calculation 内字面量
_DEFAULT_MATERIAL: str = "ceramic"


def _material_vocabulary(
    overrides: Optional[dict] = None,
) -> tuple[dict[str, tuple[str, ...]], str]:
    """从 Industry Profile 覆盖包解析材料词表与默认材料。

    overrides['material_tokens'] → tokens（缺失/非法回落 _MATERIAL_TOKENS）；
    overrides['default_material'] → default（缺失/非法回落 _DEFAULT_MATERIAL）。
    """
    tokens: dict[str, tuple[str, ...]] = _MATERIAL_TOKENS
    default_material: str = _DEFAULT_MATERIAL
    if overrides:
        raw_tokens = overrides.get("material_tokens")
        if isinstance(raw_tokens, dict) and raw_tokens:
            normalized: dict[str, tuple[str, ...]] = {}
            for material, toks in raw_tokens.items():
                if isinstance(toks, (list, tuple)) and toks:
                    normalized[str(material)] = tuple(str(t) for t in toks)
            if normalized:
                tokens = normalized
        raw_default = overrides.get("default_material")
        if isinstance(raw_default, str) and raw_default:
            default_material = raw_default
    return tokens, default_material


def _material_of(
    text: str, tokens: Optional[dict[str, tuple[str, ...]]] = None
) -> Optional[str]:
    """从文本推断材料类型；tokens=None → 用 _MATERIAL_TOKENS（行为与今天一致）。"""
    table = tokens if tokens else _MATERIAL_TOKENS
    low = (text or "").lower()
    for material, toks in table.items():
        if any(tok in low for tok in toks):
            return material
    return None


def material_conflict(
    line_text: str,
    product_text: str,
    tokens: Optional[dict[str, tuple[str, ...]]] = None,
) -> Optional[str]:
    """硬规则：行项材料与产品材料明确冲突 → 返回拒绝原因（优先于任何置信度）。

    tokens 透传材料词表；None 时行为与今天一致。
    """
    lm = _material_of(line_text, tokens)
    pm = _material_of(product_text, tokens)
    if lm and pm and lm != pm:
        return f"material_incompatible: line={lm} product={pm}"
    return None


# ── 文本表格抽取（v1 诚实能力） ───────────────────────────────

_ROW_SPLIT = re.compile(r"\||\t|，,|;；")


def parse_text_table(text: str) -> list[dict[str, Any]]:
    """从粘贴的表格文本（管道符/Tab/分号分隔）抽取行项。

    容错：自动识别「描述 | 数量 | 单位」列序（含表头行则跳过）。
    解析不出的行跳过并在返回中带 raw 以便人工补录——不伪造抽取。
    """
    rows: list[dict[str, Any]] = []
    for idx, raw_line in enumerate((text or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line or set(line) <= {"|-+ "}:
            continue
        parts = [p.strip() for p in _ROW_SPLIT.split(line) if p.strip()]
        if len(parts) < 2:
            continue
        # 跳过表头
        joined = " ".join(parts[:3]).lower()
        if any(h in joined for h in ("description", "item", "描述", "品名")) and "qty" in joined or "数量" in joined:
            continue
        description = parts[0]
        qty_raw = parts[1] if len(parts) > 1 else ""
        unit_raw = parts[2] if len(parts) > 2 else ""
        qty = normalize_quantity(qty_raw)
        unit = normalize_unit(unit_raw)
        if not description or qty is None:
            continue  # 无法解析的行：跳过（不伪造）
        rows.append(
            {
                "source_row": idx,
                "raw_description": description,
                "raw_quantity": str(qty_raw),
                "raw_unit": str(unit_raw),
                "normalized_description": description,
                "normalized_quantity": qty,
                "normalized_unit": unit,  # None = 单位无法确认（匹配阶段硬拒）
            }
        )
    return rows


# ── 管道阶段 ─────────────────────────────────────────────────


def create_job(
    db: Session,
    *,
    tenant_id: str,
    source_name: Optional[str] = None,
    defaults: Optional[dict] = None,
    created_by: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> BoqImportJob:
    job = BoqImportJob(
        tenant_id=str(tenant_id),
        source_name=source_name,
        defaults_json=defaults or {},
        created_by=created_by,
        trace_id=trace_id,
        status="uploaded",
    )
    db.add(job)
    db.flush()
    return job


def add_manual_lines(
    db: Session,
    job: BoqImportJob,
    rows: list[dict[str, Any]],
    *,
    extractor: str = "manual",
) -> int:
    """uploaded → extracting → extracted：登记行项（manual/text_table 抽取结果）。"""
    if not rows:
        raise PipelineError(422, "no_extractable_rows", "未能从输入中解析出任何行项")
    transition(job, "extracting")
    job.extractor = extractor
    job.extractor_version = "v1"
    for i, r in enumerate(rows, start=1):
        db.add(
            BoqLineItem(
                boq_job_id=job.id,
                source_row=int(r.get("source_row") or i),
                raw_description=r.get("raw_description") or r.get("description"),
                raw_quantity=str(r.get("raw_quantity") or r.get("quantity") or ""),
                raw_unit=str(r.get("raw_unit") or r.get("unit") or ""),
                normalized_description=r.get("normalized_description") or r.get("raw_description") or r.get("description"),
                normalized_quantity=r.get("normalized_quantity"),
                normalized_unit=r.get("normalized_unit"),
            )
        )
    transition(job, "extracted")
    db.commit()
    return len(rows)


def run_normalization(db: Session, job: BoqImportJob) -> int:
    """extracted → normalizing → matching：行项单位/数量归一。"""
    transition(job, "normalizing")
    lines = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).all()
    for line in lines:
        if line.normalized_unit is None:
            line.normalized_unit = normalize_unit(line.raw_unit)
        if line.normalized_quantity is None:
            line.normalized_quantity = normalize_quantity(line.raw_quantity)
        if not line.normalized_description:
            line.normalized_description = line.raw_description
        db.add(line)
    transition(job, "matching")
    db.commit()
    return len(lines)


def _score_tokens(line_text: str, product: Product) -> float:
    """描述 vs 产品名/英文名 的匹配分（0~1，2 位小数）。

    强信号：产品名（≥4 字符）完整出现在行描述中 → 0.95（名称即规格的核心锚点）。
    一般信号：token 重叠率（以行项 token 为分母的召回率）。
    """
    lt = set(re.findall(r"[a-z0-9\u4e00-\u9fff]+", (line_text or "").lower()))
    line_low = (line_text or "").lower()
    best_name = 0.0
    for name in filter(None, [product.name, getattr(product, "name_en", None)]):
        n_low = name.lower().strip()
        if len(n_low) >= 4 and n_low in line_low:
            best_name = max(best_name, 0.95)
    if best_name:
        return best_name
    if not lt:
        return 0.0
    pt = set(
        re.findall(
            r"[a-z0-9\u4e00-\u9fff]+",
            " ".join(filter(None, [product.name, getattr(product, "name_en", None)])).lower(),
        )
    )
    if not pt:
        return 0.0
    return round(len(lt & pt) / len(lt), 2)


def run_matching(
    db: Session, job: BoqImportJob, *, industry_profile: Optional[dict] = None
) -> dict:
    """matching → review_required / calculating-ready（状态留在 matching 或 review_required）。

    硬条件优先：材料冲突 / 单位无法确认 → rejected；其余按置信度门控分流。
    industry_profile=None → resolve_boq_overrides_for_tenant(db, job.tenant_id)（§4.1）。
    用得到 material_tokens；material_conflict 透传 tokens。返回结构不变。
    """
    overrides = (
        industry_profile if industry_profile is not None
        else resolve_boq_overrides_for_tenant(db, job.tenant_id)
    )
    material_tokens, _ = _material_vocabulary(overrides)

    if job.status != "matching":
        transition(job, "matching")  # normalizing 结束后已处于 matching 则不重复跃迁
    lines = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).all()
    needs_human = 0
    rejected = 0
    for line in lines:
        if line.review_status == "rejected":
            continue
        line_text = f"{line.raw_description or ''} {line.normalized_description or ''}"
        unit = line.normalized_unit
        if unit is None:
            line.review_status = "rejected"
            line.reject_reason = "unit_unrecognized"
            line.match_confidence = 0.0
            db.add(line)
            rejected += 1
            continue

        candidates: list[dict[str, Any]] = []
        products = (
            db.query(Product)
            .filter(Product.tenant_id == job.tenant_id, Product.is_active.is_(True))
            .all()
        )
        scored: list[tuple[float, Product]] = []
        for product in products:
            conflict = material_conflict(
                line_text,
                f"{product.name} {getattr(product, 'name_en', None) or ''}",
                material_tokens,
            )
            if conflict:
                continue  # 硬冲突产品直接出局（不进候选）
            score = _score_tokens(line.normalized_description or line.raw_description or "", product)
            scored.append((score, product))
        scored.sort(key=lambda t: t[0], reverse=True)
        for score, product in scored[:3]:
            candidates.append({"product_id": str(product.id), "name": product.name, "score": score})

        line.candidate_products = candidates
        best_score, best_product = (scored[0] if scored else (0.0, None))

        # 硬拒复查：得分最高的候选与行材料冲突（候选阶段已过滤，此处兜底行自身无材料而产品无法判定的情况不做硬拒）
        if best_product is None:
            line.review_status = "manual_required"
            line.match_confidence = 0.0
            needs_human += 1
        elif best_score >= 0.85:
            line.review_status = "auto_selected"
            line.selected_product_id = str(best_product.id)
        elif best_score >= 0.60:
            line.review_status = "review_required"
            line.selected_product_id = str(best_product.id)  # 预选，等待人工确认
            needs_human += 1
        else:
            line.review_status = "manual_required"
            needs_human += 1
        line.match_confidence = best_score
        db.add(line)

    avg = (
        sum(float(l.match_confidence or 0) for l in lines) / len(lines) if lines else 0.0
    )
    job.confidence = round(avg, 2)
    if needs_human:
        transition(job, "review_required")
    else:
        job.status = "matching"  # 全部自动采用 → 可直接计算
    db.add(job)
    db.commit()
    return {"lines": len(lines), "needs_human": needs_human, "rejected": rejected,
            "confidence": job.confidence}


def confirm_line(db: Session, line: BoqLineItem, product_id: str) -> BoqLineItem:
    """人工确认行项（review_required / manual_required / auto_selected 改选）。"""
    if line.review_status not in ("review_required", "manual_required", "auto_selected"):
        raise PipelineError(409, "line_not_reviewable", f"行项当前状态 {line.review_status} 不可确认")
    line.selected_product_id = str(product_id)
    line.review_status = "confirmed"
    db.add(line)
    db.commit()
    return line


def reject_line(db: Session, line: BoqLineItem, reason: str) -> BoqLineItem:
    """人工拒绝行项（终态）。"""
    line.review_status = "rejected"
    line.reject_reason = (reason or "manual_reject")[:255]
    db.add(line)
    db.commit()
    return line


def run_calculation(
    db: Session,
    job: BoqImportJob,
    *,
    defaults: Optional[dict] = None,
    industry_profile: Optional[dict] = None,
) -> dict:
    """review_required/matching → calculating → calculated。任何行未复核齐 → 409。

    industry_profile=None → resolve_boq_overrides_for_tenant(db, job.tenant_id)（§4.1）。
    计算显式传入 calculator.calculate(params, industry_profile=overrides)；
    material_type 推断用 Profile 的 tokens/default。返回结构与 result_json 字段名不变。
    """
    overrides = (
        industry_profile if industry_profile is not None
        else resolve_boq_overrides_for_tenant(db, job.tenant_id)
    )
    material_tokens, default_material = _material_vocabulary(overrides)

    if job.status not in ("matching", "review_required"):
        raise PipelineError(409, "illegal_job_state", f"作业状态 {job.status} 不可计算")
    lines = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).all()
    if not lines:
        raise PipelineError(409, "no_lines", "作业没有可计算的行项")
    unreviewed = [
        l for l in lines if l.review_status not in ("auto_selected", "confirmed", "rejected")
    ]
    if unreviewed:
        raise PipelineError(
            409,
            "review_pending",
            f"需要确认 {len(unreviewed)} 项后才能生成核价单",
        )

    transition(job, "calculating")
    merged_defaults = dict(job.defaults_json or {})
    merged_defaults.update(defaults or {})
    calculator = BOQCalculator()
    line_results: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    grand_total = 0.0
    for line in lines:
        if line.review_status == "rejected":
            skipped.append({"item_id": str(line.id), "reason": line.reject_reason})
            continue
        product = (
            db.query(Product).filter(Product.id == str(line.selected_product_id)).first()
            if line.selected_product_id else None
        )
        params: dict[str, Any] = {
            **merged_defaults,
            "description": line.normalized_description or line.raw_description,
        }
        if product is not None:
            params["product_name"] = product.name
            if getattr(product, "specifications", None):
                specs = product.specifications if isinstance(product.specifications, dict) else {}
                params.setdefault("material_type", (specs.get("material") or "").lower() or None)
        # 行项材料推断（引擎参数化：从描述/产品名推断 material_type，词表随 Profile 变）
        if not params.get("material_type"):
            params["material_type"] = _material_of(line_text_of(line), material_tokens) or default_material
        if line.normalized_unit == "sqm" and line.normalized_quantity:
            params["quantity_sqm"] = line.normalized_quantity
        calc = calculator.calculate(params, industry_profile=overrides)
        if calc.get("error"):
            line_results.append({"item_id": str(line.id), "error": calc["error"], "params": params})
            continue
        total_val = float(calc.get("total", calc.get("grand_total", 0)) or 0)
        grand_total += total_val
        line_results.append(
            {"item_id": str(line.id), "params": params, "calc": calc, "total": total_val}
        )

    if not any("total" in lr for lr in line_results):
        transition(job, "failed", error_code="calculation_failed")
        db.add(job)
        db.commit()
        raise PipelineError(422, "calculation_failed", "所有行项计算失败，作业转 failed")

    job.result_json = {
        "lines": line_results,
        "skipped": skipped,
        "grand_total_usd": round(grand_total, 2),
        "calculated_at": _utcnow().isoformat(),
    }
    transition(job, "calculated")
    db.add(job)
    db.commit()
    return job.result_json


def line_text_of(line: BoqLineItem) -> str:
    return f"{line.raw_description or ''} {line.normalized_description or ''}"


def approve_job(db: Session, job: BoqImportJob, *, approver: Optional[str] = None) -> BoqImportJob:
    """calculated → approved（人工放行；记录审批人）。"""
    if job.status != "calculated":
        raise PipelineError(409, "illegal_job_state", "仅 calculated 状态可 approve")
    transition(job, "approved")
    job.created_by = job.created_by  # 审计人另记 result_json
    result = dict(job.result_json or {})
    result["approved_by"] = approver
    result["approved_at"] = _utcnow().isoformat()
    job.result_json = result
    db.add(job)
    db.commit()

    # ── 模块9/10 轨2：BOQ/标书处理按次计量（usage.boq_processing）──
    # 计费时点 = 审批通过（calculated→approved），**不是上传/创建时**
    # （与设计 10.3「不能提交即收费」同口径：处理完成才计费）。
    # meter_type 沿用既有 7 类 rfq_created（DB CheckConstraint 不动、历史事件不迁移），
    # meter_code 落七轨稳定词表 usage.boq_processing（设计 9.3，修复 meter_code 全 NULL）。
    try:
        from app.services.billing.meter_event import MeterEventService

        tenant_id = str(getattr(job, "tenant_id", "") or "").strip()
        if tenant_id:  # fail-closed：无租户不计量（与轨2 询盘同口径）
            MeterEventService(db).emit(
                meter_type="rfq_created",
                tenant_id=tenant_id,
                event_key=f"boq_job:{job.id}:processing",  # 幂等：同一 job 只计一次
                quantity=1,
                unit="job",
                source_ref_type="boq_job",
                source_ref_id=str(job.id),
                meter_code="usage.boq_processing",
                subject_type="boq_job",
                subject_id=str(job.id),
                bill_status="unlinked",
                metadata={
                    "meter_code": "usage.boq_processing",
                    "job_status": "approved",
                    "approver": approver,
                },
            )
        else:
            logger.warning(
                "boq_processing 未计量：tenant_id 为空 job_id=%s", job.id,
            )
    except Exception:  # noqa: BLE001 —— 计量失败绝不阻断 BOQ 审批主流程（漏收可补，审批回滚不可接受）
        logger.exception("boq_processing 计量写入失败 job_id=%s", job.id)

    return job


def human_view(job: BoqImportJob, lines: list[BoqLineItem]) -> dict:
    """面向普通卖家的视图（模块 20）：不暴露 extractor/confidence/trace_id。"""
    pending = sum(1 for l in lines if l.review_status in ("review_required", "manual_required"))
    return {
        "status_label": {
            "uploaded": "已上传",
            "extracting": "AI 正在识别",
            "extracted": "识别完成",
            "normalizing": "整理中",
            "matching": "正在匹配产品",
            "review_required": f"需要确认 {pending} 项",
            "calculating": "正在生成核价单",
            "calculated": "核价单已生成",
            "approved": "已确认",
            "failed": "处理失败，可重试",
        }.get(job.status, job.status),
        "line_count": len(lines),
        "pending_confirm": pending,
    }
