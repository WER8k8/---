"""AccioWork 原生桥 — 无 ai_engine 包时使用 UBrain 卖货服务。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_BUILTIN_SKILLS = [
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

_SKILL_LABELS = {s["id"]: s["name"] for s in _BUILTIN_SKILLS}

_native_engine: "NativeAccioWorkEngine | None" = None
_history: list[dict[str, Any]] = []


class NativeAccioWorkEngine:
    """UBrain 原生执行层 — 对接 accio_sales_service。"""
    engine_id = "ubrain_native_acciowork"
    def list_skills(self, category: str | None = None) -> list[dict[str, Any]]:
        """list_skills。

        参数说明：
        :param self: 参数 self
        :param category: 参数 category
        :return: 返回处理结果。
        """
        skills = list(_BUILTIN_SKILLS)
        if category:
            skills = [s for s in skills if s["category"] == category]
        return skills

    def get_execution_history(
        self,
        *,
        limit: int = 20,
        skill_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """get_execution_history。

        参数说明：
        :param self: 参数 self
        :param limit: 参数 limit
        :param skill_id: 参数 skill_id
        :return: 返回处理结果。
        """
        rows = list(_history)
        if skill_id:
            rows = [r for r in rows if r.get("skill_id") == skill_id]
        return rows[-limit:]

    async def execute_skill(self, skill_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """execute_skill。

        参数说明：
        :param self: 参数 self
        :param skill_id: 参数 skill_id
        :param params: 参数 params
        :return: 返回处理结果。
        """
        params = dict(params or {})
        db = params.pop("_db", None)
        tenant_id = params.pop("_tenant_id", None)
        ts = datetime.now(timezone.utc).isoformat()
        if skill_id == "customer_finder":
            result = await self._run_customer_finder(db, tenant_id, params, ts)
        elif skill_id == "auto_negotiator":
            result = await self._run_auto_negotiator(db, tenant_id, params, ts)
        elif skill_id == "email_automation":
            result = await self._run_email_automation(db, tenant_id, params, ts)
        else:
            result = {
                "skill_id": skill_id,
                "skill_name": _SKILL_LABELS.get(skill_id, skill_id),
                "status": "completed",
                "results": {"message": "native_bridge_stub", "params": params},
                "timestamp": ts,
                "engine": self.engine_id,
            }

        _history.append({"skill_id": skill_id, "result": result, "timestamp": ts})
        return result

    async def execute_instruction(self, instruction: dict[str, Any]) -> dict[str, Any]:
        """execute_instruction。

        参数说明：
        :param self: 参数 self
        :param instruction: 参数 instruction
        :return: 返回处理结果。
        """
        skill_id = str(instruction.get("skill_id") or instruction.get("action") or "general")
        return await self.execute_skill(skill_id, instruction.get("params") or instruction)

    async def get_execution_status(self, execution_id: str) -> dict[str, Any]:
        """get_execution_status。

        参数说明：
        :param self: 参数 self
        :param execution_id: 参数 execution_id
        :return: 返回处理结果。
        """
        for row in reversed(_history):
            if execution_id in str(row.get("result", {})):
                return {"execution_id": execution_id, "status": "completed", "engine": self.engine_id}
        return {"execution_id": execution_id, "status": "unknown", "engine": self.engine_id}

    async def _run_customer_finder(
        self,
        db: Any,
        tenant_id: str | None,
        params: dict[str, Any],
        ts: str,
    ) -> dict[str, Any]:
        """_run_customer_finder。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param params: 参数 params
        :param ts: 参数 ts
        :return: 返回处理结果。
        """
        keywords = params.get("keywords") or []
        search_source = params.get("search_source") or "all"
        if db is not None and tenant_id:
            industry = params.get("industry")
            countries = params.get("countries") or []
            max_results = int(params.get("max_results") or 50)
            pack = self._resolve_customer_finder_pack(
                db,
                tenant_id=str(tenant_id),
                search_source=search_source,
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
            customers = self._build_customer_records(
                pack=pack,
                max_results=max_results,
                industry=industry,
                ts=ts,
            )
            find_mode = pack.get("mode") or (
                "reddit_prospect_discovery" if search_source == "reddit" else "accio_buyer_discovery"
            )
            return {
                "skill_id": "customer_finder",
                "skill_name": "客户开发",
                "status": "completed",
                "find_mode": find_mode,
                "probe_mode": pack.get("probe_mode"),
                "results": {
                    "customers": customers,
                    "total_found": len(customers),
                    "mode": find_mode,
                    "probe_mode": pack.get("probe_mode"),
                    "email_enrichment": pack.get("email_enrichment"),
                    "human_verify_required": bool(pack.get("human_verify_required", True)),
                    "disclaimer": pack.get("disclaimer"),
                    "region": pack.get("region"),
                    "category": pack.get("category"),
                    "criteria_used": {
                        "keywords": keywords,
                        "countries": countries,
                        "max_results": max_results,
                        "industry": industry,
                        "search_source": search_source,
                    },
                },
                "timestamp": ts,
                "engine": self.engine_id,
            }

    def _resolve_customer_finder_pack(
        self,
        db: Any,
        tenant_id: str,
        search_source: str,
        keywords: list[str],
        countries: list[str],
        industry: str | None,
        max_results: int,
    ) -> dict[str, Any]:
        """根据 search_source 选择并调用对应的客户发现服务，返回 pack。"""
        if search_source == "reddit":
            from app.services.ubrain.reddit_prospect_service import find_reddit_prospects
            pack = find_reddit_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "linkedin":
            from app.services.ubrain.linkedin_prospect_service import find_linkedin_prospects
            pack = find_linkedin_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "tiktok":
            from app.services.ubrain.tiktok_prospect_service import find_tiktok_prospects
            pack = find_tiktok_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "google":
            from app.services.ubrain.google_prospect_service import find_google_prospects
            pack = find_google_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "quora":
            from app.services.ubrain.quora_prospect_service import find_quora_prospects
            pack = find_quora_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "whatsapp":
            from app.services.ubrain.whatsapp_prospect_service import find_whatsapp_prospects
            pack = find_whatsapp_prospects(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        elif search_source == "all" and keywords:
            pack = self._run_multi_channel_search(
                db,
                tenant_id=str(tenant_id),
                keywords=keywords,
                countries=countries,
                industry=industry,
                max_results=max_results,
            )
        else:
            pack = self._build_fallback_pack(
                db,
                tenant_id=tenant_id,
                keywords=keywords,
                countries=countries,
                industry=industry,
            )
        return pack

    def _build_fallback_pack(
        self,
        db: Any,
        tenant_id: str,
        keywords: list[str],
        countries: list[str],
        industry: str | None,
    ) -> dict[str, Any]:
        """未匹配到具体渠道时回退到 accio 买家发现服务。"""
        from app.services.ubrain.accio_sales_service import find_buyer_prospects
        message_parts = [str(k).strip() for k in keywords if str(k).strip()]
        if industry:
            message_parts.append(str(industry))
        if countries:
            message_parts.append(" ".join(str(c) for c in countries))
        message = " ".join(message_parts) or "find buyers insulation export"
        return find_buyer_prospects(
            db,
            tenant_id=str(tenant_id),
            message=message,
            memory={"product_category": industry or "建材"},
        )

    def _build_customer_records(
        self,
        pack: dict[str, Any],
        max_results: int,
        industry: str | None,
        ts: str,
    ) -> list[dict[str, Any]]:
        """将 pack 中的 prospects 转换为统一的 customer 记录列表。"""
        prospects = pack.get("prospects") or pack.get("buyers") or []
        customers = []
        for i, p in enumerate(prospects[:max_results]):
            if not isinstance(p, dict):
                continue
            fit_score = p.get("fit_score")
            if fit_score is None:
                fit_score = p.get("score")
            try:
                score = float(fit_score if fit_score is not None else 70)
            except (TypeError, ValueError):
                score = 70.0
            if score <= 1:
                score *= 100
            title = (
                p.get("title")
                or p.get("company_name")
                or p.get("company")
                or p.get("name")
                or ""
            )
            customers.append(
                {
                    "customer_id": p.get("id") or f"cust_{i + 1:03d}",
                    "id": p.get("id") or f"cust_{i + 1:03d}",
                    "name": title,
                    "company_name": p.get("company") or p.get("company_name") or title,
                    "company": p.get("company") or p.get("company_name") or title,
                    "email": p.get("email") or "",
                    "phone": p.get("phone") or "",
                    "website": p.get("evidence_url") or p.get("website") or "",
                    "evidence_url": p.get("evidence_url") or p.get("website") or "",
                    "country": p.get("country_code") or p.get("country") or "",
                    "country_code": p.get("country_code") or p.get("country") or "",
                    "industry": industry or pack.get("category") or "",
                    "buyer_type": p.get("buyer_type") or "",
                    "score": round(score, 1),
                    "fit_score": int(score),
                    "status": "new",
                    "verification_status": p.get("verification_status") or "待核实候选",
                    "notes": p.get("notes") or "",
                    "lastContact": ts[:10],
                }
            )
        return customers
        kw = keywords[0] if keywords else "export"
        return {
            "skill_id": "customer_finder",
            "skill_name": "客户开发",
            "status": "not_configured",
            "error_code": "CUSTOMER_FINDER_NOT_CONFIGURED",
            "message": "请登录租户后使用客户开发；未配置上游时不会返回演示客户。",
            "results": {
                "customers": [],
                "total_found": 0,
                "criteria_used": {"keywords": keywords, "countries": params.get("countries") or []},
            },
            "timestamp": ts,
            "engine": self.engine_id,
        }

    def _run_multi_channel_search(
        self,
        db: Any,
        tenant_id: str,
        keywords: list[str],
        countries: list[str],
        industry: str | None,
        max_results: int,
    ) -> dict[str, Any]:
        """多渠道并行搜索 — 从 Reddit、LinkedIn、TikTok、Google、Quora、WhatsApp 同时获取线索"""
        from app.services.ubrain.reddit_prospect_service import fetch_reddit_prospects
        from app.services.ubrain.linkedin_prospect_service import fetch_linkedin_prospects
        from app.services.ubrain.tiktok_prospect_service import fetch_tiktok_prospects
        from app.services.ubrain.google_prospect_service import fetch_google_prospects
        from app.services.ubrain.quora_prospect_service import fetch_quora_prospects
        from app.services.ubrain.whatsapp_prospect_service import fetch_whatsapp_prospects
        channels = [
            ("reddit", fetch_reddit_prospects),
            ("linkedin", fetch_linkedin_prospects),
            ("tiktok", fetch_tiktok_prospects),
            ("google", fetch_google_prospects),
            ("quora", fetch_quora_prospects),
            ("whatsapp", fetch_whatsapp_prospects),
        ]
        all_prospects: list[dict[str, Any]] = []
        per_channel = max_results // len(channels)
        if per_channel < 1:
            per_channel = 1

        all_prospects = self._fetch_and_persist_channel_prospects(
            db,
            tenant_id=tenant_id,
            channels=channels,
            keywords=keywords,
            countries=countries,
            industry=industry,
            max_results=max_results,
            per_channel=per_channel,
        )
        from app.services.ubrain.tenant_memory_service import record_tool_use
        record_tool_use(
            db,
            tenant_id,
            "find_buyers",
            context_patch={
                "preferred_regions": [countries[0]] if countries else [],
                "product_category": industry or "建材",
                "last_find_mode": "multi_channel_prospect_discovery",
            },
        )
        industry_names = {
            "construction": "建筑工程",
            "insulation": "保温材料",
            "building_materials": "建材",
            "hardware": "五金配件",
            "decoration": "装饰材料",
        }
        return {
            "mode": "multi_channel_prospect_discovery",
            "region": countries[0] if countries else "",
            "category": industry_names.get(industry or "construction", "建材"),
            "count": len(all_prospects),
            "prospects": all_prospects,
            "human_verify_required": True,
            "disclaimer": "候选来自多渠道综合搜索，联系方式为推测生成；均为「待核实候选」，联系前请人工核实。",
            "source": "multi_channel",
            "next_step": "对高 fit 客户生成开发信（outreach_letter_pack），发送前需您确认。",
        }

    def _fetch_and_persist_channel_prospects(
        self,
        db: Any,
        tenant_id: str,
        channels: list[tuple[str, Any]],
        keywords: list[str],
        countries: list[str],
        industry: str | None,
        max_results: int,
        per_channel: int,
    ) -> list[dict[str, Any]]:
        """并行获取各渠道线索、排序截断并落库，返回最终 prospects 列表。"""
        all_prospects: list[dict[str, Any]] = []
        for channel_name, fetcher in channels:
            try:
                pack = fetcher(
                    tenant_id=tenant_id,
                    keywords=keywords,
                    countries=countries,
                    industry=industry,
                    max_results=per_channel,
                )
                prospects = pack.get("prospects") or []
                for p in prospects:
                    p["source"] = channel_name
                all_prospects.extend(prospects)
            except Exception as e:
                logger.warning(f"Channel {channel_name} failed: {e}")

        all_prospects.sort(key=lambda x: x.get("fit_score", 0), reverse=True)
        all_prospects = all_prospects[:max_results]
        for p in all_prospects:
            row = {
                "id": str(__import__("uuid").uuid4()),
                "tenant_id": tenant_id,
                "region_label": p.get("country", ""),
                "country_code": (p.get("country_code") or "XX")[:8],
                "buyer_type": (p.get("buyer_type") or "importer")[:32],
                "title": (p.get("title") or "Multi-channel prospect")[:200],
                "fit_score": int(p.get("fit_score") or 65),
                "suggested_channel": "email",
                "notes": (
                    f"{p.get('notes') or ''} source={p.get('source', '')}"
                    + f" evidence={p.get('evidence_url') or ''}"
                )[:2000],
                "status": "discovered",
                "source_tool": f"{p.get('source', '')}_prospect_discovery",
            }
            db.add(__import__("app.models.ubrain_accio").models.ubrain_accio.BuyerProspectLead(**row))

        db.commit()
        return all_prospects

    async def _run_auto_negotiator(
        self,
        db: Any,
        tenant_id: str | None,
        params: dict[str, Any],
        ts: str,
    ) -> dict[str, Any]:
        """_run_auto_negotiator。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param params: 参数 params
        :param ts: 参数 ts
        :return: 返回处理结果。
        """
        action = params.get("action") or "process_inquiry"
        if db is not None and tenant_id:
            from app.services.ubrain.accio_sales_service import negotiation_draft
            from app.services.ubrain.tenant_memory_service import get_memory
            memory = get_memory(db, str(tenant_id))
            msg = params.get("customer_name") or "customer inquiry"
            pack = negotiation_draft(msg, params, memory)
            return {
                "skill_id": "auto_negotiator",
                "skill_name": "自动谈单",
                "status": "completed",
                "results": {
                    "action": action,
                    "session_id": f"neg_{ts[:10].replace('-', '')}",
                    "customer_name": params.get("customer_name", ""),
                    "reply": pack.get("reply") or pack.get("draft") or "",
                    "status": "initiated",
                },
                "timestamp": ts,
                "engine": self.engine_id,
            }

        return {
            "skill_id": "auto_negotiator",
            "skill_name": "自动谈单",
            "status": "not_configured",
            "error_code": "AI_REPLY_NOT_CONFIGURED",
            "message": "请登录租户后使用自动谈单；未配置话术引擎时不会返回模板冒充智能回复。",
            "results": {
                "action": action,
                "session_id": None,
                "status": "not_configured",
                "reply": "",
            },
            "timestamp": ts,
            "engine": self.engine_id,
        }

    async def _run_email_automation(
        self,
        db: Any,
        tenant_id: str | None,
        params: dict[str, Any],
        ts: str,
    ) -> dict[str, Any]:
        """_run_email_automation。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param params: 参数 params
        :param ts: 参数 ts
        :return: 返回处理结果。
        """
        action = params.get("action") or "generate_email"
        if db is not None and tenant_id:
            from app.services.tenant_product_profile_service import ProductProfileRequiredError
            from app.services.ubrain.accio_sales_service import outreach_letter_pack
            cust = params.get("customer_data") or {}
            msg = str(cust.get("company_name") or cust.get("product") or "outreach")
            try:
                pack = outreach_letter_pack(db, tenant_id=str(tenant_id), message=msg)
            except ProductProfileRequiredError as exc:
                return {
                    "skill_id": "email_automation",
                    "skill_name": "开发信撰写",
                    "status": "blocked",
                    "error_code": exc.code,
                    "results": {
                        "message": str(exc),
                        "action": action,
                    },
                    "timestamp": ts,
                    "engine": self.engine_id,
                }
            letters = pack.get("letters") or []
            first = letters[0] if letters else {}
            return {
                "skill_id": "email_automation",
                "skill_name": "开发信撰写",
                "status": "completed",
                "results": {
                    "email_id": f"email_{ts[:10].replace('-', '')}",
                    "subject": first.get("subject") or "Partnership inquiry",
                    "body": first.get("body") or first.get("content") or "",
                    "recipient": (params.get("customer_data") or {}).get("email", ""),
                    "status": "draft",
                    "action": action,
                },
                "timestamp": ts,
                "engine": self.engine_id,
            }

        cust = params.get("customer_data") or {}
        return {
            "skill_id": "email_automation",
            "skill_name": "开发信撰写",
            "status": "completed",
            "results": {
                "email_id": "email_demo",
                "subject": f"Partnership — {cust.get('company_name', 'Partner')}",
                "body": "Dear partner, we supply export-grade building materials.",
                "recipient": cust.get("email", ""),
                "status": "draft",
                "action": action,
            },
            "timestamp": ts,
            "engine": self.engine_id,
        }


def get_native_acciowork_engine() -> NativeAccioWorkEngine:
    """get_native_acciowork_engine。
    :return: 返回处理结果。
    """
    global _native_engine
    if _native_engine is None:
        _native_engine = NativeAccioWorkEngine()
        logger.info("AccioWork 原生桥接引擎已启用（无 ai_engine 包）")
    return _native_engine
