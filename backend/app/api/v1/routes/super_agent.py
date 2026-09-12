"""
UBrain 超级智能体 API 路由

集成 DeerFlow (研究) → UBrain (决策) → AccioWork (执行) 全链路
支持效果回流机制
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.response import success_response, error_response
from app.core.security import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.services.tenant_scenario_service import resolve_tenant_id_for_user
from app.services.ubrain.channel_status import get_all_channel_statuses

logger = logging.getLogger(__name__)

# ========== 引擎延迟加载 ==========

_deerflow_engine = None
_acciowork_engine = None
_ubrain_core = None

# 内存任务存储（降级方案：Redis 不可用时使用）
_task_store: Dict[str, Dict[str, Any]] = {}


def _get_task_store_key(task_id: str) -> str:
    """生成任务存储的 Redis key"""
    return f"super_agent:task:{task_id}"


def get_deerflow_engine():
    """获取 DeerFlow 研究引擎实例（延迟加载）。
    
    SECURITY: 初始化失败时返回 None，调用方需检查 None 并提供降级方案。
    """
    global _deerflow_engine
    if _deerflow_engine is None:
        try:
            from ai_engine.deerflow.engine import create_deerflow_engine
            _deerflow_engine = create_deerflow_engine()
            logger.info("DeerFlow 研究引擎初始化成功")
        except ImportError as e:
            logger.warning("DeerFlow 引擎导入失败（模块未安装）: %s", e)
        except Exception as e:
            logger.error("DeerFlow 引擎初始化失败: %s", e)
    return _deerflow_engine


def get_acciowork_engine():
    """获取 AccioWork 执行引擎实例（延迟加载）。
    
    SECURITY: 优先尝试 ai_engine.acciowork，失败后降级到本地桥接实现。
    """
    global _acciowork_engine
    if _acciowork_engine is None:
        try:
            from ai_engine.acciowork.engine import create_acciowork_engine
            _acciowork_engine = create_acciowork_engine()
            logger.info("AccioWork 执行引擎初始化成功")
        except ImportError as e:
            logger.warning("AccioWork 引擎导入失败（模块未安装），使用本地桥接: %s", e)
        except Exception as e:
            logger.error("AccioWork 引擎初始化失败，使用本地桥接: %s", e)
    
    if _acciowork_engine is None:
        from app.services.ubrain.super_agent_bridge import get_native_acciowork_engine
        try:
            _acciowork_engine = get_native_acciowork_engine()
            logger.info("本地 AccioWork 桥接引擎初始化成功")
        except Exception as e:
            logger.error("本地 AccioWork 桥接引擎初始化也失败: %s", e)
    return _acciowork_engine


def get_ubrain_core():
    """获取 UBrain 决策中枢实例（延迟加载）。
    
    SECURITY: 需要 DeerFlow 和 AccioWork 引擎都可用才能初始化。
    如果 LLM API 未配置，也会返回 None。
    """
    global _ubrain_core
    if _ubrain_core is None:
        deerflow = get_deerflow_engine()
        acciowork = get_acciowork_engine()
        if deerflow is None or acciowork is None:
            logger.warning("UBrain 初始化需要 DeerFlow 和 AccioWork 引擎，当前至少一个不可用")
            return None
        
        from app.core.config import settings
        api_key = getattr(settings, 'AI_OPENAI_API_KEY', None)
        if not api_key:
            logger.warning("UBrain 初始化需要 AI_OPENAI_API_KEY，当前未配置")
            return None
        
        try:
            from ai_engine.ubrain.core import create_ubrain_core
            from langchain_openai import ChatOpenAI
            base_url = getattr(settings, 'AI_OPENAI_BASE_URL', 'https://api.openai.com/v1')
            llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0,
                api_key=api_key,
                base_url=base_url,
            )
            _ubrain_core = create_ubrain_core(deerflow, acciowork, llm)
            logger.info("UBrain 决策中枢初始化成功")
        except ImportError as e:
            logger.warning("UBrain 引擎导入失败（模块未安装）: %s", e)
        except Exception as e:
            logger.error("UBrain 引擎初始化失败: %s", e)
    return _ubrain_core


# ========== 任务存储辅助 ==========

def _store_task(task_id: str, task_data: Dict[str, Any]) -> None:
    """保存任务到 Redis（内存作为降级方案）"""
    from app.core.cache import set_cache, redis_available
    from datetime import timedelta
    full_data = {
        **task_data,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if redis_available():
        key = _get_task_store_key(task_id)
        set_cache(key, full_data, expire=timedelta(hours=24))
    else:
        _task_store[task_id] = full_data


def _get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """从 Redis 获取任务（内存作为降级方案）"""
    from app.core.cache import get_cache, redis_available
    if redis_available():
        key = _get_task_store_key(task_id)
        return get_cache(key)
    return _task_store.get(task_id)


def _acciowork_exec_params(
    db: Session,
    user: User | None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """为原生 AccioWork 桥注入 DB/租户上下文。

    SECURITY: 开发环境回退逻辑仅在 development 环境生效，生产环境必须明确配置租户。
    """
    from app.core.config import settings
    out = dict(params or {})
    out["_db"] = db
    if user is not None:
        tenant_id = resolve_tenant_id_for_user(db, user)
        if tenant_id:
            out["_tenant_id"] = tenant_id
        elif user.role in ("super_admin", "admin"):
            from app.models.tenant import Tenant
            # SECURITY: 开发环境回退逻辑
            if settings.ENVIRONMENT == "development":
                dev_tenant = (
                    db.query(Tenant).filter(Tenant.domain == "dev.local").first()
                )
                if dev_tenant is not None:
                    out["_tenant_id"] = str(dev_tenant.id)
                    out["_tenant_context"] = "dev.local_admin_fallback"
            else:
                # SECURITY: 生产环境禁止回退，必须明确配置租户
                logger.warning(
                    "生产环境中超级管理员缺少租户上下文，tenant_id 未设置",
                    extra={"user_id": user.id, "role": user.role},
                )
    return out



# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/super-agent", tags=["超级智能体"])


# ========== 请求/响应模型 ==========

class ResearchRequest(BaseModel):
    """研究请求"""
    topic: str = Field(..., description="研究主题")
    depth: str = Field("standard", description="研究深度: quick, standard, comprehensive")
    focus_areas: Optional[List[str]] = Field(
        default=["market", "competition", "compliance"],
        description="关注领域"
    )


class InstructionRequest(BaseModel):
    """指令生成请求"""
    report_id: str = Field(..., description="研究报告ID")
    target_platforms: List[str] = Field(
        default=["shopify", "facebook"],
        description="目标平台"
    )
    execution_mode: str = Field(
        "semi-auto",
        description="执行模式: manual, semi-auto, auto"
    )


class ExecuteRequest(BaseModel):
    """执行请求"""
    instruction_id: str = Field(..., description="指令ID")


class SkillExecuteRequest(BaseModel):
    """技能执行请求"""
    skill_id: str = Field(..., description="技能ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="技能参数")


class CustomerFinderRequest(BaseModel):
    """客户开发请求"""
    model_config = ConfigDict(populate_by_name=True)
    keywords: List[str] = Field(..., description="搜索关键词")
    search_source: str = Field("all", alias="searchSource", description="搜索来源: all, reddit")
    countries: List[str] = Field(default_factory=list, description="目标国家")
    max_results: int = Field(50, alias="maxResults", description="最大结果数")
    industry: Optional[str] = Field(None, description="行业筛选")


class AutoNegotiatorRequest(BaseModel):
    """自动谈单请求"""
    action: str = Field("process_inquiry", description="操作类型: process_inquiry, generate_quote")
    customer_name: str = Field("", description="客户名称")
    customer_email: str = Field("", description="客户邮箱")
    products: List[Dict[str, Any]] = Field(default_factory=list, description="产品列表")
    quantity: int = Field(1, description="数量")
    destination: str = Field("", description="目的地")
    urgency: str = Field("normal", description="紧急程度")
    previous_messages: List[Dict[str, str]] = Field(default_factory=list, description="历史消息")


class EmailAutomationRequest(BaseModel):
    """开发信撰写请求"""
    action: str = Field("generate_email", description="操作类型: generate_email, create_campaign")
    customer_data: Dict[str, Any] = Field(default_factory=dict, description="客户数据")
    email_type: str = Field("cold_outreach", description="邮件类型")
    language: str = Field("en", description="语言")
    campaign_name: Optional[str] = Field(None, description="活动名称")
    customer_list: List[Dict[str, Any]] = Field(default_factory=list, description="客户列表")


class PerformanceRequest(BaseModel):
    """性能查询请求"""
    execution_id: str = Field(..., description="执行ID")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    metrics: Optional[List[str]] = Field(
        default=["views", "clicks", "conversions", "revenue"],
        description="指标列表"
    )


# ========== 后台任务：异步研究 ==========

async def _run_research_background(task_id: str, topic: str, depth: str, focus_areas: List[str]) -> None:
    """后台执行研究任务"""
    deerflow = get_deerflow_engine()
    if deerflow is None:
        _store_task(task_id, {
            "status": "failed",
            "error": "DeerFlow 引擎未初始化",
            "progress": 0,
        })
        return

    try:
        _store_task(task_id, {"status": "researching", "progress": 10, "current_stage": "planning"})
        report = await deerflow.start_research(
            topic=topic,
            depth=depth,
            focus_areas=focus_areas,
        )
        _store_task(task_id, {
            "status": "completed",
            "progress": 100,
            "result": report,
        })
    except Exception as e:
        logger.error(f"研究任务 {task_id} 执行失败: {e}")
        _store_task(task_id, {
            "status": "failed",
            "progress": 0,
            "error": str(e),
        })


# ========== 后台任务：异步执行指令 ==========

async def _run_execution_background(
    execution_id: str,
    instruction: Dict[str, Any],
) -> None:
    """后台执行 AccioWork 指令"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        _store_task(execution_id, {
            "status": "failed",
            "error": "AccioWork 引擎未初始化",
            "progress": 0,
        })
        return

    try:
        _store_task(execution_id, {"status": "in_progress", "progress": 10})
        result = await acciowork.execute_instruction(instruction)
        # 效果回流：将执行结果反馈给 UBrain 追踪
        ubrain = get_ubrain_core()
        if ubrain is not None:
            try:
                await ubrain.performance_tracker.track(
                    execution_id=execution_id,
                    metrics={
                        "completed_tasks": result.get("completed_tasks", 0),
                        "total_tasks": result.get("total_tasks", 0),
                    },
                )
            except Exception as track_err:
                logger.warning(f"效果追踪失败: {track_err}")

        _store_task(execution_id, {
            "status": "completed",
            "progress": 100,
            "result": result,
        })
    except Exception as e:
        logger.error(f"执行任务 {execution_id} 失败: {e}")
        _store_task(execution_id, {
            "status": "failed",
            "progress": 0,
            "error": str(e),
        })


