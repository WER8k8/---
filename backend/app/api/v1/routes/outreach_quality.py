"""开发信质量评估 + A/B 测试 + 获客流程 API 路由 — FIX-58 & FIX-59"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.services.ubrain.email_quality_service import (
    email_quality_evaluator,
    ab_test_engine,
    outreach_workflow_engine,
    OutreachStage,
)

router = APIRouter(prefix="/outreach-quality", tags=["获客·质量"])


# ── FIX-58: 邮件质量评估 ─────────────────────────────────

@router.post("/evaluate")
async def evaluate_email(
    subject: str,
    body: str,
    recipient_name: str = "",
    user=Depends(get_current_user),
):
    """评估开发信质量"""
    report = email_quality_evaluator.evaluate(
        subject=subject,
        body=body,
        recipient_name=recipient_name,
    )
    return {"code": 0, "data": report.to_dict()}


@router.post("/ab-test/create")
async def create_ab_test(
    test_id: str,
    variant_a_subject: str,
    variant_a_body: str,
    variant_b_subject: str,
    variant_b_body: str,
    test_variable: str = "",
    traffic_split: float = 0.5,
    min_sample_size: int = 100,
    user=Depends(get_current_user),
):
    """创建 A/B 测试"""
    config = ab_test_engine.create_test(
        test_id=test_id,
        variant_a_subject=variant_a_subject,
        variant_a_body=variant_a_body,
        variant_b_subject=variant_b_subject,
        variant_b_body=variant_b_body,
        test_variable=test_variable,
        traffic_split=traffic_split,
        min_sample_size=min_sample_size,
    )
    return {"code": 0, "data": config.to_dict()}


@router.post("/ab-test/analyze")
async def analyze_ab_test(
    test_id: str,
    a_sent: int,
    a_opens: int,
    a_replies: int,
    b_sent: int,
    b_opens: int,
    b_replies: int,
    user=Depends(get_current_user),
):
    """分析 A/B 测试结果"""
    result = ab_test_engine.analyze_results(
        test_id=test_id,
        a_sent=a_sent, a_opens=a_opens, a_replies=a_replies,
        b_sent=b_sent, b_opens=b_opens, b_replies=b_replies,
    )
    return {"code": 0, "data": result.to_dict()}


@router.post("/ab-test/generate-variants")
async def generate_variants(
    base_subject: str,
    base_body: str,
    variable: str = "subject_line",
    user=Depends(get_current_user),
):
    """生成 A/B 变体"""
    variants = ab_test_engine.generate_variants(
        base_subject=base_subject,
        base_body=base_body,
        variable=variable,
    )
    return {
        "code": 0,
        "data": {
            "variant_a": {"subject": variants["A"][0], "body": variants["A"][1]},
            "variant_b": {"subject": variants.get("B", ("", ""))[0], "body": variants.get("B", ("", ""))[1]},
        },
    }


# ── FIX-59: 获客流程标准化 ───────────────────────────────

@router.post("/workflow/create")
async def create_workflow(
    lead_id: str,
    lead_name: str = "",
    lead_company: str = "",
    user=Depends(get_current_user),
):
    """创建获客工作流"""
    workflow = outreach_workflow_engine.create_workflow(
        lead_id=lead_id,
        lead_name=lead_name,
        lead_company=lead_company,
    )
    return {"code": 0, "data": workflow.to_dict()}


@router.post("/workflow/advance")
async def advance_workflow_stage(
    lead_id: str,
    lead_name: str = "",
    lead_company: str = "",
    current_stage: str = "research",
    checklist_results: Optional[dict[str, bool]] = None,
    user=Depends(get_current_user),
):
    """推进工作流阶段"""
    try:
        stage = OutreachStage(current_stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效阶段: {current_stage}")

    from app.services.ubrain.email_quality_service import OutreachWorkflow
    workflow = OutreachWorkflow(
        lead_id=lead_id,
        lead_name=lead_name,
        lead_company=lead_company,
        current_stage=stage,
    )
    # 重建 gates
    workflow = outreach_workflow_engine.create_workflow(
        lead_id=lead_id, lead_name=lead_name, lead_company=lead_company,
    )
    workflow.current_stage = stage
    updated = outreach_workflow_engine.advance_stage(
        workflow=workflow,
        checklist_results=checklist_results,
    )
    return {"code": 0, "data": updated.to_dict()}


@router.post("/workflow/check-gate")
async def check_stage_gate(
    stage: str,
    user=Depends(get_current_user),
):
    """检查阶段门控"""
    try:
        s = OutreachStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效阶段: {stage}")

    # 获取检查清单
    checklists = outreach_workflow_engine.STAGE_CHECKLISTS.get(s, [])
    return {
        "code": 0,
        "data": {
            "stage": s.value,
            "checklist": [{"item": item["item"], "category": item["category"]} for item in checklists],
            "total_items": len(checklists),
        },
    }


@router.post("/workflow/audit")
async def audit_workflow(
    lead_id: str,
    current_stage: str = "research",
    user=Depends(get_current_user),
):
    """审计工作流合规性"""
    from app.services.ubrain.email_quality_service import OutreachWorkflow
    try:
        stage = OutreachStage(current_stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效阶段: {current_stage}")

    workflow = OutreachWorkflow(
        lead_id=lead_id,
        current_stage=stage,
    )
    result = outreach_workflow_engine.audit_workflow(workflow)
    return {"code": 0, "data": result}


@router.get("/workflow/best-practices")
async def get_best_practices(
    stage: str = "research",
    user=Depends(get_current_user),
):
    """获取阶段最佳实践"""
    try:
        s = OutreachStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效阶段: {stage}")

    practices = outreach_workflow_engine.get_best_practices(s)
    return {"code": 0, "data": {"stage": s.value, "practices": practices}}


@router.get("/workflow/stages")
async def list_stages(user=Depends(get_current_user)):
    """列出所有阶段信息"""
    stages = []
    for stage in OutreachStage:
        checklists = outreach_workflow_engine.STAGE_CHECKLISTS.get(stage, [])
        practices = outreach_workflow_engine.get_best_practices(stage)
        stages.append({
            "stage": stage.value,
            "checklist_count": len(checklists),
            "practices": practices,
            "checklist": [item["item"] for item in checklists],
        })

    return {"code": 0, "data": stages}
