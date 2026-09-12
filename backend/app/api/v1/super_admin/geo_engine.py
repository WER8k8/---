"""GEO 引擎 API — 各大模型关键词收录查询"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.admin_auth import get_current_super_admin
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.geo_engine_service import GEOEngine
logger = logging.getLogger(__name__)

router = APIRouter()


class CheckRequest(BaseModel):
    keyword: str
    models: Optional[List[str]] = None
    context: str = ""
    probe_mode: str = "brand"  # brand | recommend
    brand_name: str = ""
    product_category: str = ""
    region: str = ""


@router.post("/recommend-probe")
async def recommend_probe(
    body: CheckRequest,
    user: User = Depends(get_current_super_admin),
):
    """采购意图探测 — 品牌是否进入大模型推荐前三。"""
    result = await GEOEngine.check_keyword(
        keyword=body.keyword,
        models=body.models,
        context=body.context,
        probe_mode="recommend",
        brand_name=body.brand_name or body.keyword,
        product_category=body.product_category or body.keyword,
        region=body.region,
    )
    return success_response(data=result)


class BatchCheckRequest(BaseModel):
    keywords: List[str]
    models: Optional[List[str]] = None


@router.get("/models")
def list_models(user: User = Depends(get_current_super_admin)):
    """列出支持的各大模型"""
    try:
        return success_response(data=GEOEngine.MODELS)
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@router.post("/check")
async def check_keyword(
    body: CheckRequest,
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """查询关键词在各大模型中的收录状态"""
    result = await GEOEngine.check_keyword(
        keyword=body.keyword,
        models=body.models,
        context=body.context,
        probe_mode=body.probe_mode if body.probe_mode in GEOEngine.PROBE_MODES else "brand",
        brand_name=body.brand_name,
        product_category=body.product_category,
        region=body.region,
        db=db,
    )
    return success_response(data=result)


@router.post("/batch-check")
async def batch_check(
    body: BatchCheckRequest,
    user: User = Depends(get_current_super_admin),
):
    """批量检查多个关键词"""
    result = await GEOEngine.batch_check(body.keywords)
    return success_response(data=result)


@router.post("/score")
async def geo_score(
    keyword: str = Query(...),
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """GEO 综合评分"""
    result = await GEOEngine.check_keyword(keyword, db=db)
    summary = result["summary"]
    not_configured = summary.get("errors", 0)
    # 评分模型（监测维度，非 GEO 优化完成度）
    inclusion_score = summary["indexed_rate"] * 0.5
    confidence_score = summary["avg_confidence"] * 0.3
    stability_bonus = 10 if summary["indexed"] >= 3 else 0
    total = round(inclusion_score + confidence_score + stability_bonus, 1)
    grade = "A" if total >= 80 else ("B" if total >= 60 else ("C" if total >= 40 else "D"))
    suggestions: list[str] = []
    if not_configured > 0:
        suggestions.append(
            f"【监测】尚有 {not_configured} 个模型未接通 API Key，无法探测；"
            "在 AI配置 接通后可查，这不等于 GEO 优化未完成。"
        )
    if summary["not_indexed"] > 0:
        suggestions.append(
            "【GEO】部分通道已接通但 AI 未提及品牌：建议完善官网产品页、案例与行业平台品牌描述。"
        )
    if summary["avg_confidence"] < 70 and summary["indexed"] > 0:
        suggestions.append(
            "【GEO】模型有提及但置信度偏低：补充参数表、资质与权威引用，提升可被 AI 摘要的质量。"
        )
    if not suggestions:
        suggestions.append("【监测】各通道探测正常；可持续迭代内容与外链以巩固提及率。")

    return success_response(data={
        "keyword": keyword,
        "total_score": min(total, 100),
        "grade": grade,
        "score_note": "本分数反映「各 AI 是否提及品牌」的监测结果，不等于 GEO 优化完成度。",
        "dimensions": {
            "inclusion_rate": {"score": round(inclusion_score, 1), "max": 50, "label": "模型提及率（监测）"},
            "confidence": {"score": round(confidence_score, 1), "max": 30, "label": "提及置信度（监测）"},
            "stability": {"score": stability_bonus, "max": 20, "label": "多通道监测覆盖"},
        },
        "suggestions": suggestions,
    })


@router.post("/competitor")
async def competitor_compare(
    keywords: List[str] = Query(...),
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """竞品 GEO 对比"""
    results = []
    for kw in keywords[:5]:
        r = await GEOEngine.check_keyword(kw, db=db)
        results.append({
            "keyword": kw,
            "score": r["summary"]["indexed_rate"],
            "indexed": r["summary"]["indexed"],
            "total": r["summary"]["total_models"],
            "best_model": r["summary"]["best_model"],
        })
    return success_response(data=results)


@router.get("/trend")
def geo_trend(
    keyword: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    user: User = Depends(get_current_super_admin),
):
    """收录率趋势：仅返回已归档的真实历史，无历史则空列表（禁止随机示意）。"""
    history = GEOEngine.get_history(keyword, days=days)
    if not history:
        return success_response(data=[])
    trend = []
    for row in history[-days:]:
        if not isinstance(row, dict):
            continue
        rate = row.get("indexed_rate")
        if rate is None:
            continue
        trend.append(
            {
                "date": row.get("date") or row.get("day") or "",
                "rate": float(rate),
            }
        )
    return success_response(data=trend)


@router.get("/quick-links")
def quick_links(user: User = Depends(get_current_super_admin)):
    """各大模型搜索直达链接"""
    return success_response(data=[
        {"name": "DeepSeek", "url": "https://chat.deepseek.com/", "icon": "🔍"},
        {"name": "豆包", "url": "https://www.doubao.com/chat/search", "icon": "🫘"},
        {"name": "元宝", "url": "https://yuanbao.tencent.com/chat/naQivTmsDa", "icon": "💎"},
        {"name": "通义千问", "url": "https://www.tongyi.com/", "icon": "☁️"},
        {"name": "文心一言", "url": "https://yiyan.baidu.com/", "icon": "📝"},
        {"name": "Kimi", "url": "https://kimi.moonshot.cn/", "icon": "🌙"},
        {"name": "ChatGPT", "url": "https://chat.openai.com/", "icon": "🧠"},
        {"name": "Gemini", "url": "https://gemini.google.com/", "icon": "🌐"},
    ])


@router.get("/history")
def get_history(
    keyword: str = Query(...),
    days: int = Query(7, ge=1, le=30),
    user: User = Depends(get_current_super_admin),
):
    """获取关键词历史查询记录"""
    history = GEOEngine.get_history(keyword, days=days)
    return success_response(data=history)


@router.get("/quick-check")
async def quick_check(
    keyword: str = Query(..., min_length=1),
    user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """快速检查：已配置 Key 的模型走真实探测，未配置则标 not_configured。"""
    result = await GEOEngine.check_keyword(keyword, db=db)
    result["mode"] = "live"
    return success_response(data=result)


# ─────────────────────────────────────────────
# 新增端点：GEO 内容质量评估（RAG Evaluator）
# ─────────────────────────────────────────────

class EvaluateContentRequest(BaseModel):
    intent: str = ""         # 用户意图 / 目标描述
    content: str             # 待评估内容
    required_terms: Optional[List[str]] = None  # 自定义必现词（可选）


@router.post("/evaluate-content")
def evaluate_content(
    body: EvaluateContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    评估内容质量（GEO 蒸馏质量）
    返回：是否通过、评分、未通过原因
    """
    from app.services.geo_rag_evaluator import GEORAGEvaluator
    evaluator = GEORAGEvaluator(required_terms=tuple(body.required_terms) if body.required_terms else None)
    result = evaluator.evaluate(intent=body.intent or body.content[:100], content=body.content)
    return success_response(data={
        "passed": result.passed,
        "score": result.score,
        "reasons": result.reasons,
        "semantic_score": result.semantic_score,
        "coverage_score": result.coverage_score,
        "threshold": GEORAGEvaluator.PASS_THRESHOLD,
    })


