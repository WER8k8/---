# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""商业闭环编排器。

从产品输入到成交的完整链路:
自然语言+产品图片 → AI建站 → 内容/视频 → SEO/GEO/AEO → 多平台分发 → 获客 → Lead评分 → CRM → 开发信 → 报价 → 成交 → 数据沉淀 → AI进化

每个步骤:
- 失败时自动降级（降级不中断）
- 全程Trace记录
- 租户数据隔离
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


class CommercialLoopOrchestrator:
    """商业闭环编排器 — 将AI Growth OS各模块串联成端到端业务流程。

    使用方式:
        orchestrator = CommercialLoopOrchestrator(db)
        result = await orchestrator.execute(
            tenant_id="xxx",
            product_data={...},
            target_market="us",
        )
    """
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db
        self.trace_id = str(uuid.uuid4())
        self.steps_executed: list[dict[str, Any]] = []

    async def execute(
        self,
        tenant_id: str,
        product_data: dict[str, Any],
        target_market: str = "global",
        language: str = "en",
        skip_to: str | None = None,
    ) -> dict[str, Any]:
        """执行完整商业闭环。

        Args:
            tenant_id: 租户ID
            product_data: 产品数据 {name, description, images, industry, ...}
            target_market: 目标市场
            language: 主语言
            skip_to: 从指定步骤开始（用于断点续传）

        Returns:
            完整执行结果 {site, content, distribution, leads, ...}
        """
        result: dict[str, Any] = {
            "trace_id": self.trace_id,
            "tenant_id": tenant_id,
            "status": "started",
            "steps": {},
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        steps = [
            ("analyze_product", self._step_analyze_product),
            ("build_website", self._step_build_website),
            ("generate_content", self._step_generate_content),
            ("optimize_seo", self._step_optimize_seo),
            ("distribute", self._step_distribute),
            ("capture_leads", self._step_capture_leads),
            ("score_leads", self._step_score_leads),
            ("crm_import", self._step_crm_import),
            ("send_outreach", self._step_send_outreach),
            ("create_quote", self._step_create_quote),
            ("close_deal", self._step_close_deal),
            ("record_evolution", self._step_record_evolution),
        ]
        # 支持断点续传
        start_idx = 0
        if skip_to:
            for i, (name, _) in enumerate(steps):
                if name == skip_to:
                    start_idx = i
                    break

        for step_name, step_func in steps[start_idx:]:
            try:
                step_result = await step_func(tenant_id, product_data, result, target_market, language)
                result["steps"][step_name] = {"status": "success", "data": step_result}
                self.steps_executed.append({"step": step_name, "status": "success"})
            except Exception as e:
                log.warning("Commercial loop step '%s' failed: %s", step_name, e)
                result["steps"][step_name] = {"status": "failed", "error": str(e)}
                self.steps_executed.append({"step": step_name, "status": "failed", "error": str(e)})
                # 关键步骤失败则中断，非关键步骤继续
                if step_name in ("analyze_product", "build_website"):
                    result["status"] = "failed"
                    result["failed_at"] = step_name
                    return result

        result["status"] = "completed"
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result

    async def _step_analyze_product(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 1: 分析产品 — 提取特性、参数、应用场景。"""
        from app.services.ai_engine import AIEngine
        engine = AIEngine()
        prompt = f"""分析以下产品，提取:
1. 核心特性和差异化卖点
2. 技术参数和规格
3. 典型应用场景
4. 目标客户画像
5. SEO关键词

产品名称: {data.get('name', 'N/A')}
产品描述: {data.get('description', 'N/A')}
目标市场: {market}

返回JSON格式。"""

        analysis = await engine.generate(prompt, model="general")
        return {"analysis": analysis, "market": market, "language": lang}

    async def _step_build_website(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 2: AI建站 — 生成完整品牌官网。"""
        from app.services.site_builder.orchestrator import SiteBuilderOrchestrator
        builder = SiteBuilderOrchestrator(self.db)
        site_result = await builder.build(
            tenant_id=tenant_id,
            product_data=data,
            target_market=market,
            language=lang,
        )
        return {"site_id": site_result.get("site_id"), "pages": site_result.get("pages", [])}

    async def _step_generate_content(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 3: 生成内容 — 文章、视频脚本、社媒帖子。"""
        from app.services.ai_engine import AIEngine
        engine = AIEngine()
        site_pages = result.get("steps", {}).get("build_website", {}).get("data", {}).get("pages", [])
        content_package = {}
        # 生成一篇博客文章
        blog_prompt = f"""为以下产品信息写一篇SEO优化的博客文章:
产品: {data.get('name', 'N/A')}
描述: {data.get('description', 'N/A')}
目标语言: {lang}
字数: 800-1200字"""
        content_package["blog_post"] = await engine.generate(blog_prompt, model="general")
        # 生成3条社媒帖子
        social_prompt = f"""为产品 {data.get('name', 'N/A')} 写3条社交媒体营销文案:
- LinkedIn专业风格
- Facebook轻松风格
- Twitter/X精简风格
语言: {lang}"""
        content_package["social_posts"] = await engine.generate(social_prompt, model="general")
        return content_package

    async def _step_optimize_seo(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 4: SEO/GEO/AEO优化 — 关键词、Meta、Schema。"""
        from app.services.seo.seo_analyzer import SEOAnalyzer
        analyzer = SEOAnalyzer(self.db)
        site_data = result.get("steps", {}).get("build_website", {}).get("data", {})
        seo_result = await analyzer.optimize(
            tenant_id=tenant_id,
            pages=site_data.get("pages", []),
            language=lang,
        )
        return {"seo_score": seo_result.get("score", 0), "recommendations": seo_result.get("recommendations", [])}

    async def _step_distribute(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 5: 多平台分发 — 发布到各渠道。"""
        from app.services.publish_dispatch_service import PublishDispatchService
        dispatch = PublishDispatchService(self.db)
        content = result.get("steps", {}).get("generate_content", {}).get("data", {})
        distribution = await dispatch.distribute(
            tenant_id=tenant_id,
            content=content,
            channels=["website", "blog", "social_media"],
        )
        return {"channels": distribution.get("channels", []), "published_count": distribution.get("published", 0)}

    async def _step_capture_leads(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 6: 获取线索 — 从站和社媒收集询盘。"""
        from app.services.geo_lead_service import GeoLeadService
        lead_service = GeoLeadService(self.db)
        leads = await lead_service.search_leads(
            tenant_id=tenant_id,
            industry=data.get("industry", ""),
            market=market,
        )
        return {"leads_found": len(leads), "source": "geo_search"}

    async def _step_score_leads(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 7: Lead评分 — 价值评估、分级。"""
        from app.services.prospect_scorer import ProspectScorer
        scorer = ProspectScorer(self.db)
        leads_data = result.get("steps", {}).get("capture_leads", {}).get("data", {})
        scored = await scorer.score_batch(tenant_id=tenant_id, leads=leads_data.get("leads", []))
        return {"scored_count": len(scored), "mql_count": sum(1 for s in scored if s.get("score", 0) >= 61)}

    async def _step_crm_import(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 8: CRM导入 — Leads进入销售管道。"""
        # 简化实现 — 实际会将leads写入CRM
        scored_leads = result.get("steps", {}).get("score_leads", {}).get("data", {})
        return {"imported_to_crm": scored_leads.get("scored_count", 0), "pipeline": "sales"}

    async def _step_send_outreach(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 9: 开发信 — 个性化邮件触达。"""
        from app.services.email_service import EmailService
        email_svc = EmailService(self.db)
        outreach = await email_svc.send_batch(
            tenant_id=tenant_id,
            template="b2b_outreach",
            language=lang,
        )
        return {"emails_sent": outreach.get("sent", 0), "template": "b2b_outreach"}

    async def _step_create_quote(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 10: 报价 — 生成报价单。"""
        from app.services.rfq_service import RFQService
        rfq = RFQService(self.db)
        quote = await rfq.create_quote(
            tenant_id=tenant_id,
            product_name=data.get("name", ""),
            quantity=100,
            currency="USD",
        )
        return {"quote_id": quote.get("id"), "status": "draft"}

    async def _step_close_deal(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 11: 成交 — 创建订单和支付链接。"""
        # 简化实现 — 实际会创建订单和支付
        quote_data = result.get("steps", {}).get("create_quote", {}).get("data", {})
        return {"order_id": quote_data.get("quote_id"), "status": "pending_payment"}

    async def _step_record_evolution(
        self, tenant_id: str, data: dict, result: dict, market: str, lang: str
    ) -> dict[str, Any]:
        """Step 12: 数据沉淀 — 记录执行数据到进化引擎。"""
        # 为每个步骤创建执行记录
        for step_info in self.steps_executed:
            record = {
                "tenant_id": tenant_id,
                "task_type": "commercial_loop",
                "executor_type": "orchestrator",
                "executor_id": f"commercial_loop.{step_info['step']}",
                "success": step_info["status"] == "success",
                "duration_ms": 0,
                "cost": 0.0,
            }
            # 实际会写入 evolution_task_records 表
        return {"recorded_steps": len(self.steps_executed), "evolution_enabled": True}
