"""线索处理 Pipeline + 评分 API — FIX-35/36

端点：
- POST /lead/pipeline/process      - 处理单条线索
- POST /lead/pipeline/process-batch - 批量处理线索
- POST /lead/score                  - 对线索评分
- POST /lead/score-batch            - 批量评分
"""

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response, error_response

router = APIRouter(prefix="/lead", tags=["获客引擎"])


# ============================================================
# Pipeline 处理
# ============================================================

@router.post("/pipeline/process")
async def process_lead(
    raw_data: dict,
    current_user=Depends(get_current_user),
):
    """通过 Pipeline 处理单条线索（标准化→去重→验证→评分→丰富→入库）。"""
    try:
        from app.services.ubrain.lead_processing_pipeline import LeadPipeline
        pipeline = LeadPipeline.create_default()
        ctx = await pipeline.process(raw_data)
        return success_response(data={
            "lead_id": ctx.id,
            "status": ctx.status.value,
            "score": ctx.score,
            "score_breakdown": ctx.score_breakdown,
            "is_duplicate": ctx.is_duplicate,
            "duplicate_of": ctx.duplicate_of,
            "errors": ctx.errors,
        })
    except Exception as e:
        return error_response(message=f"Pipeline 处理失败: {str(e)}", code=500)


@router.post("/pipeline/process-batch")
async def process_leads_batch(
    leads: list[dict],
    max_concurrent: int = Query(5, ge=1, le=20),
    current_user=Depends(get_current_user),
):
    """批量处理线索（带并发控制）。"""
    if len(leads) > 100:
        return error_response(message="单次最多处理100条线索", code=400)

    try:
        from app.services.ubrain.lead_processing_pipeline import LeadPipeline
        pipeline = LeadPipeline.create_default()
        results = await pipeline.process_batch(leads, max_concurrent=max_concurrent)
        summary = {
            "total": len(results),
            "completed": sum(1 for r in results if r.status.value == "completed"),
            "skipped": sum(1 for r in results if r.status.value == "skipped"),
            "failed": sum(1 for r in results if r.status.value == "failed"),
            "avg_score": round(
                sum(r.score for r in results if r.status.value == "completed") /
                max(1, sum(1 for r in results if r.status.value == "completed")),
                1,
            ),
        }
        return success_response(data={
            "summary": summary,
            "results": [
                {
                    "lead_id": r.id,
                    "status": r.status.value,
                    "score": r.score,
                    "email": r.normalized.get("email", ""),
                }
                for r in results
            ],
        })
    except Exception as e:
        return error_response(message=f"批量处理失败: {str(e)}", code=500)


# ============================================================
# 线索评分
# ============================================================

@router.post("/score")
async def score_lead(
    lead_data: dict,
    verification_result: dict | None = None,
    current_user=Depends(get_current_user),
):
    """对单条线索进行评分。"""
    try:
        from app.services.ubrain.lead_scoring_engine import score_lead as _score
        result = await _score(lead_data, verification_result)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=f"评分失败: {str(e)}", code=500)


@router.post("/score-batch")
async def score_leads_batch(
    leads: list[dict],
    current_user=Depends(get_current_user),
):
    """批量评分线索。"""
    if len(leads) > 200:
        return error_response(message="单次最多评分200条", code=400)

    try:
        from app.services.ubrain.lead_scoring_engine import score_lead as _score
        results = []
        for lead in leads:
            result = await _score(lead)
            result["email"] = lead.get("email", "")
            result["company"] = lead.get("company", "")
            results.append(result)

        # 排序：高分在前
        results.sort(key=lambda r: r["score"], reverse=True)
        # 统计
        grades = {"hot": 0, "warm": 0, "cool": 0, "cold": 0}
        for r in results:
            grades[r["grade"]] += 1

        return success_response(data={
            "total": len(results),
            "grades": grades,
            "avg_score": round(sum(r["score"] for r in results) / len(results), 1) if results else 0,
            "results": results,
        })
    except Exception as e:
        return error_response(message=f"批量评分失败: {str(e)}", code=500)