@router.post("/evaluate-and-rewrite")
def evaluate_and_rewrite(
    body: EvaluateContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    评估内容，不通过则自动改写
    返回：改写后的内容和评估结果
    """
    from app.services.geo_rag_evaluator import GEORAGEvaluator
    evaluator = GEORAGEvaluator(required_terms=tuple(body.required_terms) if body.required_terms else None)
    rewritten, result = evaluator.evaluate_and_rewrite_if_needed(
        intent=body.intent or body.content[:100],
        content=body.content,
    )
    return success_response(data={
        "original_passed": result.passed,
        "original_score": result.score,
        "rewritten_content": rewritten,
        "rewritten_evaluation": {
            "passed": result.passed,
            "score": result.score,
            "reasons": result.reasons,
        },
    })


# ─────────────────────────────────────────────
# 新增端点：Rank Guard 质量门禁
# ─────────────────────────────────────────────

class RankGuardCheckRequest(BaseModel):
    lcp_ms: int = 2500
    inp_ms: int = 200
    error_rate: float = 0.0
    inquiry_rate: float = 0.0
    baseline_inquiry_rate: float = 0.05
    rank_signal: float = 50.0
    baseline_rank_signal: float = 50.0
    seo_audit_score: Optional[float] = None
    geo_indexed_rate: Optional[float] = None


@router.post("/rank-guard/check")
def rank_guard_check(
    body: RankGuardCheckRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    发布前质量门禁检查（五维 + 扩展）
    返回：是否通过、拦截原因、警告原因
    """
    from app.services.geo_rank_guard import GEORankGuard, GuardMetrics
    guard = GEORankGuard()
    metrics = GuardMetrics(
        lcp_ms=body.lcp_ms,
        inp_ms=body.inp_ms,
        error_rate=body.error_rate,
        inquiry_rate_delta=(body.inquiry_rate - body.baseline_inquiry_rate) / max(body.baseline_inquiry_rate, 0.001),
        rank_signal_delta=(body.rank_signal - body.baseline_rank_signal) / max(abs(body.baseline_rank_signal), 0.001),
        seo_audit_score=body.seo_audit_score,
        geo_indexed_rate=body.geo_indexed_rate,
    )
    result = guard.evaluate(metrics)
    return success_response(data={
        "passed": result.passed,
        "blocked_reasons": result.blocked_reasons,
        "warning_reasons": result.warning_reasons,
        "checked_at": result.checked_at,
        "message": guard.format_blocked_message(result),
    })


# ─────────────────────────────────────────────
# 新增端点：竞品监控计划
# ─────────────────────────────────────────────

class MonitorPlanRequest(BaseModel):
    keyword: str = "轻集料混凝土"
    platforms: Optional[List[str]] = None


@router.post("/monitor/plan")
def create_monitor_plan(
    body: MonitorPlanRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    生成竞品 GEO 监控计划
    """
    from app.services.geo_agents import CompetitorMonitorAgent
    agent = CompetitorMonitorAgent()
    plan = agent.build_monitor_plan(body.keyword)
    return success_response(data=plan)


@router.get("/monitor/run")
async def run_monitor(
    keyword: str = Query("轻集料混凝土"),
    user: User = Depends(get_current_super_admin),
):
    """
    手动触发一次竞品监控检查
    """
    from app.services.geo_agents import CompetitorMonitorAgent
    agent = CompetitorMonitorAgent()
    results = await agent.run_check(keyword)
    return success_response(data={
        "keyword": keyword,
        "results": [AlertResponse.model_validate(r.__dict__).model_dump() for r in results],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────────
# 新增端点：技术雷达扫描计划
# ─────────────────────────────────────────────

@router.get("/tech-radar/plan")
def get_tech_radar_plan(user: User = Depends(get_current_super_admin)):
    """
    获取技术雷达每日扫描计划
    """
    from app.services.geo_agents import TechRadarAgent
    agent = TechRadarAgent()
    plan = agent.build_daily_scan_plan()
    return success_response(data=plan)


@router.get("/tech-radar/run")
async def run_tech_radar(user: User = Depends(get_current_super_admin)):
    """
    手动触发一次技术雷达扫描
    """
    from app.services.geo_agents import TechRadarAgent
    agent = TechRadarAgent()
    result = await agent.run_daily_scan()
    return success_response(data=result)


# ─────────────────────────────────────────────
# 新增端点：调度器状态
# ─────────────────────────────────────────────

@router.get("/scheduler/status")
async def get_scheduler_status(user: User = Depends(get_current_super_admin)):
    """
    获取 GEO 调度器状态（定时任务列表）
    """
    from app.services.geo_agents import build_daily_jobs, run_scheduler_once
    status = await run_scheduler_once()
    return success_response(data=status)


@router.post("/scheduler/register-tasks")
def register_celery_tasks(user: User = Depends(get_current_super_admin)):
    """
    注册 GEO Celery 任务到 app（需要在 celery_app.py 启动时调用）
    """
    from app.services.geo_agents import register_celery_tasks
    ok = register_celery_tasks()
    return success_response(data={"registered": ok})


# ────────────────────────────────────────────
# 新增端点：GEO Alert 预警系统
# ────────────────────────────────────────────

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.geo_alert_models import (
    AlertRuleCreate, AlertCreate, AlertAcknowledge, AlertResolve,
    AlertRuleResponse, AlertResponse, AlertListResponse, AlertStatisticsResponse,
    AlertSeverity, AlertType, AlertStatus,
)
from app.services.geo_alert_service import geo_alert_service


@router.get("/alerts/rules")
def list_alert_rules(
    enabled_only: bool = Query(False, description="只返回启用的规则"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """列出预警规则"""
    rules = geo_alert_service.list_rules(db, enabled_only=enabled_only)
    return success_response(data=[AlertRuleResponse.model_validate(r.__dict__) for r in rules])


@router.post("/alerts/rules")
def create_alert_rule(
    body: AlertRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """创建预警规则"""
    rule = geo_alert_service.create_rule(db, body)
    return success_response(data=AlertRuleResponse.model_validate(rule.__dict__))


@router.get("/alerts/rules/{rule_id}")
def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """获取单个预警规则"""
    rule = geo_alert_service.get_rule(db, rule_id)
    if not rule:
        return success_response(success=False, error="Rule not found")
    return success_response(data=AlertRuleResponse.model_validate(rule.__dict__))


@router.put("/alerts/rules/{rule_id}")
def update_alert_rule(
    rule_id: int,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """更新预警规则"""
    rule = geo_alert_service.update_rule(db, rule_id, body)
    if not rule:
        return success_response(success=False, error="Rule not found")
    return success_response(data=AlertRuleResponse.model_validate(rule.__dict__))


@router.post("/alerts/rules/{rule_id}/trigger")
def trigger_alert_rule(
    rule_id: int,
    context: dict = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """手动触发规则检查"""
    alert = geo_alert_service.trigger_rule(db, rule_id, context)
    if not alert:
        return success_response(data=None, message="Rule not triggered")
    return success_response(data=AlertResponse.model_validate(alert.__dict__))


@router.get("/alerts")
def list_alerts(
    status: Optional[str] = Query(None, description="按状态过滤"),
    severity: Optional[str] = Query(None, description="按严重程度过滤"),
    alert_type: Optional[str] = Query(None, description="按类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """列出预警"""
    result = geo_alert_service.list_alerts(
        db, status=status, severity=severity, alert_type=alert_type,
        page=page, page_size=page_size,
    )
    # 转换 items 为 AlertResponse
    items = [AlertResponse.model_validate(a.__dict__) for a in result["items"]]
    result["items"] = items
    return success_response(data=AlertListResponse(**result))


@router.get("/alerts/statistics")
def get_alert_statistics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """获取预警统计"""
    stats = geo_alert_service.get_statistics(db)
    return success_response(data=AlertStatisticsResponse(**stats))


@router.post("/alerts/check-all")
def check_all_alert_rules(
    context: dict = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """检查所有启用的规则"""
    alerts = geo_alert_service.check_all_rules(db, context)
    return success_response(data=[AlertResponse.model_validate(a.__dict__) for a in alerts])


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """获取单个预警"""
    alert = geo_alert_service.get_alert(db, alert_id)
    if not alert:
        return success_response(success=False, error="Alert not found")
    return success_response(data=AlertResponse.model_validate(alert.__dict__))


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    body: AlertAcknowledge,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """确认预警"""
    alert = geo_alert_service.acknowledge(db, alert_id, body)
    if not alert:
        return success_response(success=False, error="Alert not found")
    return success_response(data=AlertResponse.model_validate(alert.__dict__))


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    body: AlertResolve,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """解决预警"""
    alert = geo_alert_service.resolve(db, alert_id, body)
    if not alert:
        return success_response(success=False, error="Alert not found")
    return success_response(data=AlertResponse.model_validate(alert.__dict__))


@router.get("/alerts/{alert_id}/histories")
def get_alert_histories(
    alert_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """获取预警历史记录"""
    histories = geo_alert_service.get_histories(db, alert_id)
    return success_response(data=[AlertResponse.model_validate(h.__dict__).model_dump() for h in histories])


# ────────────────────────────────────────────
# 快捷创建 GEO 专用预警规则
# ────────────────────────────────────────────

class CreateGEORankRuleRequest(BaseModel):
    keyword: str = "轻集料混凝土"
    baseline_rank: int = 10
    drop_threshold: int = 5


class CreateGEOInquiryRuleRequest(BaseModel):
    baseline_rate: float = 0.1
    drop_threshold: float = 0.05


@router.post("/alerts/quick-create/geo-rank")
def quick_create_geo_rank_rule(
    body: CreateGEORankRuleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """快捷创建 GEO 排名监控规则"""
    rule = geo_alert_service.create_geo_rank_rule(
        db,
        keyword=body.keyword,
        baseline_rank=body.baseline_rank,
        drop_threshold=body.drop_threshold,
    )
    return success_response(data=AlertRuleResponse.model_validate(rule.__dict__))


@router.post("/alerts/quick-create/geo-inquiry")
def quick_create_geo_inquiry_rule(
    body: CreateGEOInquiryRuleRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """快捷创建 GEO 询盘转化率监控规则"""
    rule = geo_alert_service.create_geo_inquiry_rule(
        db,
        baseline_rate=body.baseline_rate,
        drop_threshold=body.drop_threshold,
    )
    return success_response(data=AlertRuleResponse.model_validate(rule.__dict__))


# ──────────────────────────────────────
# 新增端点：GEO Generate 内容生成与评估
# ──────────────────────────────────────

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=255, description="目标关键词")
    intent: str = Field(min_length=1, description="用户意图 / 查询目标")
    content: str = Field(min_length=1, description="待生成或评估的内容")
    product_slug: str = Field(default="polyurethane-lightweight-concrete", description="关联产品 slug")


class GenerateResponse(BaseModel):
    content_id: Optional[int] = None
    passed: bool
    score: float
    reasons: List[str]
    keyword: str
    final_content: str
    semantic_score: Optional[float] = None
    coverage_score: Optional[float] = None


@router.post("/generate/evaluate")
def generate_evaluate(
    body: GenerateRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    仅评估内容质量（不保存，不生成）
    用于快速检查内容是否符合 GEO 标准
    """
    from app.services.geo_rag_evaluator import GEORAGEvaluator
    passed, score, reasons = GEORAGEvaluator().evaluate(body.intent, body.content)
    return success_response(data={
        "passed": passed,
        "score": score,
        "reasons": reasons,
        "keyword": body.keyword,
    })


# ──────────────────────────────────────
# 新增端点：Lead 询盘统计（从 sourcechain-geo-engine 合并）
# ──────────────────────────────────────

@router.get("/leads/summary")
async def get_leads_summary(
    user: User = Depends(get_current_super_admin),
):
    """
    询盘统计摘要
    
    返回总询盘数、总方量、平均预估价格、地区分布
    用于 RankGuard 的 inquiry_rate_delta 检查器
    """
    from app.services.geo_lead_service import summarize_leads
    summary = await summarize_leads()
    return success_response(data=summary)


@router.post("/generate/content")
def generate_content(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """
    生成/评估内容：评估 → 不通过则改写 → 保存到数据库
    返回：内容ID、评估分数、最终内容
    """
    from app.services.geo_rag_evaluator import GEORAGEvaluator
    evaluator = GEORAGEvaluator()
    passed, score, reasons = evaluator.evaluate(body.intent, body.content)
    final_content = body.content if passed else evaluator.rewrite_content(
        keyword=body.keyword,
        intent=body.intent,
        content=body.content,
    )
    # 保存内容块到 Redis（轻量存储，后续可迁移到数据库）
    content_id = f"geo_content_{body.keyword}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        from app.core.database import get_redis
        redis_client = get_redis()
        if redis_client:
            import json
            redis_client.set(
                f"geo:content:{content_id}",
                json.dumps({
                    "keyword": body.keyword,
                    "intent": body.intent,
                    "content": final_content,
                    "passed": passed,
                    "score": score,
                    "created_at": datetime.now().isoformat(),
                }, ensure_ascii=False),
                ex=86400 * 30,
            )
    except Exception as e:
        logger.warning(f"保存内容块失败: {e}")

    return success_response(data={
        "content_id": content_id,
        "passed": passed,
        "score": score,
        "reasons": reasons,
        "keyword": body.keyword,
        "final_content": final_content,
        "semantic_score": None,
        "coverage_score": None,
    })


@router.get("/generate/history")
def get_generate_history(
    keyword: Optional[str] = Query(None, description="按关键词过滤"),
    status: Optional[str] = Query(None, description="按状态过滤（passed/rewritten）"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_super_admin),
):
    """获取历史生成内容列表"""
    # 从 Redis 查询历史记录
    try:
        from app.core.database import get_redis
        redis_client = get_redis()
        if redis_client:
            import json
            pattern = "geo:content:*"
            keys = list(redis_client.scan_iter(match=pattern, count=100))
            results = []
            for k in keys[:limit]:
                raw = redis_client.get(k)
                if raw:
                    data = json.loads(raw)
                    if keyword and data.get("keyword") != keyword:
                        continue
                    if status:
                        if status == "passed" and not data.get("passed"):
                            continue
                        if status == "rewritten" and data.get("passed"):
                            continue
                    results.append(data)
            return success_response(data=results[:limit])
    except Exception as e:
        logger.warning(f"查询历史记录失败: {e}")
    return success_response(data=[])


# ─────────────────────────────────────────────
# 新增端点：GEO 优化器（从 geo_optimizer.py 合并）
# ─────────────────────────────────────────────

class OptimizeContentRequest(BaseModel):
    """优化内容请求"""
    content: str = Field(min_length=1, description="待优化内容")
    target_keywords: List[str] = Field(min_length=1, description="目标关键词列表")
    context: Optional[Dict[str, Any]] = Field(default={}, description="上下文信息")


@router.post("/optimizer/analyze")
async def analyze_content_ge(
    body: OptimizeContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    分析内容GEO评分
    返回：GE0评分、优化建议
    """
    from app.geo_engine.geo_optimizer import GEOOptimizer, GEOScore
    optimizer = GEOOptimizer()
    score: GEOScore = await optimizer.analyze_content(
        content=body.content,
        target_keywords=body.target_keywords,
        context=body.context,
    )
    return success_response(data={
        "overall_score": score.overall_score,
        "visibility_score": score.visibility_score,
        "relevance_score": score.relevance_score,
        "freshness_score": score.freshness_score,
        "authority_score": score.authority_score,
        "recommendations": [
            {
                "category": r.category,
                "priority": r.priority,
                "title": r.title,
                "description": r.description,
                "impact_score": r.impact_score,
                "implementation_effort": r.implementation_effort,
            }
            for r in score.recommendations
        ],
        "details": score.details,
    })


@router.post("/optimizer/optimize")
async def optimize_content_ge(
    body: OptimizeContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    优化内容并返回优化后的版本
    返回：优化后的内容、新GEO评分
    """
    from app.geo_engine.geo_optimizer import GEOOptimizer
    optimizer = GEOOptimizer()
    optimized_content, new_score = await optimizer.optimize_content(
        content=body.content,
        target_keywords=body.target_keywords,
        context=body.context,
    )
    return success_response(data={
        "original_content": body.content[:100] + "..." if len(body.content) > 100 else body.content,
        "optimized_content": optimized_content,
        "new_score": new_score.overall_score,
        "improvements": new_score.overall_score - 50.0,  # 假设基础分50
    })


# ─────────────────────────────────────────────
# 新增端点：排名监控器（从 rank_monitor.py 合并）
# ─────────────────────────────────────────────

class AddKeywordRequest(BaseModel):
    """添加监控关键词请求"""
    keyword: str = Field(min_length=1, description="关键词")
    search_engines: List[str] = Field(description="搜索引擎列表（chatgpt, perplexity, bard, bing_chat）")


class CheckRankRequest(BaseModel):
    """检查排名请求"""
    keyword: str = Field(min_length=1, description="关键词")
    search_engine: str = Field(default="chatgpt", description="搜索引擎")


@router.post("/rank-monitor/add-keyword")
async def add_monitor_keyword(
    body: AddKeywordRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    添加监控关键词
    """
    from app.geo_engine.rank_monitor import RankMonitor, SearchEngine
    monitor = RankMonitor()
    engines = [SearchEngine(e) for e in body.search_engines]
    success = await monitor.add_keyword(body.keyword, engines)
    return success_response(data={"added": success, "keyword": body.keyword})


@router.post("/rank-monitor/check")
async def check_keyword_rank(
    body: CheckRankRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    检查关键词排名（真实搜索引擎查询）
    返回：排名位置或None（未进入前10）
    """
    from app.geo_engine.rank_monitor import RankMonitor, SearchEngine
    monitor = RankMonitor()
    try:
        engine = SearchEngine(body.search_engine)
    except ValueError:
        return success_response(success=False, error=f"不支持的搜索引擎: {body.search_engine}")
    
    rank = await monitor.check_rank(body.keyword, engine, mock=False)
    if rank:
        return success_response(data={
            "keyword": rank.keyword,
            "search_engine": rank.search_engine.value,
            "position": rank.position,
            "url": rank.url,
            "title": rank.title,
            "checked_at": rank.checked_at.isoformat(),
        })
    else:
        return success_response(data={"keyword": body.keyword, "position": 0, "message": "未进入前10"})


@router.get("/rank-monitor/trend")
async def get_rank_trend(
    keyword: str = Query(..., description="关键词"),
    search_engine: str = Query("chatgpt", description="搜索引擎"),
    days: int = Query(30, ge=1, le=90, description="天数"),
    user: User = Depends(get_current_super_admin),
):
    """
    获取关键词排名趋势
    """
    from app.geo_engine.rank_monitor import RankMonitor, SearchEngine
    monitor = RankMonitor()
    try:
        engine = SearchEngine(search_engine)
    except ValueError:
        return success_response(success=False, error=f"不支持的搜索引擎: {search_engine}")
    
    trend = await monitor.get_rank_trend(keyword, engine, days)
    return success_response(data={
        "keyword": keyword,
        "search_engine": engine.value,
        "days": days,
        "trend": [
            {
                "position": r.position,
                "checked_at": r.checked_at.isoformat(),
            }
            for r in trend
        ],
    })


@router.get("/rank-monitor/report")
async def generate_rank_report(
    keywords: List[str] = Query(..., description="关键词列表"),
    search_engines: List[str] = Query(..., description="搜索引擎列表"),
    days: int = Query(30, ge=1, le=90, description="天数"),
    user: User = Depends(get_current_super_admin),
):
    """
    生成排名报告
    """
    from app.geo_engine.rank_monitor import RankMonitor, SearchEngine
    monitor = RankMonitor()
    engines = [SearchEngine(e) for e in search_engines]
    report = await monitor.generate_rank_report(keywords, engines, days)
    return success_response(data=report)


# ────────────────────────────────────────────
# GEO 优化器端点（新增）
# ────────────────────────────────────────────

class AnalyzeContentRequest(BaseModel):
    content: str = "轻集料混凝土是一种新型的建筑材料..."
    keyword: str = "轻集料混凝土"


@router.post("/optimizer/analyze")
async def analyze_content(
    body: AnalyzeContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    分析内容GEO评分（生成引擎优化评分）
    返回：GEO评分、建议列表
    """
    from app.geo_engine.geo_optimizer import GEOOptimizer
    optimizer = GEOOptimizer()
    score_obj = await optimizer.analyze_content(body.content, body.keyword)
    return success_response(data={
        "overall_score": score_obj.overall_score,
        "dimension_scores": score_obj.dimension_scores,
        "passed": score_obj.passed,
        "recommendations": [
            {
                "priority": r.priority,
                "dimension": r.dimension,
                "message": r.message,
                "suggestion": r.suggestion,
            }
            for r in score_obj.recommendations
        ],
        "keyword": body.keyword,
    })


class OptimizeContentRequest(BaseModel):
    content: str = "轻集料混凝土是一种新型的建筑材料..."
    keyword: str = "轻集料混凝土"


@router.post("/optimizer/optimize")
async def optimize_content(
    body: OptimizeContentRequest,
    user: User = Depends(get_current_super_admin),
):
    """
    优化内容（基于GEO评分自动优化）
    返回：优化后的内容、优化评分
    """
    from app.geo_engine.geo_optimizer import GEOOptimizer
    optimizer = GEOOptimizer()
    optimized = await optimizer.optimize_content(body.content, body.keyword)
    return success_response(data={
        "original_content": body.content[:100] + "..." if len(body.content) > 100 else body.content,
        "optimized_content": optimized[:200] + "..." if len(optimized) > 200 else optimized,
        "keyword": body.keyword,
        "message": "内容已优化，请查看 optimized_content 字段获取完整内容",
    })