# ========== 后台任务：端到端工作流 ==========

async def _run_workflow_background(
    workflow_id: str,
    topic: str,
    depth: str,
    target_platforms: List[str],
    execution_mode: str,
    focus_areas: List[str],
) -> None:
    """后台执行端到端工作流：研究 → 决策 → 执行 → 效果回流"""
    ubrain = get_ubrain_core()
    if ubrain is None:
        _store_task(workflow_id, {
            "status": "failed",
            "error": "UBrain 决策中枢未初始化",
            "stages": [
                {"name": "research", "status": "pending", "progress": 0},
                {"name": "analyze", "status": "pending", "progress": 0},
                {"name": "execute", "status": "pending", "progress": 0},
                {"name": "optimize", "status": "pending", "progress": 0},
            ],
        })
        return

    stages = [
        {"name": "research", "status": "pending", "progress": 0},
        {"name": "analyze", "status": "pending", "progress": 0},
        {"name": "execute", "status": "pending", "progress": 0},
        {"name": "optimize", "status": "pending", "progress": 0},
    ]
    try:
        # Phase 1: 研究
        stages[0] = {"name": "research", "status": "in_progress", "progress": 10}
        _store_task(workflow_id, {"status": "in_progress", "current_stage": "research", "stages": stages})
        report = await ubrain.deerflow.start_research(
            topic=topic,
            depth=depth,
            focus_areas=focus_areas,
        )
        stages[0] = {"name": "research", "status": "completed", "progress": 100}
        # Phase 2: 决策 - 生成指令
        stages[1] = {"name": "analyze", "status": "in_progress", "progress": 10}
        _store_task(workflow_id, {"status": "in_progress", "current_stage": "analyze", "stages": stages})
        instruction = await ubrain.instruction_generator.generate(
            report=report,
            target_platforms=target_platforms,
            execution_mode=execution_mode,
        )
        stages[1] = {"name": "analyze", "status": "completed", "progress": 100}
        # Phase 3: 执行
        stages[2] = {"name": "execute", "status": "in_progress", "progress": 10}
        _store_task(workflow_id, {"status": "in_progress", "current_stage": "execute", "stages": stages})
        execution_result = await ubrain.acciowork.execute_instruction(instruction)
        stages[2] = {"name": "execute", "status": "completed", "progress": 100}
        # Phase 4: 效果回流
        stages[3] = {"name": "optimize", "status": "in_progress", "progress": 10}
        _store_task(workflow_id, {"status": "in_progress", "current_stage": "optimize", "stages": stages})
        execution_id = execution_result.get("execution_id", str(uuid4()))
        await ubrain.performance_tracker.track(
            execution_id=execution_id,
            metrics={
                "completed_tasks": execution_result.get("completed_tasks", 0),
                "total_tasks": execution_result.get("total_tasks", 0),
            },
        )
        stages[3] = {"name": "optimize", "status": "completed", "progress": 100}
        _store_task(workflow_id, {
            "status": "completed",
            "current_stage": "optimize",
            "stages": stages,
            "report": report,
            "instruction": instruction,
            "execution_result": execution_result,
        })

    except Exception as e:
        logger.error(f"工作流 {workflow_id} 执行失败: {e}")
        # 标记当前阶段为失败
        for s in stages:
            if s["status"] == "in_progress":
                s["status"] = "failed"
        _store_task(workflow_id, {
            "status": "failed",
            "current_stage": stages,
            "error": str(e),
        })


