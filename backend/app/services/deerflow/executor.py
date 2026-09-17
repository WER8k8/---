# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeerFlow 子任务执行器。

负责执行规划器生成的子任务，每个子任务有独立的 Trace span。
支持独立的重试策略和超时控制。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.services.deerflow.planner import ExecutionPlan, SubTask

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 真实能力接入辅助
# ---------------------------------------------------------------------------
# 陷阱：foreign_trade 的技能是**模块导入时**才 register 进 skill_registry 的，
# `app.services.foreign_trade.__init__` 并不导入各技能模块。未先导入就调用
# skill_registry.execute(name) 会永远得到「技能未注册」——这是把真实能力误判成
# 「能力不存在」的头号坑。故此处显式导入一次（Python import 有缓存，幂等）。
def _ensure_foreign_trade_skills() -> None:
    """导入外贸技能模块，确保 skill_registry 已填充。失败不影响调用方。"""
    try:
        from app.services.foreign_trade import (  # noqa: F401
            cold_email_skill,
            competitor_profile_skill,
            copywriting_skill,
            customer_research_skill,
            market_insight_skill,
            prospect_skill,
            sales_enablement_skill,
            seo_audit_skill,
            supplier_compare_skill,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("外贸技能模块导入失败，相关 intent 将降级: %s", exc)


def _run_coro(coro):
    """在同步上下文（Celery worker）安全执行协程。

    已有事件循环时（极少见，如被 async 链路嵌套调用）退化到新线程执行，
    避免 asyncio.run 抛 "cannot be called from a running event loop"。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


# ---------------------------------------------------------------------------
# 子任务执行结果
# ---------------------------------------------------------------------------

@dataclass
class SubTaskResult:
    """子任务执行结果。"""
    subtask_id: str
    success: bool
    intent: str
    agent_ref: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    trace_id: str = ""
    duration_ms: int = 0
    def to_dict(self) -> dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "subtask_id": self.subtask_id,
            "success": self.success,
            "intent": self.intent,
            "agent_ref": self.agent_ref,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "output": self.output,
            "error": self.error,
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms,
        }


# ---------------------------------------------------------------------------
# 子任务执行器
# ---------------------------------------------------------------------------

class SubTaskExecutor:
    """子任务执行器。

    逐个或分批执行执行计划中的子任务。
    每个子任务在独立的 OpenTelemetry Trace span 中执行。
    支持超时控制和独立重试。
    """
    def __init__(
        self,
        db: Session,
        job: DeerflowJob,
        *,
        on_subtask_start: Optional[callable] = None,
        on_subtask_complete: Optional[callable] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param job: 参数 job
        :param on_subtask_start: 参数 on_subtask_start
        :param on_subtask_complete: 参数 on_subtask_complete
        :return: 返回处理结果。
        """
        self.db = db
        self.job = job
        self.on_subtask_start = on_subtask_start
        self.on_subtask_complete = on_subtask_complete
        self._tracer = None

    @property
    def tracer(self):
        """延迟初始化 tracer，避免 OpenTelemetry 未配置时出错。"""
        if self._tracer is None:
            try:
                from opentelemetry import trace
                self._tracer = trace.get_tracer("deerflow-executor")
            except Exception:
                logger.debug("OpenTelemetry tracer not available")
        return self._tracer

    def execute_plan(
        self,
        plan: ExecutionPlan,
    ) -> list[SubTaskResult]:
        """执行完整的执行计划，返回所有子任务结果。

        按批次执行，同一批次内的任务顺序执行（如需并行由 Celery 任务层面处理）。
        """
        batches = plan.get_execution_order()
        all_results: list[SubTaskResult] = []
        logger.info(
            "Executing plan: job=%s batches=%d subtasks=%d",
            self.job.id, len(batches), len(plan.subtasks),
        )
        for batch_idx, batch in enumerate(batches):
            logger.info(
                "Executing batch %d/%d: %d subtasks",
                batch_idx + 1, len(batches), len(batch),
            )
            for subtask in batch:
                result = self.execute_subtask(subtask)
                all_results.append(result)
                if not result.success:
                    logger.warning(
                        "Subtask failed: job=%s subtask=%s error=%s",
                        self.job.id, subtask.id, result.error,
                    )
                    # 检查是否可重试
                    retry_result = self._maybe_retry(subtask, result)
                    if retry_result:
                        all_results[-1] = retry_result
                        result = retry_result

                    if not result.success:
                        # 记录失败并更新 checkpoint
                        self._save_subtask_result(subtask, result)
                        raise SubTaskExecutionError(
                            f"子任务执行失败: {subtask.title} ({subtask.id})",
                            subtask_id=subtask.id,
                            result=result,
                        )

                self._save_subtask_result(subtask, result)

        return all_results

    def execute_subtask(self, subtask: SubTask) -> SubTaskResult:
        """执行单个子任务。

        在独立的 Trace span 中执行，记录执行时间和输出。
        """
        start_time = datetime.now(timezone.utc)
        result = SubTaskResult(
            subtask_id=subtask.id,
            success=False,
            intent=subtask.intent,
            agent_ref=subtask.agent_ref,
            started_at=start_time.isoformat(),
        )
        # 通知回调
        if self.on_subtask_start:
            try:
                self.on_subtask_start(subtask)
            except Exception:
                pass

        # 在 Trace span 中执行
        span_context = None
        if self.tracer:
            from opentelemetry import trace
            with self.tracer.start_as_current_span(
                f"deerflow.subtask.{subtask.intent}",
                attributes={
                    "deerflow.job_id": str(self.job.id),
                    "deerflow.subtask_id": subtask.id,
                    "deerflow.subtask_title": subtask.title,
                    "deerflow.agent_ref": subtask.agent_ref,
                },
            ) as span:
                span_context = span
                result.trace_id = format(span.get_span_context().trace_id, "032x")
                result = self._do_execute(subtask, result, span)
        else:
            result = self._do_execute(subtask, result, None)

        # 计算执行时长
        end_time = datetime.now(timezone.utc)
        result.finished_at = end_time.isoformat()
        result.duration_ms = int((end_time - start_time).total_seconds() * 1000)
        # 事实层抽取：内容类子任务把产出抽成 FactKernel 挂到 result，
        # 供统一发布台按平台形态投影（不写 DB、不发网络；失败不影响主链）。
        if result.success and result.output:
            try:
                from app.services.deerflow.kernel_bridge import extract_kernel_from_subtask

                kernel = extract_kernel_from_subtask(result.intent, result.output)
                if kernel is not None:
                    result.output["fact_kernel"] = kernel.to_dict()
            except Exception as exc:  # 事实层抽取失败不得阻断 DeerFlow 主链
                logger.debug("deerflow 事实层抽取失败 subtask=%s: %s", subtask.id, exc)
        # 通知回调
        if self.on_subtask_complete:
            try:
                self.on_subtask_complete(subtask, result)
            except Exception:
                pass

        logger.info(
            "Subtask executed: job=%s subtask=%s success=%s duration=%dms",
            self.job.id, subtask.id, result.success, result.duration_ms,
        )
        return result

    # ------------------------------------------------------------------
    # 内部执行逻辑
    # ------------------------------------------------------------------
    def _do_execute(
        self,
        subtask: SubTask,
        result: SubTaskResult,
        span: Any,
    ) -> SubTaskResult:
        """实际执行子任务的逻辑。

        根据 intent 分发到对应的执行逻辑。
        """
        try:
            # 根据 intent 选择执行器
            output = self._dispatch_by_intent(subtask)
            result.success = True
            result.output = output
            if span:
                from opentelemetry import trace
                span.set_attribute("deerflow.subtask.success", True)
                span.set_attribute("deerflow.subtask.output_size", len(json.dumps(output)))

        except Exception as exc:
            result.success = False
            result.error = str(exc)[:500]
            logger.exception(
                "Subtask execution error: job=%s subtask=%s intent=%s",
                self.job.id, subtask.id, subtask.intent,
            )
            if span:
                from opentelemetry import trace
                span.set_attribute("deerflow.subtask.success", False)
                span.set_attribute("deerflow.subtask.error", result.error)
                span.set_status(trace.StatusCode.ERROR, result.error)

        return result

    def _dispatch_by_intent(self, subtask: SubTask) -> dict[str, Any]:
        """根据 intent 分发到对应的执行逻辑。

        对于已知的 intent 调用对应的服务，未知的 intent 尝试通用的 Hermes/Paperclip 调用。
        """
        intent = subtask.intent
        params = subtask.parameters
        # 关键词研究
        if intent == "keyword_research":
            return self._exec_keyword_research(params)

        # 内容创作
        if intent == "content_creation":
            return self._exec_content_creation(params)

        # SEO 发布
        if intent == "seo_publish":
            return self._exec_seo_publish(params)

        # 页面创建
        if intent == "page_creation":
            return self._exec_page_creation(params)

        # SEO 元数据
        if intent == "seo_metadata":
            return self._exec_seo_metadata(params)

        # 多渠道分发
        if intent == "multi_channel_publish":
            return self._exec_multi_channel_publish(params)

        # 买家研究
        if intent == "buyer_research":
            return self._exec_buyer_research(params)

        # 开发信生成
        if intent == "outreach_letter":
            return self._exec_outreach_letter(params)

        # 邮件发送
        if intent == "email_dispatch":
            return self._exec_email_dispatch(params)

        # 目标市场洞察（对标 Accio Work 市场洞察）
        if intent == "market_insight":
            return self._exec_market_insight(params)

        # 供应商/同行比较排序卡（对标 Accio Work 比价与供应商比较）
        if intent == "supplier_compare":
            return self._exec_supplier_compare(params)

        # 通用 Hermes/Paperclip 调用
        return self._exec_generic(subtask)

    # ------------------------------------------------------------------
    # Intent 处理函数（真实接线 + 安全降级）
    # ------------------------------------------------------------------
    # 设计约定（"每个环节做正确的事"）：
    # - **默认真执行**：所有 intent 一律接真实服务，不做"因为没接所以降级"的占位。
    # - 降级**唯一正当理由** = 外部依赖未就绪（无 LLM 凭据 / 无 Perplexity key /
    #   aitoearn 未启用 / 缺必填参数）。此时必须带**真实原因**，便于运维定位，
    #   而不是含糊的"暂无可接入服务"。
    # - 所有 _exec_* 不得向上抛未捕获异常：execute_plan 捕获 SubTaskExecutionError
    #   会把整个 DeerFlow job 判 FAILED，单个子任务失败不应连坐整条计划。
    def _degraded(
        self,
        intent: str,
        reason: str,
        params: dict[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """统一的降级返回：保留 completed（不连坐整条计划）但显式标记原因。

        兜底策略：若降级原因**不是**「缺必填参数」（参数不全时 LLM 也编不出结果），
        先尝试用技能包 SOP 真执行（自动智能调用 skills）。技能包可用则直接返回
        真执行结果，否则才按原逻辑降级，并在 reason 中标注已尝试过技能包。
        """
        blocked = ("缺少必填参数", "缺失", "required", "REQUIRED")
        if params and not any(b in str(reason) for b in blocked):
            attempt = self._run_skill_pack(intent, params)
            if attempt:
                logger.info(
                    "DeerFlow %s 经技能包 %s 真执行成功（原降级原因: %s）",
                    intent, attempt.get("skill_pack"), reason,
                )
                return attempt
            reason = f"{reason}（已尝试技能包兜底，未命中或执行失败）"
        payload: dict[str, Any] = {
            "status": "completed",
            "degraded": True,
            "intent": intent,
            "reason": reason,
        }
        if params is not None:
            payload["params"] = params
        payload.update(extra)
        logger.warning("DeerFlow %s 降级: %s", intent, reason)
        return payload

    def _run_skill_pack(
        self, intent: str, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """用**技能包**（skills/ 下 76 个业务 SOP）执行意图。

        这是「自动智能判断调用 skills」的落点：DeerFlow 某个 intent 没有专属
        真实服务（或专属服务不可用时），按意图自动匹配最相关的技能包 skill，
        取回它的 SKILL.md 正文作为 SOP，交给 LLM 执行。

        Returns:
            成功 → 结果 dict（status=completed, degraded=False, skill_pack=...）；
            技能包不可用 / 匹配不到 / 执行失败 → None，由调用方继续降级。
        """
        try:
            from app.services.registry.skill_pack_loader import load_skill_body
            from app.services.registry.skill_service import match_skill_scored

            db = self.db
            owns_db = False
            if db is None:
                from app.core.database import SessionLocal

                db = SessionLocal()
                owns_db = True
            try:
                hits = match_skill_scored(db, intent, top_k=1)
                if not hits:
                    return None
                skill, score = hits[0]

                # 取 SOP 正文：优先用入库时记录的绝对路径，回落按 name 扫描
                sop = ""
                try:
                    from pathlib import Path

                    impl = self._skill_implementation(skill)
                    p = impl.get("skill_pack_path") if impl else None
                    if p and Path(p).is_file():
                        sop = Path(p).read_text(encoding="utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    sop = ""
                if not sop:
                    sop = load_skill_body(skill.name)
                if not sop:
                    return None

                from app.services.ai_engine import AIEngine

                engine = AIEngine()
                llm = (
                    engine.llms.get("cost_optimized")
                    or engine.llms.get("deepseek")
                    or engine.llms.get("general")
                )
                if not llm:
                    return None

                # 关键：引擎默认 max_tokens 仅 2000~3000，而成本模型多为推理型，
                # 实测 reasoning 会吃光全部配额导致 finish_reason=length、
                # content 为空。这里为技能包执行单独放大输出上限。
                try:
                    llm = llm.bind(
                        max_tokens=int(os.environ.get("SKILL_PACK_MAX_TOKENS", "8000"))
                    )
                except Exception:  # noqa: BLE001  不支持 bind 时沿用原实例
                    pass

                # SOP 截断：部分 SKILL.md 很长，叠加任务后易触发模型输出上限
                max_chars = int(os.environ.get("SKILL_PACK_MAX_SOP_CHARS", "6000"))
                if len(sop) > max_chars:
                    sop = sop[:max_chars] + "\n\n[...SOP 已截断...]"

                # 注意：成本模型多为**推理型**（实测 qwen3.8-flash 会把
                # completion_tokens 全耗在 reasoning 上，导致 finish_reason=length、
                # content 为空）。故明确要求"直出结果、不要推理过程、控制篇幅"。
                prompt = (
                    f"{sop}\n\n---\n\n"
                    f"## 本次任务\n意图: {intent}\n"
                    f"参数: {json.dumps(params, ensure_ascii=False)}\n\n"
                    "要求：直接输出最终结果，不要输出思考过程或解释性长文，"
                    "篇幅控制在 800 字以内；优先输出 JSON。"
                )
                result = llm.invoke(prompt)
                content = (getattr(result, "content", "") or "").strip()
                if not content:
                    # 空内容 = 未真正产出（推理被截断/模型拒答）。
                    # 必须判为失败并让上层降级，绝不能拿空串冒充成功。
                    logger.warning(
                        "DeerFlow %s 技能包 %s 返回空内容，判为失败",
                        intent, getattr(skill, "name", "?"),
                    )
                    return None
                data: Any = content
                if content.startswith(("{", "[")):
                    try:
                        data = json.loads(content)
                    except Exception:  # noqa: BLE001
                        data = content
                return {
                    "status": "completed",
                    "degraded": False,
                    "intent": intent,
                    "skill_pack": skill.name,
                    "skill_score": score,
                    "result": data,
                    "model_used": getattr(llm, "model_name", "unknown"),
                }
            finally:
                if owns_db and db is not None:
                    db.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow %s 技能包执行失败，继续降级: %s", intent, exc)
            return None

    @staticmethod
    def _skill_implementation(skill: Any) -> dict[str, Any] | None:
        """取 Skill 当前版本的 implementation dict（含 skill_pack_path）。"""
        try:
            import json as _json

            raw = getattr(skill, "implementation_json", None)
            if raw:
                return _json.loads(raw)
            # 部分 ORM 实例可能只有 versions 关系
            vers = getattr(skill, "versions", None) or []
            if vers:
                return _json.loads(vers[-1].implementation_json or "{}")
        except Exception:  # noqa: BLE001
            return None
        return None

    def _notify_content_published(self, intent: str, result: dict[str, Any]) -> None:
        """内容发布成功 → 经 n8n 多渠道路由出站分发。

        打通『发布 → 分发』末段。工作流未注册 / 未启用 / Celery 不可达时静默跳过，
        绝不阻断执行主链路（"每个环节做正确的事"）。
        """
        try:
            from app.services.n8n.trigger import trigger_n8n_workflow

            payload = {
                "tenant_id": str(self.job.tenant_id),
                "job_id": str(self.job.id),
                "intent": intent,
                "event": "content_publish",
                "publish_result": result,
            }
            trigger_n8n_workflow.delay("content_publish_dispatch", payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow n8n 多渠道路由出站失败（已忽略）: %s", exc)

    def _exec_keyword_research(self, params: dict[str, Any]) -> dict[str, Any]:
        """关键词研究：接 ai_search_probe_service 真实 AI 搜索探测（Perplexity）。"""
        keyword = str(params.get("keyword") or params.get("query") or "")
        if not keyword:
            return self._degraded(
                "keyword_research", "缺少必填参数 keyword", params, keywords=[]
            )
        try:
            from app.services.ai_search_probe_service import run_ai_search_probes

            data = _run_coro(
                run_ai_search_probes(
                    keyword=keyword,
                    brand_name=str(params.get("brand_name") or params.get("brand") or ""),
                    product_category=str(
                        params.get("product_category") or params.get("industry") or ""
                    ),
                )
            )
            # 关键：configured_count==0 表示**没有任何探针被配置**（如缺
            # PERPLEXITY_API_KEY）。此时 data 非空但全是无意义的占位结果，
            # 若按成功返回就是"假成功"——比降级更危险（上层会拿到空数据
            # 却以为探测完成）。因此显式判为外部依赖未就绪 → 降级（并触发
            # 技能包兜底）。
            configured = 0
            if isinstance(data, dict):
                try:
                    configured = int(data.get("configured_count") or 0)
                except (TypeError, ValueError):
                    configured = 0
            if not data or configured == 0:
                return self._degraded(
                    "keyword_research",
                    "AI 搜索探测无可用探针（configured_count=0，缺 PERPLEXITY 等凭据）",
                    params,
                    keywords=[],
                )
            return {
                "status": "completed",
                "degraded": False,
                "keyword": keyword,
                "probe": data,
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "keyword_research",
                f"AI 搜索探测失败: {str(exc)[:200]}",
                params,
                keywords=[],
            )

    def _exec_content_creation(self, params: dict[str, Any]) -> dict[str, Any]:
        """内容创作：复用 AI 多语建站引擎生成站点内容 schema（本地，无外部依赖）。"""
        try:
            from app.services.ai_site_engine import AISiteEngine

            engine = AISiteEngine()
            schema = _run_coro(
                engine.generate_landing_page(
                    product_name=str(params.get("product_name") or params.get("title") or ""),
                    product_description=str(params.get("product_description") or params.get("description") or ""),
                    target_industry=str(params.get("industry") or "Industrial Equipment"),
                    target_market=str(params.get("target_market") or "Global"),
                    style_theme=str(params.get("style_theme") or "modern-b2b"),
                    contact_email=str(params.get("contact_email") or "sales@company.com"),
                )
            )
            return {
                "status": "completed",
                "degraded": False,
                "content_id": schema.get("site_id"),
                "schema": schema,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow content_creation 降级: %s", exc)
            return {
                "status": "completed",
                "degraded": True,
                "note": f"content_creation 真实服务不可用，降级占位: {str(exc)[:160]}",
                "params": params,
            }

    def _exec_seo_publish(self, params: dict[str, Any]) -> dict[str, Any]:
        """SEO 发布：接 content_master_publish_service 真实多平台发布。"""
        platform_ids = (
            params.get("platform_ids")
            or params.get("seo_platforms")
            or params.get("platforms")
            or []
        )
        if not platform_ids:
            return self._degraded(
                "seo_publish",
                "缺少必填参数 platform_ids（发布目标平台）",
                params,
                published_url="",
            )
        try:
            from app.services.content_master_publish_service import publish_auto_variants

            res = publish_auto_variants(
                self.db,
                tenant_id=str(self.job.tenant_id),
                platform_ids=[str(p) for p in platform_ids],
                draft_ids=params.get("draft_ids"),
                fallback_master_id=params.get("fallback_master_id"),
                primary_url=params.get("primary_url"),
                secondary_url=params.get("secondary_url"),
                utm=params.get("utm"),
                utm_campaign=params.get("utm_campaign"),
            )
            self._notify_content_published("seo_publish", res)
            return {
                "status": "completed",
                "degraded": False,
                "publish_result": res,
            }
        except Exception as exc:  # noqa: BLE001
            # 常见真实原因：no_drafts（无待发布母版）/ tenant_not_found
            return self._degraded(
                "seo_publish",
                f"发布服务执行失败: {str(exc)[:200]}",
                params,
                published_url="",
            )

    def _exec_page_creation(self, params: dict[str, Any]) -> dict[str, Any]:
        """页面创建：调用 AI 多语建站引擎生成 landing page schema（纯本地构造）。"""
        try:
            from app.services.ai_site_engine import AISiteEngine

            engine = AISiteEngine()
            schema = _run_coro(
                engine.generate_landing_page(
                    product_name=str(params.get("product_name") or params.get("title") or ""),
                    product_description=str(params.get("product_description") or params.get("description") or ""),
                    target_industry=str(params.get("industry") or "Industrial Equipment"),
                    target_market=str(params.get("target_market") or "Global"),
                    style_theme=str(params.get("style_theme") or "modern-b2b"),
                    contact_email=str(params.get("contact_email") or "sales@company.com"),
                )
            )
            return {
                "status": "completed",
                "degraded": False,
                "page_id": schema.get("site_id"),
                "schema": schema,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow page_creation 降级: %s", exc)
            return {
                "status": "completed",
                "degraded": True,
                "note": f"page_creation 真实服务不可用，降级占位: {str(exc)[:160]}",
                "params": params,
            }

    def _exec_seo_metadata(self, params: dict[str, Any]) -> dict[str, Any]:
        """SEO 元数据优化：调用 AI 建站引擎生成 JSON-LD SEO 元数据（本地）。"""
        try:
            from app.services.ai_site_engine import AISiteEngine

            engine = AISiteEngine()
            meta = engine.generate_seo_metadata(
                product_name=str(params.get("product_name") or params.get("title") or ""),
                industry=str(params.get("industry") or "Industrial Equipment"),
            )
            # G.8：generate_seo_metadata 目前是无实时 AI 优化引擎的静态模板
            # （仅填 name/category，无真实价格/库存/AI 字段），恒不抛异常。
            # 若仍报 degraded=False 属静默假成功；按 AGENTS「无真引擎须标降级」
            # 显式 degraded=True，保留静态 JSON-LD 作为可用占位而非真优化结果。
            return {
                "status": "completed",
                "degraded": True,
                "note": "seo_metadata 为静态模板占位（无实时 AI 优化引擎），非真优化结果",
                "optimized_fields": list(meta.keys()),
                "seo_metadata": meta,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow seo_metadata 降级: %s", exc)
            return {
                "status": "completed",
                "degraded": True,
                "note": f"seo_metadata 真实服务不可用，降级占位: {str(exc)[:160]}",
            }

    def _exec_multi_channel_publish(self, params: dict[str, Any]) -> dict[str, Any]:
        """多渠道分发：同样接 content_master_publish_service，一次性投放多平台。"""
        platform_ids = (
            params.get("platform_ids")
            or params.get("channels")
            or params.get("targets")
            or []
        )
        if not platform_ids:
            return self._degraded(
                "multi_channel_publish",
                "缺少必填参数 platform_ids/channels（分发目标渠道）",
                params,
                channels=[],
            )
        try:
            from app.services.content_master_publish_service import publish_auto_variants

            res = publish_auto_variants(
                self.db,
                tenant_id=str(self.job.tenant_id),
                platform_ids=[str(p) for p in platform_ids],
                draft_ids=params.get("draft_ids"),
                fallback_master_id=params.get("fallback_master_id"),
                primary_url=params.get("primary_url"),
                secondary_url=params.get("secondary_url"),
                utm=params.get("utm"),
                utm_campaign=params.get("utm_campaign"),
            )
            self._notify_content_published("multi_channel_publish", res)
            return {
                "status": "completed",
                "degraded": False,
                "channels": [str(p) for p in platform_ids],
                "publish_result": res,
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "multi_channel_publish",
                f"多渠道分发执行失败: {str(exc)[:200]}",
                params,
                channels=[],
            )

    def _exec_buyer_research(self, params: dict[str, Any]) -> dict[str, Any]:
        """目标买家调研：接外贸 customer_research 技能（AIEngine LLM 驱动）。"""
        company_name = str(params.get("company_name") or params.get("company") or "")
        country = str(params.get("country") or params.get("target_market") or "")
        industry = str(params.get("industry") or "")
        if not company_name:
            return self._degraded(
                "buyer_research", "缺少必填参数 company_name", params, buyers=[]
            )
        # 注意：SkillMeta.prompt_template.format(**params) 要求占位符齐全，
        # 缺任一键都会 KeyError —— 故此处显式补齐全部键。
        skill_params = {
            "company_name": company_name,
            "website": str(params.get("website") or ""),
            "country": country,
            "industry": industry,
        }
        try:
            _ensure_foreign_trade_skills()
            from app.services.foreign_trade import skill_registry

            result = _run_coro(skill_registry.execute("customer_research", skill_params))
            if not getattr(result, "success", False):
                return self._degraded(
                    "buyer_research",
                    f"customer_research 技能执行失败: {getattr(result, 'error', '未知')}"
                    "（常见原因：AI 服务未配置 LLM 凭据）",
                    params,
                    buyers=[],
                )
            return {
                "status": "completed",
                "degraded": False,
                "buyers": [{"company_name": company_name, "country": country}],
                "research": getattr(result, "data", None),
                "model_used": getattr(result, "model_used", None),
                "tokens_used": getattr(result, "tokens_used", 0),
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "buyer_research",
                f"buyer_research 执行异常: {str(exc)[:200]}",
                params,
                buyers=[],
            )

    def _exec_outreach_letter(self, params: dict[str, Any]) -> dict[str, Any]:
        """开发信生成：接外贸 cold_email 技能（AIEngine LLM 驱动）。"""
        company_name = str(params.get("company_name") or params.get("company") or "")
        if not company_name:
            return self._degraded(
                "outreach_letter", "缺少必填参数 company_name", params, letters=[]
            )
        # 同上：cold_email 模板占位符必须齐全，否则 format 抛 KeyError。
        skill_params = {
            "company_name": company_name,
            "country": str(params.get("country") or params.get("target_market") or ""),
            "industry": str(params.get("industry") or ""),
            "contact_name": str(params.get("contact_name") or "Purchasing Team"),
            "contact_title": str(params.get("contact_title") or "Procurement Manager"),
            "website": str(params.get("website") or ""),
            "product_advantages": str(
                params.get("product_advantages")
                or params.get("product_description")
                or params.get("description")
                or ""
            ),
        }
        try:
            _ensure_foreign_trade_skills()
            from app.services.foreign_trade import skill_registry

            result = _run_coro(skill_registry.execute("cold_email", skill_params))
            if not getattr(result, "success", False):
                return self._degraded(
                    "outreach_letter",
                    f"cold_email 技能执行失败: {getattr(result, 'error', '未知')}"
                    "（常见原因：AI 服务未配置 LLM 凭据）",
                    params,
                    letters=[],
                )
            return {
                "status": "completed",
                "degraded": False,
                "letters": [{"company_name": company_name}],
                "letter": getattr(result, "data", None),
                "model_used": getattr(result, "model_used", None),
                "tokens_used": getattr(result, "tokens_used", 0),
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "outreach_letter",
                f"outreach_letter 执行异常: {str(exc)[:200]}",
                params,
                letters=[],
            )

    def _exec_email_dispatch(self, params: dict[str, Any]) -> dict[str, Any]:
        """邮件发送与跟踪：调用统一邮件服务发送（SMTP/Resend 由 EmailService 决定）。"""
        try:
            from app.services.email_service import EmailService

            to = str(params.get("to") or params.get("recipient") or "")
            subject = str(params.get("subject") or "Notification")
            html = str(params.get("html") or params.get("body") or "")
            if not to:
                return {
                    "status": "completed",
                    "degraded": True,
                    "note": "email_dispatch 缺少收件人 to，跳过",
                    "sent_count": 0,
                }
            ok = EmailService(self.db).send_email(to=to, subject=subject, html=html)
            if not ok:
                # 邮件**并未真正发出**（未配置 SMTP/Resend 等），若仍报
                # degraded=False 就是"假成功"，上层会误以为已送达。
                return self._degraded(
                    "email_dispatch",
                    "邮件服务未配置或发送失败（邮件实际未发出）",
                    params,
                    sent_count=0,
                    delivered=False,
                )
            return {
                "status": "completed",
                "degraded": False,
                "sent_count": 1,
                "delivered": True,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeerFlow email_dispatch 降级: %s", exc)
            return {
                "status": "completed",
                "degraded": True,
            "note": f"email_dispatch 真实服务不可用，降级占位: {str(exc)[:160]}",
            "sent_count": 0,
        }

    def _exec_market_insight(self, params: dict[str, Any]) -> dict[str, Any]:
        """目标市场洞察：接 market_insight 技能（对标 Accio Work 市场洞察能力）。"""
        category = str(params.get("category") or params.get("product_name") or params.get("keyword") or "")
        target_market = str(
            params.get("target_market")
            or params.get("market")
            or params.get("country")
            or params.get("region")
            or ""
        )
        if not category or not target_market:
            return self._degraded(
                "market_insight",
                "缺少必填参数 category 与 target_market（缺一即无法定位洞察对象）",
                params,
                insight=None,
            )
        # SkillMeta.prompt_template.format(**params) 要求占位符齐全，缺任一键 KeyError，
        # 故此处显式补齐 input_schema 的全部键。
        skill_params = {
            "category": category,
            "target_market": target_market,
            "our_position": str(params.get("our_position") or "中等价位、可定制、交期稳定的中国制造商"),
            "horizon": str(params.get("horizon") or "未来 12 个月"),
        }
        try:
            _ensure_foreign_trade_skills()
            from app.services.foreign_trade import skill_registry

            result = _run_coro(skill_registry.execute("market_insight", skill_params))
            if not getattr(result, "success", False):
                return self._degraded(
                    "market_insight",
                    f"market_insight 技能执行失败: {getattr(result, 'error', '未知')}"
                    "（常见原因：AI 服务未配置 LLM 凭据）",
                    params,
                    insight=None,
                )
            return {
                "status": "completed",
                "degraded": False,
                "category": category,
                "target_market": target_market,
                "insight": getattr(result, "data", None),
                "model_used": getattr(result, "model_used", None),
                "tokens_used": getattr(result, "tokens_used", 0),
                # 洞察是模型推断而非一手数据，诚实标记原样透出，禁止上层当既成事实
                "human_verify_required": True,
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "market_insight",
                f"market_insight 执行异常: {str(exc)[:200]}",
                params,
                insight=None,
            )

    def _exec_supplier_compare(self, params: dict[str, Any]) -> dict[str, Any]:
        """供应商/同行比较排序卡：接 supplier_compare 技能（对标 Accio Work 比价链）。"""
        category = str(params.get("category") or params.get("product_name") or "")
        target_market = str(params.get("target_market") or params.get("market") or params.get("country") or "")
        raw_candidates = params.get("candidates") or params.get("suppliers") or params.get("subjects") or ""
        if isinstance(raw_candidates, (list, tuple)):
            # 允许上游直接给名单/对象列表（如 matching_engine 结果或人工填写的同行清单）
            candidates = "\n".join(
                item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
                for item in raw_candidates
            )
        else:
            candidates = str(raw_candidates).strip()
        if not category or not target_market or not candidates:
            return self._degraded(
                "supplier_compare",
                "缺少必填参数 category / target_market / candidates"
                "（候选主体必须由调用方给定，不允许模型杜撰公司名）",
                params,
                comparison=None,
            )
        skill_params = {
            "category": category,
            "target_market": target_market,
            "candidates": candidates,
            "criteria": str(params.get("criteria") or "价格、认证合规、交期、MOQ、售后与本地支持"),
            "our_position": str(params.get("our_position") or "中等价位、可定制、交期稳定的中国制造商"),
        }
        try:
            _ensure_foreign_trade_skills()
            from app.services.foreign_trade import skill_registry

            result = _run_coro(skill_registry.execute("supplier_compare", skill_params))
            if not getattr(result, "success", False):
                return self._degraded(
                    "supplier_compare",
                    f"supplier_compare 技能执行失败: {getattr(result, 'error', '未知')}"
                    "（常见原因：AI 服务未配置 LLM 凭据）",
                    params,
                    comparison=None,
                )
            return {
                "status": "completed",
                "degraded": False,
                "category": category,
                "target_market": target_market,
                "candidate_count": len([line for line in candidates.splitlines() if line.strip()]),
                "comparison": getattr(result, "data", None),
                "model_used": getattr(result, "model_used", None),
                "tokens_used": getattr(result, "tokens_used", 0),
                "human_verify_required": True,
            }
        except Exception as exc:  # noqa: BLE001
            return self._degraded(
                "supplier_compare",
                f"supplier_compare 执行异常: {str(exc)[:200]}",
                params,
                comparison=None,
            )

    def _exec_generic(self, subtask: SubTask) -> dict[str, Any]:
        """未知 intent 兜底：登记为 Paperclip 任务，等 Agent 心跳认领执行。

        2026-09-10 端到端真跑修的两处真 bug：
        1) 原来直接把 tenant_id 当 company_id 传下去。paperclip_tasks.company_id
           的外键指向 paperclip_companies.id（不是 tenants.id），而该表当时为空
           → 必然 ForeignKeyViolation。仓库里早有现成的
           get_or_create_company_for_tenant()，本就该用它做 tenant→company 映射。
        2) 原来 except 里不回滚，却还返回 status=completed。PG 里事务一旦
           aborted，同一 Session 上后续所有 SQL 全部级联报
           "This Session's transaction has been rolled back..."，于是节点真正的
           失败原因被 SQLAlchemy 的包装信息盖掉（本次 n3 排查被坑了一轮），
           同时把"入队失败"混成了"执行成功" —— 属于假成功，必须显式标 degraded。
        """
        from app.services.paperclip.orchestrator import (
            create_task,
            get_or_create_company_for_tenant,
        )

        try:
            company_id = get_or_create_company_for_tenant(
                self.db, str(self.job.tenant_id)
            )
            task_result = create_task(
                self.db,
                company_id=company_id,
                title=subtask.title,
                description=subtask.description,
                intent=subtask.intent,
            )
            return {
                "status": "completed",
                "degraded": True,
                "reason": (
                    f"intent={subtask.intent} 无专用执行器，"
                    "已登记为 Paperclip 任务，待 Agent 心跳认领执行（本节点未产出业务结果）"
                ),
                "paperclip_task": task_result,
            }
        except Exception as exc:
            # 必须先回滚：否则脏事务会污染同一 Session，后续状态回写全部报错
            try:
                self.db.rollback()
            except Exception:  # noqa: BLE001 — 回滚本身失败不再连坐
                pass
            logger.exception(
                "DeerFlow generic 兜底入队失败: job=%s subtask=%s intent=%s",
                self.job.id, subtask.id, subtask.intent,
            )
            return self._degraded(
                subtask.intent or "generic",
                f"Paperclip 兜底入队失败：{type(exc).__name__}: {str(exc)[:160]}",
                subtask.parameters,
            )

    # ------------------------------------------------------------------
    # 重试与 Checkpoint
    # ------------------------------------------------------------------
    def _maybe_retry(
        self,
        subtask: SubTask,
        failed_result: SubTaskResult,
    ) -> Optional[SubTaskResult]:
        """检查是否需要重试并执行重试。"""
        # 从 checkpoint 获取当前重试次数
        retry_count = self._get_subtask_retry_count(subtask.id)
        if retry_count >= subtask.max_retries:
            logger.warning(
                "Subtask retry exhausted: job=%s subtask=%s retries=%d",
                self.job.id, subtask.id, retry_count,
            )
            return None

        logger.info(
            "Retrying subtask: job=%s subtask=%s attempt=%d/%d",
            self.job.id, subtask.id, retry_count + 1, subtask.max_retries,
        )
        # 执行重试
        return self.execute_subtask(subtask)

    def _get_subtask_retry_count(self, subtask_id: str) -> int:
        """获取子任务已重试次数。"""
        checkpoint = self._load_checkpoint()
        results = checkpoint.get("subtask_results", {})
        subtask_data = results.get(subtask_id, {})
        return subtask_data.get("retry_count", 0)

    def _save_subtask_result(self, subtask: SubTask, result: SubTaskResult) -> None:
        """保存子任务执行结果到 checkpoint。"""
        checkpoint = self._load_checkpoint()
        results = checkpoint.setdefault("subtask_results", {})
        existing = results.get(subtask.id, {})
        retry_count = existing.get("retry_count", 0)
        results[subtask.id] = {
            **result.to_dict(),
            "retry_count": retry_count + (0 if result.success else 1),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_checkpoint(checkpoint)

    def _load_checkpoint(self) -> dict[str, Any]:
        """加载 checkpoint 数据。"""
        if self.job.payload_json:
            try:
                data = json.loads(self.job.payload_json)
                return data.get("checkpoint", {})
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    def _save_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        """保存 checkpoint 到任务 payload_json。"""
        payload: dict[str, Any] = {}
        if self.job.payload_json:
            try:
                payload = json.loads(self.job.payload_json)
            except (json.JSONDecodeError, TypeError):
                pass
        payload["checkpoint"] = checkpoint
        self.job.payload_json = json.dumps(payload, ensure_ascii=False)
        self.db.commit()


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------

class SubTaskExecutionError(Exception):
    """子任务执行异常。"""
    def __init__(
        self,
        message: str,
        subtask_id: str = "",
        result: Optional[SubTaskResult] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param subtask_id: 参数 subtask_id
        :param result: 参数 result
        :return: 返回处理结果。
        """
        super().__init__(message)
        self.subtask_id = subtask_id
        self.result = result