# ========== 研究相关端点 ==========

@router.post("/research/start")
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """启动深度研究任务（异步执行，通过 status 端点查询进度）"""
    deerflow = get_deerflow_engine()
    if deerflow is None:
        return error_response(code=500, message="DeerFlow 研究引擎未初始化")

    report_id = f"df_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:6]}"
    _store_task(report_id, {
        "status": "started",
        "progress": 0,
        "topic": request.topic,
        "depth": request.depth,
        "current_stage": "planning",
    })
    background_tasks.add_task(
        _run_research_background,
        report_id,
        request.topic,
        request.depth,
        request.focus_areas or ["market", "competition", "compliance"],
    )
    return success_response(data={
        "report_id": report_id,
        "topic": request.topic,
        "depth": request.depth,
        "status": "started",
        "message": "研究任务已启动，请通过 /research/{report_id}/status 查询进度",
    })


@router.get("/research/{report_id}")
async def get_research_report(report_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取研究报告"""
    task = _get_task(report_id)
    if task is None:
        return error_response(code=404, message=f"研究报告 {report_id} 不存在")

    if task.get("status") != "completed":
        return success_response(data={
            "report_id": report_id,
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0),
            "message": "研究尚未完成，请稍后再查询",
        })

    report = task.get("result", {})
    return success_response(data=report)


@router.get("/research/{report_id}/status")
async def get_research_status(report_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取研究进度"""
    task = _get_task(report_id)
    if task is None:
        return error_response(code=404, message=f"研究任务 {report_id} 不存在")

    return success_response(data={
        "report_id": report_id,
        "status": task.get("status", "unknown"),
        "progress": task.get("progress", 0),
        "current_stage": task.get("current_stage", ""),
        "error": task.get("error"),
    })


# ========== 指令相关端点 ==========

@router.post("/instructions/generate")
async def generate_instructions(request: InstructionRequest, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """从研究报告生成执行指令"""
    ubrain = get_ubrain_core()
    if ubrain is None:
        return error_response(code=500, message="UBrain 决策中枢未初始化")

    # 查找研究报告
    task = _get_task(request.report_id)
    if task is None:
        return error_response(code=404, message=f"研究报告 {request.report_id} 不存在")

    if task.get("status") != "completed":
        return error_response(code=400, message="研究报告尚未完成，无法生成指令")

    report = task.get("result", {})
    if not report:
        return error_response(code=400, message="研究报告内容为空")

    try:
        instruction = await ubrain.instruction_generator.generate(
            report=report,
            target_platforms=request.target_platforms,
            execution_mode=request.execution_mode,
        )
        # 存储指令，供后续执行使用
        instruction_id = instruction.get("instruction_id", str(uuid4()))
        _store_task(f"inst_{instruction_id}", {
            "status": "generated",
            "instruction": instruction,
        })
        return success_response(data=instruction)
    except Exception as e:
        logger.error(f"指令生成失败: {e}")
        return error_response(code=500, message=f"指令生成失败: {str(e)}")


@router.post("/execute/{instruction_id}")
async def execute_instruction(
    instruction_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """执行指令（异步执行，通过 status 端点查询进度）"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        return error_response(code=500, message="AccioWork 执行引擎未初始化")

    # 查找指令
    inst_task = _get_task(f"inst_{instruction_id}")
    if inst_task is None:
        return error_response(code=404, message=f"指令 {instruction_id} 不存在")

    instruction = inst_task.get("instruction", {})
    execution_id = f"ex_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:6]}"
    _store_task(execution_id, {
        "status": "started",
        "progress": 0,
        "instruction_id": instruction_id,
    })
    background_tasks.add_task(
        _run_execution_background,
        execution_id,
        instruction,
    )
    return success_response(data={
        "execution_id": execution_id,
        "instruction_id": instruction_id,
        "status": "started",
        "message": "执行任务已启动，请通过 /execution/{execution_id}/status 查询进度",
    })


@router.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取执行状态"""
    task = _get_task(execution_id)
    if task is None:
        # 尝试从 AccioWork 引擎获取
        acciowork = get_acciowork_engine()
        if acciowork is not None:
            try:
                status = await acciowork.get_execution_status(execution_id)
                return success_response(data=status)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning("获取执行状态失败: %s", e)
                pass

    result = task.get("result", {})
    completed_tasks = result.get("completed_tasks", 0)
    total_tasks = result.get("total_tasks", 0)
    progress = task.get("progress", 0)
    return success_response(data={
        "execution_id": execution_id,
        "status": task.get("status", "unknown"),
        "progress": progress,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "error": task.get("error"),
    })


# ========== 技能相关端点 ==========

@router.get("/skills")
async def list_skills(
    category: Optional[str] = None,
    include_gaps: bool = Query(False),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """列出可用技能（合并 foreign_trade_ecosystem_catalog 状态）。"""
    from app.services.foreign_trade_ecosystem_service import list_skills as eco_skills
    eco = {s["id"]: s for s in eco_skills()}
    acciowork = get_acciowork_engine()
    skills: list[dict] = []
    if acciowork is not None:
        try:
            skills = acciowork.list_skills(category)
        except Exception as e:
            logger.warning(f"从 AccioWork 获取技能列表失败: {e}")

    if not skills:
        skills = [
            {"id": "smart_product_selection", "name": "智能选品", "category": "product_selection", "description": "基于大数据的蓝海品类挖掘"},
            {"id": "image_search", "name": "以图搜品", "category": "product_selection", "description": "上传图片自动匹配相似商品"},
            {"id": "one_click_store", "name": "一键建站", "category": "store_setup", "description": "30分钟生成多语言独立站"},
            {"id": "seo_optimization", "name": "SEO优化", "category": "store_setup", "description": "自动优化关键词密度和Meta标签"},
            {"id": "ad_generator", "name": "广告生成", "category": "marketing", "description": "Facebook/Google/TikTok 素材自动生成"},
            {"id": "social_calendar", "name": "社媒日历", "category": "marketing", "description": "结合热点事件的内容规划"},
            {"id": "supplier_matcher", "name": "供应商匹配", "category": "supply_chain", "description": "自动筛选优质供应商并发起询盘"},
            {"id": "compliance_checker", "name": "合规检查", "category": "supply_chain", "description": "CE/FDA/RoHS 认证自动识别"},
            {"id": "customer_finder", "name": "客户开发", "category": "sales", "description": "多渠道客户采集、智能筛选、评分排序"},
            {"id": "auto_negotiator", "name": "自动谈单", "category": "sales", "description": "RFQ监控、询盘回复、多轮谈判"},
            {"id": "email_automation", "name": "开发信撰写", "category": "sales", "description": "个性化邮件生成、多语言支持、自动跟进"},
        ]

    merged: list[dict] = []
    seen: set[str] = set()
    for s in skills:
        sid = s.get("id") or ""
        seen.add(sid)
        row = dict(s)
        if sid in eco:
            row["status"] = eco[sid].get("status")
            row["handler"] = eco[sid].get("handler")
            row["gw_task"] = eco[sid].get("gw_task")
        merged.append(row)

    if include_gaps:
        for sid, meta in eco.items():
            if sid in seen:
                continue
            if category and meta.get("category") != category:
                continue
            if meta.get("status") in ("gap", "reference", "partial"):
                merged.append(
                    {
                        "id": sid,
                        "name": meta.get("name"),
                        "category": meta.get("category"),
                        "description": meta.get("handler") or meta.get("integrate") or "",
                        "status": meta.get("status"),
                        "gw_task": meta.get("gw_task"),
                    }
                )

    if category:
        merged = [s for s in merged if s.get("category") == category]

    return success_response(data={"skills": merged, "total": len(merged), "ecosystem_catalog": "foreign_trade_ecosystem_catalog.json"})


@router.post("/skills/execute")
async def execute_skill(
    request: SkillExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行单个技能"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        return error_response(code=500, message="AccioWork引擎未初始化")

    try:
        params = _acciowork_exec_params(db, current_user, request.params)
        result = await acciowork.execute_skill(request.skill_id, params)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"技能 {request.skill_id} 执行失败: {e}")
        return error_response(code=500, message=f"技能执行失败: {str(e)}")


# ========== 客户开发端点 ==========

@router.get("/sales/channels")
def list_prospect_channels(
    current_user: User = Depends(get_current_user),
):
    """FIX-5: 返回所有获客渠道的真实可用状态。
    前端根据 status 字段决定是否展示该渠道：
      - "real": 真实 API 已配置，可正常使用
      - "mock": 尚未实现，返回演示数据（前端应标注"演示"或隐藏）
      - "coming_soon": 尚未开发
    """
    channels = get_all_channel_statuses()
    return success_response(data=[
        {
            "id": ch.id,
            "name": ch.name,
            "status": ch.status,
            "reason": ch.reason,
        }
        for ch in channels
    ])


@router.post("/sales/customer-finder")
async def find_customers(
    request: CustomerFinderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """客户开发 - 多渠道采集、智能筛选"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        return error_response(code=500, message="AccioWork引擎未初始化")

    try:
        params = _acciowork_exec_params(db, current_user, {
            "keywords": request.keywords,
            "search_source": request.search_source,
            "countries": request.countries,
            "max_results": request.max_results,
            "industry": request.industry,
        })
        result = await acciowork.execute_skill("customer_finder", params)
        results = result.get("results") or {}
        customers = results.get("customers") or []
        # 效果回流
        ubrain = get_ubrain_core()
        if ubrain is not None:
            try:
                await ubrain.performance_tracker.track(
                    execution_id=f"cf_{uuid4().hex[:8]}",
                    metrics={"customers_found": len(customers)},
                )
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning("Customer Finder 自动创建 inquiry 失败: %s", e)
                pass

        # ── Connection ③: Customer Finder → Inquiry 自动创建 ──
        auto_inquiries: list[dict[str, Any]] = []
        try:
            from app.services.attribution_service import create_inquiry_from_customer_finder
            for cust in customers:
                inquiry = create_inquiry_from_customer_finder(
                    db, cust, tenant_id=params.get("_tenant_id"),
                )
                if inquiry is not None:
                    auto_inquiries.append({
                        "inquiry_id": str(inquiry.id),
                        "customer_finder_id": str(cust.get("id", "")),
                        "name": inquiry.name,
                    })
        except Exception as cf_err:
            logger.warning("Customer Finder → Inquiry auto-creation failed: %s", cf_err)

        payload = {
            **results,
            "customers": customers,
            "total_found": results.get("total_found", len(customers)),
            "skill_id": result.get("skill_id"),
            "find_mode": result.get("find_mode") or results.get("mode"),
            "probe_mode": result.get("probe_mode") or results.get("probe_mode"),
            "email_enrichment": result.get("email_enrichment") or results.get("email_enrichment"),
            "human_verify_required": results.get("human_verify_required", True),
            "disclaimer": results.get("disclaimer"),
            "timestamp": result.get("timestamp"),
            "engine": result.get("engine"),
            "auto_inquiries_created": len(auto_inquiries),
            "auto_inquiries": auto_inquiries,
        }
        return success_response(data=payload)
    except Exception as e:
        logger.error(f"客户开发失败: {e}")
        return error_response(code=500, message=f"客户开发失败: {str(e)}")


@router.get("/sales/customer-finder/{customer_id}")
async def get_customer_detail(customer_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取客户详情"""
    try:
        from acciowork.skills.customer_finder import CustomerFinder
        finder = CustomerFinder()
        customer = finder.get_customer(customer_id)
        if customer is not None:
            data = customer.to_dict()
            data.setdefault("name", data.get("company_name", ""))
            return success_response(data=data)
    except ImportError:
        pass

    acciowork = get_acciowork_engine()
    if acciowork is not None:
        try:
            execute = acciowork.execute_skill
            if asyncio.iscoroutinefunction(execute):
                result = await execute("customer_finder", {
                    "keywords": [customer_id],
                    "max_results": 1,
                })
            else:
                result = execute("customer_finder", {
                    "keywords": [customer_id],
                    "max_results": 1,
                })
            if isinstance(result, dict):
                customers = result.get("results", {}).get("customers", [])
                if customers:
                    return success_response(data=customers[0])
        except Exception as e:
            logger.warning(f"从 AccioWork 获取客户详情失败: {e}")

    return error_response(code=404, message=f"客户 {customer_id} 不存在")


# ========== 自动谈单端点 ==========

@router.post("/sales/auto-negotiator")
async def auto_negotiate(
    request: AutoNegotiatorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """自动谈单 - RFQ监控、询盘回复、多轮谈判"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        return error_response(code=500, message="AccioWork引擎未初始化")

    try:
        params = _acciowork_exec_params(db, current_user, {
            "action": request.action,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "products": request.products,
            "quantity": request.quantity,
            "destination": request.destination,
            "urgency": request.urgency,
            "previous_messages": request.previous_messages,
        })
        result = await acciowork.execute_skill("auto_negotiator", params)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"自动谈单失败: {e}")
        return error_response(code=500, message=f"自动谈单失败: {str(e)}")


@router.get("/sales/negotiations")
async def list_negotiations(
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """获取谈判列表"""
    acciowork = get_acciowork_engine()
    if acciowork is not None:
        try:
            history = acciowork.get_execution_history(limit=limit, skill_id="auto_negotiator")
            if not isinstance(history, (list, tuple)):
                history = []
            negotiations = []
            for h in history:
                result = h.get("result", {}) if isinstance(h, dict) else {}
                neg_data = result.get("results", {}) if isinstance(result, dict) else {}
                if status and neg_data.get("status") != status:
                    continue
                negotiations.append({
                    "session_id": neg_data.get("session_id", h.get("skill_id") if isinstance(h, dict) else ""),
                    "customer_name": neg_data.get("customer_name", ""),
                    "product": neg_data.get("product", ""),
                    "status": neg_data.get("status", "unknown"),
                    "round": neg_data.get("round", 0),
                    "last_message": neg_data.get("last_message", ""),
                    "updated_at": h.get("timestamp", "") if isinstance(h, dict) else "",
                })
            return success_response(data={
                "negotiations": negotiations,
                "total": len(negotiations),
                "limit": limit,
            })
        except Exception as e:
            logger.warning(f"获取谈判列表失败: {e}")

    return success_response(data={
        "negotiations": [],
        "total": 0,
        "limit": limit,
    })


@router.post("/sales/negotiations/{session_id}/approve")
async def approve_negotiation(session_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """审批最终报价"""
    # 记录审批到效果追踪
    ubrain = get_ubrain_core()
    if ubrain is not None:
        try:
            await ubrain.performance_tracker.track(
                execution_id=f"neg_{session_id}",
                metrics={"approved": True},
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("自动审批报价失败: %s", e)
            pass
        return {
        "status": "approved",
        "message": "报价已审批，将自动发送给客户",
    }


# ========== 开发信撰写端点 ==========

@router.post("/sales/email-automation")
async def automate_email(
    request: EmailAutomationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开发信撰写 - 个性化邮件生成、自动跟进"""
    acciowork = get_acciowork_engine()
    if acciowork is None:
        return error_response(code=500, message="AccioWork引擎未初始化")

    try:
        params = _acciowork_exec_params(db, current_user, {
            "action": request.action,
            "customer_data": request.customer_data,
            "email_type": request.email_type,
            "language": request.language,
        })
        if request.action == "create_campaign":
            params["campaign_name"] = request.campaign_name
            params["customer_list"] = request.customer_list

        result = await acciowork.execute_skill("email_automation", params)
        return success_response(data=result)
    except Exception as e:
        logger.error(f"开发信生成失败: {e}")
        return error_response(code=500, message=f"开发信生成失败: {str(e)}")


@router.get("/sales/campaigns")
async def list_campaigns(limit: int = Query(20, le=100), current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取邮件活动列表"""
    acciowork = get_acciowork_engine()
    if acciowork is not None:
        try:
            history = acciowork.get_execution_history(limit=limit, skill_id="email_automation")
            campaigns = []
            for h in history:
                result = h.get("result", {})
                camp_data = result.get("results", {})
                if camp_data.get("campaign_id"):
                    campaigns.append({
                        "campaign_id": camp_data["campaign_id"],
                        "name": camp_data.get("name", ""),
                        "total_emails": camp_data.get("total_emails", 0),
                        "status": "active",
                        "created_at": h.get("timestamp", ""),
                    })
            return success_response(data={
                "campaigns": campaigns,
                "total": len(campaigns),
                "limit": limit,
            })
        except Exception as e:
            logger.warning(f"获取邮件活动列表失败: {e}")

    return success_response(data={"campaigns": [], "total": 0, "limit": limit})


@router.get("/sales/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取邮件活动统计"""
    ubrain = get_ubrain_core()
    if ubrain is not None:
        try:
            performance = await ubrain.performance_tracker.get_performance(campaign_id)
            if performance.get("metrics"):
                return success_response(data={
                    "campaign_id": campaign_id,
                    "stats": performance.get("summary", {}),
                    "metrics_history": performance.get("metrics", []),
                })
        except Exception as e:
            logger.warning(f"获取邮件活动统计失败: {e}")

    return error_response(code=404, message=f"活动 {campaign_id} 统计数据不存在")


# ========== 分析相关端点 ==========

@router.post("/analytics/performance")
async def get_performance(request: PerformanceRequest, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取性能数据"""
    ubrain = get_ubrain_core()
    if ubrain is not None:
        try:
            performance = await ubrain.performance_tracker.get_performance(
                execution_id=request.execution_id,
                date_range=request.date_range,
            )
            return success_response(data=performance)
        except Exception as e:
            logger.warning(f"获取性能数据失败: {e}")

    # 回退到任务存储
    task = _get_task(request.execution_id)
    if task is not None:
        result = task.get("result", {})
        return success_response(data={
            "execution_id": request.execution_id,
            "status": task.get("status"),
            "result": result,
            "date_range": request.date_range,
        })

    return error_response(code=404, message=f"执行记录 {request.execution_id} 不存在")


@router.post("/analytics/feedback/{execution_id}")
async def generate_feedback(execution_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """生成优化反馈（效果回流核心端点）"""
    ubrain = get_ubrain_core()
    if ubrain is None:
        return error_response(code=500, message="UBrain 决策中枢未初始化")

    try:
        feedback = await ubrain.performance_tracker.generate_feedback(
            execution_id=execution_id,
            llm=ubrain.llm,
        )
        return success_response(data=feedback)
    except Exception as e:
        logger.error(f"生成优化反馈失败: {e}")
        return error_response(code=500, message=f"生成优化反馈失败: {str(e)}")


# ========== 仪表板端点 ==========

@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取仪表板数据"""
    ubrain = get_ubrain_core()
    if ubrain is not None:
        try:
            dashboard = ubrain.get_dashboard()
            return success_response(data=dashboard)
        except Exception as e:
            logger.warning(f"获取仪表板数据失败: {e}")

    # 回退到内存任务存储统计
    total = len(_task_store)
    completed = sum(1 for t in _task_store.values() if t.get("status") == "completed")
    failed = sum(1 for t in _task_store.values() if t.get("status") == "failed")
    return success_response(data={
        "total_tasks": total,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "success_rate": completed / total if total > 0 else 0,
        "recent_tasks": [],
        "performance_summary": {},
    })


# ========== 端到端流程端点 ==========

@router.post("/workflow/start")
async def start_workflow(
    topic: str,
    depth: str = "standard",
    target_platforms: Optional[List[str]] = None,
    execution_mode: str = "semi-auto",
    focus_areas: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),  # SECURITY: 强制认证
):
    """启动端到端工作流：研究 → 决策 → 执行 → 效果回流"""
    ubrain = get_ubrain_core()
    if ubrain is None:
        return error_response(code=500, message="UBrain 决策中枢未初始化，无法启动工作流")

    workflow_id = f"wf_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:6]}"
    stages = [
        {"name": "research", "status": "pending", "progress": 0},
        {"name": "analyze", "status": "pending", "progress": 0},
        {"name": "execute", "status": "pending", "progress": 0},
        {"name": "optimize", "status": "pending", "progress": 0},
    ]
    _store_task(workflow_id, {
        "status": "started",
        "topic": topic,
        "depth": depth,
        "current_stage": "research",
        "stages": stages,
    })
    background_tasks.add_task(
        _run_workflow_background,
        workflow_id,
        topic,
        depth,
        target_platforms or ["shopify", "facebook"],
        execution_mode,
        focus_areas or ["market", "competition", "compliance"],
    )
    return success_response(data={
        "workflow_id": workflow_id,
        "topic": topic,
        "depth": depth,
        "status": "started",
        "stages": stages,
        "message": "端到端工作流已启动，请通过 /workflow/{workflow_id}/status 查询进度",
    })


@router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str, current_user: User = Depends(get_current_user)):  # SECURITY: 强制认证
    """获取工作流状态"""
    task = _get_task(workflow_id)
    if task is None:
        return error_response(code=404, message=f"工作流 {workflow_id} 不存在")

    stages = task.get("stages", [])
    overall_progress = sum(s.get("progress", 0) for s in stages) // max(len(stages), 1)
    return success_response(data={
        "workflow_id": workflow_id,
        "status": task.get("status", "unknown"),
        "current_stage": task.get("current_stage", ""),
        "stages": stages,
        "overall_progress": overall_progress,
        "error": task.get("error"),
    })
