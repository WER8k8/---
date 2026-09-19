# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""UBrain v1 — 意图识别 + 工具调用（走现有 API 数据或 M0 规则）。"""

from __future__ import annotations

import logging
from collections import Counter
import re
from typing import Any

from sqlalchemy.orm import Session

from app.services.inquiries_unified_service import InquiriesUnifiedService
from app.services.ubrain.accio_sales_service import (
    find_buyer_prospects,
    negotiation_draft,
    outreach_letter_pack,
)
from app.services.ubrain.chat_context_service import (
    build_situational_context,
    refine_intent,
)
from app.services.ubrain.general_smart_reply import (
    build_smart_general_reply,
    expand_strategy_choice,
)
from app.services.ubrain.deerflow_job_service import enqueue_job, run_job
from app.services.hermes.brand_guard import sanitize_public_copy
from app.services.hermes.flywheel_workflow import run_closed_loop_flywheel
from app.services.ubrain.export_feasibility_reply import (
    build_export_feasibility_reply,
    memory_patch_after_export,
)
from app.services.ubrain.tenant_memory_service import get_memory, record_tool_use
from app.services.trade_intel_service import (
    DISCLAIMER,
    blue_ocean,
    export_feasibility,
    hs_lookup,
)

_CAPABILITY_QUESTION_RE = re.compile(
    r"(你能干嘛|你会什么|你会做什么|你会干|能干什么|你会干什么|"
    r"你能做什么|能帮我什么|有什么功能|哪些功能|功能列表|"
    r"你是谁|你是做什么|介绍一下|介绍你自己|"
    r"怎么用|如何使用|有啥用|有什么用|"
    r"^(你好|您好|嗨|hello|hi|在吗|在不在)[\?？!！。呀啊]*$|"
    r"^(hello|hi)\b|"
    r"who\s+are\s+you|"
    r"what\s+can\s+you\s+do|"
    r"\bhelp\b)",
    re.I,
)

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# 目标市场识别：只收通用地理名，不收品类词。
# 品类一律走「用户明说」或「租户产品档案」，不把建材等行业词硬编进内核
# （对齐 AEOS 核心观点 1：去行业化通用 B2B 抽象，行业只是参数化 Profile）。
_MARKET_ALIASES: tuple[str, ...] = (
    "沙特阿拉伯", "阿联酋", "迪拜", "阿曼", "卡塔尔", "科威特", "巴林",
    "沙特", "印尼", "马来西亚", "马来", "澳洲",
    "哈萨克斯坦", "乌兹别克斯坦", "巴基斯坦", "孟加拉", "斯里兰卡",
    "尼日利亚", "南非", "埃及", "摩洛哥", "肯尼亚", "加纳", "坦桑尼亚",
    "墨西哥", "巴西", "哥伦比亚", "智利", "秘鲁", "阿根廷",
    "美国", "加拿大", "德国", "法国", "英国", "意大利", "西班牙", "荷兰",
    "波兰", "俄罗斯", "日本", "韩国", "新加坡", "马来西亚", "印度尼西亚",
    "泰国", "越南", "菲律宾", "印度", "澳大利亚", "新西兰",
    "中东", "东南亚", "南亚", "中亚", "拉美", "拉丁美洲", "非洲",
    "欧洲", "北美", "海湾", "GCC", "SASO",
)

_COMPANY_TOKEN_RE = re.compile(
    r"[\u4e00-\u9fa5A-Za-z0-9&.\-]{2,40}?[\s]{0,2}"
    r"(?:公司|集团|有限公司|股份|工业|实业|Co\.?|Corp\.?|Inc\.?|Ltd\.?|LLC|GmbH|S\.A\.|Group)",
    re.I,
)


def _extract_insight_subject(message: str) -> dict[str, Any]:
    """从自然语言里抽 品类 / 目标市场 / 候选主体，供市场洞察与供应商比较使用。

    抽不到就返回空值，由调用方明确向用户追问；绝不替用户编一个品类或市场。
    """
    text = (message or "").strip()
    out: dict[str, Any] = {"category": "", "target_market": "", "candidates": ""}
    if not text:
        return out

    # 按别名长度倒序匹配：否则「印度尼西亚」会被「印度」抢先命中，
    # 「沙特阿拉伯」会退化成「沙特」。别表写顺序不再敏感。
    market = next(
        (alias for alias in sorted(_MARKET_ALIASES, key=len, reverse=True) if alias in text),
        "",
    )
    out["target_market"] = market

    candidates = [c.strip() for c in _COMPANY_TOKEN_RE.findall(text) if len(c.strip()) >= 3]
    # 去重保序，至少两家才构成"比较"
    uniq: list[str] = []
    for cand in candidates:
        if cand not in uniq:
            uniq.append(cand)
    if len(uniq) >= 2:
        out["candidates"] = "\n".join(uniq)

    # 品类：优先「把 X 出口到 Y」「X 在 Y 的洞察」这类显式句式，剥掉地理词与动词后再看还剩什么
    residual = text
    for alias in sorted(_MARKET_ALIASES, key=len, reverse=True):
        residual = residual.replace(alias, " ")
    for cand in uniq:
        residual = residual.replace(cand, " ")
    residual = re.sub(
        r"(市场洞察|洞察报告|需求驱动|价格带|准入壁垒|买家画像|供应商|同行|厂家|厂商|对手|比较|对比|排序|横向|比价|出口|外销|出海|分析|机会|报告|到|去|在|的|请|帮我|给我|我们|一下|看看|这个|那个|做个|做一个|做一份|来一份|出一份|，|,|、|。|\?|？|!|！|\s|market\s*insight|compare\s+suppliers?)",
        " ",
        residual,
        flags=re.I,
    )
    guess = " ".join(token for token in residual.split() if len(token) >= 2)
    out["category"] = guess[:60]
    return out


LONG_RUNNING_INTENTS = frozenset(
    {
        "find_buyers",
        "lead_content_pack",
        "geo_content_matrix",
        "market_research",
        "flywheel_loop",
        "osint_check",
        "website_icp",
        # 对标 Accio Work 的两条新能力（LLM 驱动，默认走异步入队）
        "market_insight",
        "supplier_compare",
    }
)


class UBrainOrchestrator:
    TOOLS = [
        "find_buyers",
        "outreach_letter_pack",
        "negotiation_draft",
        "lead_content_pack",
        "geo_content_matrix",
        "geo_submit_pack",
        "matrix_publish",
        "inquiry_score",
        "inquiry_draft",
        "weekly_lead_report",
        "publish_status",
        "ssl_status",
        "export_feasibility",
        "blue_ocean",
        "hs_lookup",
        "market_research",
        "market_insight",
        "supplier_compare",
        "sync_feedback",
        "ops_snapshot",
        "general",
        "osint_check",
        "website_icp",
        "proforma_invoice",
        "prospect_clean",
    ]
    def detect_intent(self, message: str) -> str:
        """detect_intent。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        m = message.strip()
        intent = self._match_intent_group_a(m)
        if intent is not None:
            return intent
        intent = self._match_intent_group_b(m)
        if intent is not None:
            return intent
        return "general"

    def _match_intent_group_a(self, m: str) -> str | None:
        """_match_intent_group_a。

        参数说明：
        :param self: 参数 self
        :param m: 参数 m
        :return: 返回处理结果。
        """
        if re.search(
            r"(跑一轮|全自动|闭环|卖货飞轮).{0,24}(找客|卖货|获客|研究|市场)|"
            r"飞轮.{0,12}(研究|找客|跑)",
            m,
        ):
            return "flywheel_loop"
        if re.search(
            r"(找.{0,24}(客户|采购商|买家|线索)|挖掘.{0,8}采购|目标客户)",
            m,
        ) and not re.search(r"(跑一轮|飞轮|闭环)", m):
            return "find_buyers"
        if re.search(r"自动找客", m) and not re.search(r"(跑一轮|飞轮|闭环|研究)", m):
            return "find_buyers"
        if re.search(
            r"(开发信|cold\s*email|outreach|写信|邮件模板|给.{0,8}写.{0,4}信)",
            m,
            re.I,
        ):
            return "outreach_letter_pack"
        if re.search(
            r"(谈单|砍价|还价|反报价|议价|negotiat|报价.{0,4}怎么回|压价)",
            m,
            re.I,
        ):
            return "negotiation_draft"
        if re.search(
            r"(GEO.{0,12}(文章|内容矩阵|矩阵)|SEO.{0,8}内容矩阵|geo_content|"
            r"写.{0,6}GEO.{0,6}文|生成.{0,6}GEO)",
            m,
            re.I,
        ):
            return "geo_content_matrix"
        if re.search(r"(获客包|内容包|长尾|FAQ|faq|写.{0,6}\d+.{0,3}篇|生成.{0,6}文章|保温.{0,8}(选题|文章|内容))", m, re.I):
            return "lead_content_pack"
        if re.search(
            r"(GEO.{0,8}清单|按.{0,4}GEO|geo.{0,8}清单|"
            r"检查.{0,8}独立域|独立域.{0,8}检查|llms\.txt|"
            r"GEO.{0,4}提交|geo.{0,4}提交|AI.{0,4}引用|"
            r"提交.{0,4}(豆包|通义|文心)|结构化数据清单|Schema清单)",
            m,
            re.I,
        ):
            return "geo_submit_pack"
        if re.search(r"(矩阵|平台|抖音|视频号|百家号|小红书|发布|发帖).{0,12}(发|发布|分发|导流)", m):
            return "matrix_publish"
        if re.search(r"(询盘|线索).{0,8}(分级|评分|打分|高意向|意向|跟进)", m):
            return "inquiry_score"
        if re.search(r"(周报|复盘|线索表|电话量|询盘量|本周线索)", m):
            return "weekly_lead_report"
        if re.search(
            r"(能做出口|能出口|能不能出口|出口.{0,10}(可行|合适|怎么样|如何|吗|不)|"
            r"发到|出口到|外销.{0,8}(越南|沙特|美国|印尼|阿联酋|迪拜|墨西哥|泰国|马来))",
            m,
            re.I,
        ):
            return "export_feasibility"
        if re.search(r"(出口|外销).{0,12}(可行性|适不适合|值不值得|怎么样|如何)", m):
            return "export_feasibility"
        if re.search(r"(可行性|适不适合).{0,12}(出口|外销|出海)", m):
            return "export_feasibility"
        if re.search(r"(市场研究|竞品.{0,6}报告|反哺)", m, re.I):
            return "market_research"
        # 放在 market_research 之后：「市场研究」这类老说法保持原路由，
        # 只有明确要洞察/横向比较时才走对标 Accio Work 的新能力。
        if re.search(
            r"(市场洞察|洞察报告|需求驱动|价格带|准入壁垒|买家画像|目标市场.{0,10}(分析|机会|洞察)|"
            r"market\s*insight)",
            m,
            re.I,
        ):
            return "market_insight"
        if re.search(
            r"((对比|比较|排序|哪家|谁更|横向|比价).{0,14}(供应商|同行|厂家|厂商|对手)|"
            r"供应商.{0,6}(对比|比较|排序)|compare\s+suppliers?)",
            m,
            re.I,
        ):
            return "supplier_compare"
        return None

    def _match_intent_group_b(self, m: str) -> str | None:
        """_match_intent_group_b。

        参数说明：
        :param self: 参数 self
        :param m: 参数 m
        :return: 返回处理结果。
        """
        if re.search(r"(同步.{0,4}反馈|效果回流|销售反馈|销售数据|转化复盘)", m):
            return "sync_feedback"
        if re.search(r"(蓝海|哪个国家好卖|往哪卖|推荐.{0,4}国家)", m):
            return "blue_ocean"
        if re.search(r"(HS|海关编码|税号|hs)", m, re.I):
            return "hs_lookup"
        if re.search(
            r"(最新询盘|回复.{0,6}询盘(?!.*打分)|询盘回复(?!.*分)|回信|draft)",
            m,
            re.I,
        ):
            return "inquiry_draft"
        if re.search(r"(经营快照|店铺诊断|待处理询盘)", m):
            return "ops_snapshot"
        if re.search(r"(发布|发帖).{0,8}(好了|完成|状态)", m):
            return "publish_status"
        if re.search(r"(SSL|证书|https|域名).{0,8}(好了|签发|过期)", m, re.I):
            return "ssl_status"
        if re.search(
            r"(背调|尽调|尽职调查|OSINT|background\s*check|制裁名单|sanction)",
            m,
            re.I,
        ) or (_EMAIL_RE.search(m) and re.search(r"(查|验|背调|风险)", m)):
            return "osint_check"
        if re.search(
            r"(官网分析|网站画像|ICP|理想客户|分析.{0,6}官网|website.{0,8}profile)",
            m,
            re.I,
        ):
            return "website_icp"
        if re.search(
            r"(形式发票|proforma|\bPI\b|报价单|做.{0,4}PI|开.{0,4}PI)",
            m,
            re.I,
        ):
            return "proforma_invoice"
        if re.search(r"(清洗|去重).{0,8}(潜客|线索|客户|名单)", m):
            return "prospect_clean"
        return None

    def _is_capability_question(self, message: str) -> bool:
        """_is_capability_question。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        return bool(_CAPABILITY_QUESTION_RE.search(message.strip()))

    def _load_ops_snapshot(
        self,
        db: Session | None,
        tenant_id: str | None,
    ) -> dict[str, Any] | None:
        """_load_ops_snapshot。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        if db is None or not tenant_id:
            return None
        try:
            from app.services.ubrain.inquiry_context_service import tenant_ops_snapshot
            return tenant_ops_snapshot(db, tenant_id)
        except Exception:
            return None

    def _general_smart_reply(
        self,
        message: str,
        memory: dict[str, Any],
        *,
        db: Session | None = None,
        tenant_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """_general_smart_reply。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param memory: 参数 memory
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param context: 参数 context
        :return: 返回处理结果。
        """
        situational = build_situational_context(db, tenant_id, memory)
        ops = self._load_ops_snapshot(db, tenant_id)
        ctx = context or {}
        reply, meta = build_smart_general_reply(
            message,
            memory,
            situational=situational,
            ops=ops,
            is_capability_question=self._is_capability_question(message),
            last_strategies=ctx.get("last_strategies"),
        )
        meta["context_lines"] = len(situational.splitlines())
        return reply, meta

    def _general_llm_reply(
        self,
        message: str,
        memory: dict[str, Any],
        *,
        db: Session | None = None,
        tenant_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """_general_llm_reply。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param memory: 参数 memory
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param context: 参数 context
        :return: 返回处理结果。
        """
        from app.services.ubrain.llm_assist_reply import reply_with_template_and_llm
        from app.services.ubrain.reply_templates import polish_scaffold_from_smart_reply
        ctx = context or {}
        ops = self._load_ops_snapshot(db, tenant_id)
        situational = build_situational_context(db, tenant_id, memory)
        expanded = expand_strategy_choice(
            message,
            memory,
            ops=ops,
            last_strategies=ctx.get("last_strategies"),
        )
        if expanded:
            return expanded

        is_cap = self._is_capability_question(message)
        smart_reply, smart_meta = build_smart_general_reply(
            message,
            memory,
            situational=situational,
            ops=ops,
            is_capability_question=is_cap,
            last_strategies=ctx.get("last_strategies"),
        )
        if is_cap:
            smart_meta.setdefault("mode", "capability_intro")
            return smart_reply, smart_meta

        recent = ctx.get("recent_turns")
        recent_turns = recent if isinstance(recent, list) else None
        mode = str(smart_meta.get("mode") or "general")
        scaffold = polish_scaffold_from_smart_reply(smart_reply, mode=mode)
        reply, meta = reply_with_template_and_llm(
            message,
            memory,
            template_body=scaffold,
            mode=mode,
            situational=situational,
            ops=ops,
            recent_turns=recent_turns,
            fallback_reply=smart_reply,
            fallback_meta=smart_meta,
        )
        meta.setdefault("context_lines", len(situational.splitlines()))
        return reply, meta

    def _lead_content_pack(
        self,
        message: str,
        ctx: dict[str, Any],
        *,
        db: Session | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """_lead_content_pack。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        category = ctx.get("category") or ("保温建材" if "保温" in message else "建材")
        primary = category
        spec_hint = ""
        if db is not None and tenant_id:
            from app.services.tenant_product_profile_service import require_product_profile_for_content
            profile = require_product_profile_for_content(db, str(tenant_id))
            primary = profile.get("primary_product") or category
            category = profile.get("product_category") or primary or category
            spec_hint = (profile.get("spec_summary_zh") or "")[:120]
        count_match = re.search(r"(\d+)\s*篇", message)
        count = min(int(count_match.group(1)), 20) if count_match else int(ctx.get("count", 10))
        count = max(3, min(count, 20))
        spec_line = f"（规格要点：{spec_hint}）" if spec_hint else ""
        seed_topics = [
            f"{primary}怎么选：采购前先看密度、厚度和防火等级{spec_line}",
            f"{primary}报价为什么差很多：材料、规格和运输怎么影响价格",
            f"{primary}施工常见问题与验收清单",
            f"{primary}厂家怎么判断是否靠谱：资质、案例和交付能力",
            f"{primary}适合哪些场景：冷库、外墙、厂房还是屋面",
            f"{primary}防火等级怎么问才不会买错",
            f"{primary}运输到外地怎么算损耗和运费",
            f"{primary}小批量采购和工程批量采购有什么区别",
            f"{primary}常见规格参数表，采购询价前要准备什么",
            f"{primary}售后与施工配合，哪些问题要提前写进合同",
        ]
        topics = seed_topics[:count]
        return {
            "mode": "deerflow_ready",
            "category": category,
            "primary_product": primary,
            "count": count,
            "topics": topics,
            "write_back": "cms_draft",
            "human_review_required": True,
            "north_star": "生成后必须导向独立域表单或电话，不能只堆文章。",
        }

    def _geo_submit_pack(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """_geo_submit_pack。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        domain = ctx.get("domain") or "待绑定独立域"
        checklist = [
            {"id": "https", "label": "HTTPS 可访问且无证书警告"},
            {"id": "phone_required", "label": "表单手机号必填，电话入口明显"},
            {"id": "llms_txt", "label": "生成 /llms.txt 与品牌/产品 FAQ"},
            {"id": "schema", "label": "补 Organization / Product / FAQ 结构化数据"},
            {"id": "baidu_submit", "label": "提交百度站长 sitemap 与主动推送"},
            {"id": "ai_entries", "label": "整理豆包/通义/文心可引用品牌说明"},
        ]
        return {
            "domain": domain,
            "checklist": checklist,
            "human_review_required": True,
            "promise_boundary": "这是 GEO 执行清单，不承诺具体排名或电话数。",
        }

    def _matrix_publish_plan(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """_matrix_publish_plan。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        platforms = ctx.get("platforms") or ["抖音", "视频号", "百家号"]
        platforms = [str(p) for p in platforms][:5]
        return {
            "platforms": platforms,
            "content_source": ctx.get("content_source") or "待选择内容母版",
            "cta": ctx.get("cta") or "导向独立域询盘表单/电话",
            "write_back": "publish_tasks",
            "human_confirmation_required": True,
        }

    def _score_inquiry(
        self,
        message: str,
        ctx: dict[str, Any],
        *,
        db: Session | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """_score_inquiry。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        inquiry = ctx.get("inquiry") or {}
        if db is not None and tenant_id and not inquiry.get("message"):
            from app.services.ubrain.inquiry_context_service import resolve_inquiry
            resolved = resolve_inquiry(db, str(tenant_id), ctx)
            if resolved:
                inquiry = resolved
                ctx = {**ctx, "inquiry": resolved}
        from app.services.ubrain.inquiry_scoring_service import score_inquiry_lead
        return score_inquiry_lead(message, inquiry=inquiry)

    def _weekly_lead_report(self, db: Session | None, tenant_id: str | None) -> dict[str, Any]:
        """_weekly_lead_report。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        if db is None:
            return {
                "available": False,
                "message": "需要数据库会话才能生成真实线索周报。",
            }
        data = InquiriesUnifiedService(db).list_page(
            page=1,
            page_size=200,
            tenant_id=tenant_id,
        )
        items = data.get("items") or []
        status_counter = Counter(str(i.get("status") or "unknown") for i in items)
        source_counter = Counter(str(i.get("source_channel") or "unknown") for i in items)
        with_phone = [
            i for i in items
            if re.search(r"1[3-9]\d{9}", str(i.get("phone") or ""))
        ]
        return {
            "available": True,
            "total": data.get("total", len(items)),
            "sample_size": len(items),
            "with_phone": len(with_phone),
            "by_status": dict(status_counter),
            "by_source": dict(source_counter),
            "north_star": "有效电话/询盘数量以 with_phone 和人工标注可跟进为准。",
        }

    def chat(
        self,
        message: str,
        *,
        db: Session | None = None,
        tenant_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """chat。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param context: 参数 context
        :return: 返回处理结果。
        """
        intent = self.detect_intent(message)
        intent = refine_intent(message, intent)
        if isinstance(context, dict):
            ctx = dict(context)
        elif isinstance(context, str):
            ctx = {"raw_context": context}
        else:
            ctx = {}
        if intent in LONG_RUNNING_INTENTS and not ctx.get("sync"):
            ctx.setdefault("async", True)
        tool_result: dict[str, Any] = {}
        reply = ""
        memory: dict[str, Any] = {}
        effective_tenant = ctx.get("tenant_id") or tenant_id
        if db is not None and effective_tenant:
            memory = get_memory(db, str(effective_tenant))

        if intent == "find_buyers":
            reply, tool_result = self._handle_find_buyers(message, ctx, db, effective_tenant, memory)
        elif intent == "outreach_letter_pack":
            reply, tool_result = self._handle_outreach_letter_pack(message, ctx, db, effective_tenant, memory)
        elif intent == "negotiation_draft":
            reply, tool_result = self._handle_negotiation_draft(message, ctx, memory)
        elif intent == "lead_content_pack":
            return self._handle_lead_content_pack(message, ctx, db, effective_tenant, memory, tenant_id, intent)
        elif intent == "geo_content_matrix":
            return self._handle_geo_content_matrix(message, ctx, db, effective_tenant, memory, tenant_id, intent)
        elif intent == "geo_submit_pack":
            reply, tool_result = self._handle_geo_submit_pack(message, ctx, db, effective_tenant)
        elif intent == "matrix_publish":
            reply, tool_result = self._handle_matrix_publish(message, ctx, db, effective_tenant)
        elif intent == "inquiry_score":
            reply, tool_result = self._handle_inquiry_score(message, ctx, db, effective_tenant)
        elif intent == "weekly_lead_report":
            reply, tool_result = self._handle_weekly_lead_report(db, tenant_id)
        elif intent == "market_research":
            reply, tool_result = self._handle_market_research(message, ctx, db, effective_tenant)
        elif intent in ("market_insight", "supplier_compare"):
            reply, tool_result = self._handle_accio_replica_intent(
                intent, message, ctx, db, effective_tenant
            )
        elif intent == "sync_feedback":
            reply, tool_result = self._handle_sync_feedback(ctx, db, effective_tenant)
        elif intent == "flywheel_loop":
            reply, tool_result = self._handle_flywheel_loop(message, ctx, db, effective_tenant)
        elif intent == "osint_check":
            reply, tool_result = self._handle_osint_check(message, ctx, db, effective_tenant)
        elif intent == "website_icp":
            reply, tool_result = self._handle_website_icp(message, ctx, db, effective_tenant)
        elif intent == "proforma_invoice":
            reply, tool_result = self._handle_proforma_invoice(message, ctx, db, effective_tenant)
        elif intent == "prospect_clean":
            reply, tool_result = self._handle_prospect_clean(ctx)
        elif intent == "export_feasibility":
            reply, tool_result, memory = self._handle_export_feasibility(message, ctx, db, effective_tenant, memory)
        elif intent == "blue_ocean":
            reply, tool_result = self._handle_blue_ocean(message, db)
        elif intent == "hs_lookup":
            reply, tool_result = self._handle_hs_lookup(message)
        elif intent == "ops_snapshot":
            reply, tool_result = self._handle_ops_snapshot(ctx, db, effective_tenant)
        elif intent == "inquiry_draft":
            reply, tool_result = self._handle_inquiry_draft(message, ctx, db, effective_tenant, memory)
        elif intent == "publish_status":
            reply, tool_result = self._handle_publish_status()
        elif intent == "ssl_status":
            reply, tool_result = self._handle_ssl_status(ctx)
        else:
            reply, tool_result = self._handle_general_reply(message, ctx, db, effective_tenant, memory)

        return self._finalize_chat_response(intent, reply, tool_result, tenant_id, memory, effective_tenant, db)


    def _handle_find_buyers(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_find_buyers。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            tool_result = {"available": False}
            reply = "找客需登录并绑定租户；登录后可按区域生成采购商候选画像。"
        else:
            async_mode = bool(ctx.get("async")) and not bool(ctx.get("sync"))
            if async_mode:
                job = enqueue_job(
                    db,
                    tenant_id=str(effective_tenant),
                    intent="find_buyers",
                    payload={"message": message, "context": ctx},
                    created_by=ctx.get("user_id"),
                )
                tool_result = {
                    "job_id": job.id,
                    "job_status": "queued",
                    "mode": "deerflow_async",
                }
                reply = f"已排队找客任务（{job.id[:8]}…），完成后刷新查看候选采购商。"
            else:
                tool_result = find_buyer_prospects(
                    db, tenant_id=str(effective_tenant), message=message, memory=memory
                )
                reply = (
                    f"已为「{tool_result['region']}」生成 {tool_result['count']} 条"
                    f"{tool_result['category']}采购商「待核实候选」画像。"
                    f"{tool_result['next_step']}"
                    "可在副驾导出 CSV 核实后标记已联系。"
                )
        return reply, tool_result

    def _handle_outreach_letter_pack(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_outreach_letter_pack。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            reply = "开发信需登录租户；登录后可基于候选客户生成中英草稿。"
            tool_result = {"available": False}
        else:
            try:
                tool_result = outreach_letter_pack(
                    db, tenant_id=str(effective_tenant), message=message, memory=memory
                )
                pp = tool_result.get("product_profile") or {}
                sku_n = pp.get("library_sku_count", 0)
                src = ", ".join(pp.get("sources") or [])
                reply = (
                    f"已基于「{pp.get('primary_product') or '主营产品'}」"
                    f"（来源：{src or '产品画像'}；产品库 {sku_n} 条）"
                    f"生成 {tool_result['letter_count']} 封开发信草稿（{tool_result['language']}）。"
                    "发送前请您人工确认规格与证书后再发出。"
                )
            except Exception as exc:
                from app.services.tenant_product_profile_service import ProductProfileRequiredError
                if isinstance(exc, ProductProfileRequiredError):
                    reply = str(exc)
                    tool_result = {"available": False, "error_code": exc.code}
                else:
                    raise
        return reply, tool_result

    def _handle_negotiation_draft(
        self,
        message: str,
        ctx: dict[str, Any],
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_negotiation_draft。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        tool_result = negotiation_draft(message, ctx, memory)
        reply = (
            "已生成 3 轮谈单话术（首轮报价 / 压价回应 / 临门确认）。"
            "请按实际订单修改后发送，系统不会自动砍价或改价。"
        )
        return reply, tool_result

    def _handle_lead_content_pack(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
        tenant_id: str | None,
        intent: str,
    ) -> dict[str, Any]:
        """_handle_lead_content_pack。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :param tenant_id: 参数 tenant_id
        :param intent: 参数 intent
        :return: 返回处理结果。
        """
        effective_tenant = ctx.get("tenant_id") or tenant_id
        try:
            tool_result = self._lead_content_pack(
                message,
                ctx,
                db=db,
                tenant_id=str(effective_tenant) if effective_tenant else None,
            )
        except Exception as exc:
            from app.services.tenant_product_profile_service import ProductProfileRequiredError
            if isinstance(exc, ProductProfileRequiredError):
                reply = str(exc)
                tool_result = {"available": False, "error_code": exc.code}
                return {
                    "intent": intent,
                    "reply": reply.strip(),
                    "tool": intent,
                    "tool_result": tool_result,
                    "disclaimer": None,
                    "tenant_id": tenant_id,
                    "memory_snapshot": memory if memory else None,
                    "needs_confirmation": False,
                }
            raise
        async_mode = bool(ctx.get("async")) and not bool(ctx.get("sync"))
        if db is not None and effective_tenant:
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="lead_content_pack",
                payload={"message": message, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result["job_id"] = job.id
            if async_mode:
                tool_result["job_status"] = "queued"
                tool_result["mode"] = "deerflow_async"
                reply = (
                    f"已创建获客内容任务（{job.id[:8]}…），状态 queued。"
                    "可在副驾刷新任务状态；完成后 CMS 草稿将出现在统一发布母版。"
                )
            else:
                ran = run_job(db, job.id)
                tool_result["job_status"] = ran["status"]
                if ran.get("status") == "success" and ran.get("result"):
                    tool_result.update(ran["result"])
                if ran.get("status") == "failed":
                    reply = f"内容任务失败：{ran.get('error_message') or '未知错误'}"
                elif tool_result.get("cms_draft_count"):
                    reply = (
                        f"已写入 {tool_result['cms_draft_count']} 篇 CMS 草稿（任务 {job.id[:8]}…）。"
                        "请在「统一发布母版」人审后发布，并确保 CTA 指向独立域电话/表单。"
                    )
                else:
                    reply = (
                        f"已生成「{tool_result['category']}」选题计划；"
                        "重复标题已跳过。请到统一发布母版查看。"
                    )
        else:
            tool_result["cms_write_skipped"] = "missing_db_or_tenant"
            reply = (
                f"已生成「{tool_result['category']}」获客内容包计划（{tool_result['count']} 篇选题）。"
                "登录租户账号后可自动写入 CMS 草稿。"
            )
        return self._finalize_chat_response(intent, reply, tool_result, tenant_id, memory, effective_tenant, db)

    def _handle_geo_content_matrix(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
        tenant_id: str | None,
        intent: str,
    ) -> dict[str, Any]:
        """_handle_geo_content_matrix。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :param tenant_id: 参数 tenant_id
        :param intent: 参数 intent
        :return: 返回处理结果。
        """
        async_mode = bool(ctx.get("async")) and not bool(ctx.get("sync"))
        if db is not None and effective_tenant:
            try:
                from app.services.tenant_product_profile_service import require_product_profile_for_content
                require_product_profile_for_content(db, str(effective_tenant))
            except Exception as exc:
                from app.services.tenant_product_profile_service import ProductProfileRequiredError
                if isinstance(exc, ProductProfileRequiredError):
                    reply = str(exc)
                    tool_result = {"available": False, "error_code": exc.code}
                    return {
                        "intent": intent,
                        "reply": reply.strip(),
                        "tool": intent,
                        "tool_result": tool_result,
                        "disclaimer": None,
                        "tenant_id": tenant_id,
                        "memory_snapshot": memory if memory else None,
                        "needs_confirmation": False,
                    }
                raise
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="geo_content_matrix",
                payload={"message": message, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result = {
                "job_id": job.id,
                "job_status": "queued" if async_mode else "running",
                "mode": "deerflow_async" if async_mode else "deerflow_sync",
            }
            if async_mode:
                reply = (
                    f"已入队 GEO 内容矩阵任务（{job.id[:8]}…）。"
                    "完成后将写入统一发布母版：1 篇母版 + 多平台变体 + GEO 清单。"
                )
            else:
                ran = run_job(db, job.id)
                tool_result["job_status"] = ran["status"]
                if ran.get("status") == "success" and ran.get("result"):
                    tool_result.update(ran["result"])
                if ran.get("status") == "failed":
                    reply = f"GEO 内容矩阵失败：{ran.get('error_message') or '未知错误'}"
                elif tool_result.get("cms_draft_count"):
                    reply = (
                        f"已写入 {tool_result['cms_draft_count']} 条内容草稿（母版+变体+清单）。"
                        "请在「统一发布母版」人审后矩阵分发。"
                    )
                else:
                    reply = "GEO 内容矩阵已完成，请到统一发布母版查看。"
        else:
            tool_result = {"available": False}
            reply = (
                "GEO 内容矩阵需登录租户；登录后可生成 SEO/GEO 母版与各平台变体草稿。"
            )
        return self._finalize_chat_response(intent, reply, tool_result, tenant_id, memory, effective_tenant, db)

    def _handle_geo_submit_pack(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_geo_submit_pack。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        async_mode = bool(ctx.get("async")) and not bool(ctx.get("sync"))
        if db is not None and effective_tenant and async_mode:
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="geo_submit_pack",
                payload={"message": message, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result = {
                "job_id": job.id,
                "job_status": "queued",
                "mode": "deerflow_async",
            }
            reply = (
                f"已入队 GEO 执行清单任务（{job.id[:8]}…）。"
                "完成后可在副驾查看 checklist；不承诺具体排名或电话数。"
            )
        else:
            tool_result = self._geo_submit_pack(ctx)
            reply = (
                f"已按 {tool_result['domain']} 生成 GEO 执行清单。"
                "这能加快被发现，但不承诺具体排名或电话数。"
            )
        return reply, tool_result

    def _handle_matrix_publish(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_matrix_publish。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        from app.services.ubrain.matrix_publish_service import execute_matrix_publish
        async_mode = bool(ctx.get("async")) and not bool(ctx.get("sync"))
        if db is not None and effective_tenant and async_mode and not ctx.get("human_confirmed"):
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="matrix_publish",
                payload={"message": message, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result = {
                "job_id": job.id,
                "job_status": "queued",
                "mode": "deerflow_async",
                "needs_confirmation": True,
            }
            reply = (
                f"已入队矩阵发布任务（{job.id[:8]}…）。"
                "确认后在 context 设置 human_confirmed=true 再执行。"
            )
        elif db is not None and effective_tenant:
            tool_result = execute_matrix_publish(
                db,
                tenant_id=str(effective_tenant),
                message=message,
                context=ctx,
                user_id=ctx.get("user_id"),
            )
            status = tool_result.get("status")
            if status == "queued":
                reply = tool_result.get("reply") or "矩阵发布任务已创建。"
            elif status == "awaiting_confirmation":
                reply = (
                    "已生成矩阵发布计划："
                    f"{'、'.join(tool_result.get('platforms') or [])}。"
                    "请确认后设置 human_confirmed=true 再执行。"
                )
            else:
                reply = tool_result.get("reply") or str(tool_result.get("error") or "矩阵发布处理完成")
        else:
            tool_result = self._matrix_publish_plan(ctx)
            tool_result["needs_confirmation"] = True
            tool_result["human_review_required"] = True
            reply = (
                "已生成矩阵发布计划："
                f"{'、'.join(tool_result['platforms'])}。"
                "发布前需要人工确认，主 CTA 指向独立域询盘。"
            )
        return reply, tool_result

    def _handle_inquiry_score(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_inquiry_score。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        tool_result = self._score_inquiry(
            message, ctx, db=db, tenant_id=str(effective_tenant) if effective_tenant else None
        )
        src = tool_result.get("inquiry_source", "message_only")
        reply = (
            f"这条线索意向为 {tool_result['level']}（{tool_result['score']} 分）。"
            f"建议：{tool_result['next_action']}"
        )
        if src == "latest_inquiry":
            reply = f"【基于最新询盘】{reply}"
        return reply, tool_result

    def _handle_weekly_lead_report(
        self,
        db: Session | None,
        tenant_id: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_weekly_lead_report。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        tool_result = self._weekly_lead_report(db, tenant_id)
        if tool_result.get("available"):
            reply = (
                f"本次可统计线索 {tool_result['sample_size']} 条，其中带手机号 "
                f"{tool_result['with_phone']} 条。建议以带手机号和人工可跟进为北极星。"
            )
        else:
            reply = tool_result["message"]
        return reply, tool_result

    def _handle_market_research(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_market_research。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            reply = "市场研究需登录租户；将入队深度研究并自动串联找客与开发信。"
            tool_result = {"available": False}
        else:
            from app.services.ubrain.commercial_os_bridge import run_market_research
            if ctx.get("async") and not ctx.get("sync"):
                job = enqueue_job(
                    db,
                    tenant_id=str(effective_tenant),
                    intent="market_research",
                    payload={"message": message, "context": ctx},
                    created_by=ctx.get("user_id"),
                )
                tool_result = {"job_id": job.id, "job_status": "queued", "mode": "deerflow_async"}
                reply = (
                    f"已入队深度市场研究（{job.id[:8]}…）。"
                    "完成后将沉淀洞察并自动排队找客→开发信；可在副驾查看任务进度。"
                )
            else:
                tool_result = run_market_research(
                    db, tenant_id=str(effective_tenant), message=message
                )
                n_findings = len(tool_result.get("findings") or [])
                approved = tool_result.get("reviewer_approved", True)
                reply = (
                    f"【市场研究简报】{tool_result.get('executive_summary', '')}\n"
                    f"结论 {n_findings} 条，审核{'通过' if approved else '需人工确认'}；"
                    f"已参考历史洞察 {tool_result.get('prior_insights_used', 0)} 条。"
                    f"后续编排：{tool_result.get('next_pipeline', '')}"
                )
        return reply, tool_result

    def _handle_accio_replica_intent(
        self,
        intent: str,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """市场洞察 / 供应商比较（对标阿里国际 Accio Work）。

        与 DeerFlow 计划路径共用同一 intent 实现：这里只入队 + 消费，
        不再自己算一遍，避免两条链路结论不一致。
        """
        subject = _extract_insight_subject(message)
        tool_result: dict[str, Any] = {
            "intent": intent,
            "category": subject.get("category"),
            "target_market": subject.get("target_market"),
        }
        if db is None or not effective_tenant:
            return (
                "市场洞察与供应商比较需要登录租户后运行（结果会沉淀进租户洞察）。",
                {**tool_result, "available": False},
            )

        missing: list[str] = []
        if not subject.get("category"):
            missing.append("品类")
        if not subject.get("target_market"):
            missing.append("目标市场")
        if intent == "supplier_compare" and not subject.get("candidates"):
            missing.append("要比较的供应商/同行名单")
        if missing:
            # 参数不全就明说要什么，不硬猜一个品类糊弄过去
            return (
                f"还缺 {'、'.join(missing)} 才能出结论。"
                "例：「岩棉板 出口 沙特 市场洞察」，"
                "或「对比 A 公司、B 公司、C 公司在沙特的岩棉板供应商」。",
                {**tool_result, "available": False, "missing_params": missing},
            )

        payload: dict[str, Any] = {
            "category": subject["category"],
            "target_market": subject["target_market"],
        }
        if subject.get("candidates"):
            payload["candidates"] = subject["candidates"]
        job = enqueue_job(
            db,
            tenant_id=str(effective_tenant),
            intent=intent,
            payload=payload,
            created_by=ctx.get("user_id"),
        )
        tool_result["job_id"] = job.id

        if ctx.get("async") and not ctx.get("sync"):
            tool_result["job_status"] = "queued"
            tool_result["mode"] = "deerflow_async"
            return (
                f"已入队{('市场洞察' if intent == 'market_insight' else '供应商横向比较')}"
                f"（{job.id[:8]}…），完成后结论会沉淀进租户洞察。",
                tool_result,
            )

        ran = run_job(db, job.id)
        tool_result["job_status"] = ran["status"]
        result = ran.get("result") or {}
        if result:
            tool_result.update(result)
        label = "市场洞察" if intent == "market_insight" else "供应商比较"
        if ran.get("status") != "success":
            return f"{label}失败：{ran.get('error_message') or '未知错误'}", tool_result
        if result.get("degraded"):
            return f"{label}未完成：{result.get('reason') or '执行降级'}", tool_result
        body = result.get("insight") or result.get("comparison") or {}
        confidence = body.get("confidence") if isinstance(body, dict) else None
        verify = body.get("verification_required") if isinstance(body, dict) else None
        parts = [f"{label}已生成（品类 {subject['category']} × 市场 {subject['target_market']}）。"]
        if confidence:
            parts.append(f"模型置信度 {confidence}；")
        if verify:
            parts.append(f"待人工核实 {len(verify)} 项。")
        else:
            parts.append("结论为模型推断，须经人工核实后方可对外使用。")
        return "".join(parts), tool_result

    def _handle_sync_feedback(
        self,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_sync_feedback。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            reply = "效果回流需登录租户。"
            tool_result = {"available": False}
        else:
            from app.services.ubrain.commercial_os_bridge import collect_sales_feedback
            tool_result = collect_sales_feedback(db, str(effective_tenant))
            reply = sanitize_public_copy(
                tool_result.get("assistant_prompt")
                or tool_result.get("deerflow_next_prompt")
                or "已同步销售反馈到研究记忆。"
            )
        return reply, tool_result

    def _handle_flywheel_loop(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_flywheel_loop。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            reply = "飞轮闭环需登录并绑定租户。"
            tool_result = {"available": False}
        else:
            user_role = str(ctx.get("user_role") or "")
            can_sync = user_role == "super_admin" and bool(ctx.get("sync"))
            if not can_sync:
                job = enqueue_job(
                    db,
                    tenant_id=str(effective_tenant),
                    intent="flywheel_loop",
                    payload={"message": message, "context": ctx},
                    created_by=ctx.get("user_id"),
                )
                tool_result = {
                    "job_id": job.id,
                    "job_status": "queued",
                    "mode": "deerflow_async",
                }
                reply = (
                    f"已入队卖货飞轮（{job.id[:8]}…）：市场研究→找客→编排。"
                    "完成后副驾会刷新；外发仍需您确认。"
                )
            else:
                loop = run_closed_loop_flywheel(
                    db,
                    tenant_id=str(effective_tenant),
                    message=message,
                    user_id=str(ctx.get("user_id")) if ctx.get("user_id") else None,
                )
                tool_result = loop
                reply = sanitize_public_copy(str(loop.get("reply") or ""))
        return reply, tool_result

    def _handle_osint_check(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_osint_check。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        from app.services.foreign_trade.foreign_trade_agent_service import (
            extract_osint_target,
            run_osint_agent,
        )
        target = extract_osint_target(message, ctx)
        if not target:
            tool_result = {"available": False, "needs_target": True}
            reply = "请提供要背调的邮箱、域名或公司名，例如：「背调 buyer@acme.com」。"
        elif db is not None and effective_tenant and ctx.get("async") and not ctx.get("sync"):
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="osint_check",
                payload={"message": message, "target": target, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result = {"job_id": job.id, "job_status": "queued", "target": target}
            reply = f"已入队背调任务（{job.id[:8]}…），目标 {target}。"
        else:
            tool_result = run_osint_agent(target)
            reply = tool_result.get("summary") or "背调完成，请查看风险评分与建议。"
            if db is not None and effective_tenant:
                record_tool_use(db, str(effective_tenant), "osint_check")
        return reply, tool_result

    def _handle_website_icp(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_website_icp。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        from app.services.foreign_trade.foreign_trade_agent_service import run_website_icp_agent
        if db is None or not effective_tenant:
            reply = "官网 ICP 分析需登录租户。"
            tool_result = {"available": False}
        elif ctx.get("async") and not ctx.get("sync"):
            job = enqueue_job(
                db,
                tenant_id=str(effective_tenant),
                intent="website_icp",
                payload={"message": message, "context": ctx},
                created_by=ctx.get("user_id"),
            )
            tool_result = {"job_id": job.id, "job_status": "queued"}
            reply = f"已入队官网 ICP 分析（{job.id[:8]}…）。"
        else:
            tool_result = run_website_icp_agent(
                db, str(effective_tenant), message=message, ctx=ctx
            )
            reply = tool_result.get("summary") or "官网 ICP 分析完成。"
        return reply, tool_result

    def _handle_proforma_invoice(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_proforma_invoice。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        from app.services.foreign_trade.foreign_trade_agent_service import run_proforma_agent
        if db is None or not effective_tenant:
            reply = "形式发票需登录租户；可补充买家信息与行项目。"
            tool_result = {"available": False}
        else:
            tool_result = run_proforma_agent(
                db, str(effective_tenant), message=message, ctx=ctx
            )
            reply = (
                f"{tool_result.get('summary')}。"
                "请人工核对条款后再发给客户。"
            )
        return reply, tool_result

    def _handle_prospect_clean(
        self,
        ctx: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_prospect_clean。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        from app.services.foreign_trade.foreign_trade_agent_service import run_prospect_clean_agent
        customers = ctx.get("customers") or ctx.get("prospects") or []
        if not customers:
            tool_result = {"available": False}
            reply = "请在 context 传入 customers/prospects 列表，或先说「找客」再清洗。"
        else:
            tool_result = run_prospect_clean_agent(
                customers, existing=ctx.get("existing")
            )
            reply = tool_result.get("summary") or "潜客清洗完成。"
        return reply, tool_result

    def _handle_export_feasibility(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """_handle_export_feasibility。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        fr = export_feasibility(message, db=db)
        recent_turns = ctx.get("recent_turns")
        if not isinstance(recent_turns, list):
            recent_turns = None
        reply, reply_meta = build_export_feasibility_reply(
            message,
            fr,
            memory=memory,
            recent_turns=recent_turns,
        )
        tool_result = {**fr.to_dict(), **reply_meta}
        if db is not None and effective_tenant:
            ask_count = int(reply_meta.get("ask_count") or 1)
            memory = record_tool_use(
                db,
                str(effective_tenant),
                "export_feasibility",
                context_patch=memory_patch_after_export(
                    message, fr, ask_count=ask_count
                ),
            )
            tool_result["memory_updated"] = True
        return reply, tool_result, memory

    def _handle_blue_ocean(
        self,
        message: str,
        db: Session | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_blue_ocean。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param db: 参数 db
        :return: 返回处理结果。
        """
        tool_result = blue_ocean(message, db=db)
        lines = [
            f"{i+1}. {r['country_code']}（{r.get('growth','')} · 竞争{r.get('competition','')}）— {r.get('reason','')[:60]}"
            for i, r in enumerate(tool_result.get("recommendations") or [])
        ]
        reply = f"针对【{tool_result.get('category')}】推荐市场：\n" + "\n".join(lines)
        return reply, tool_result

    def _handle_hs_lookup(self, message: str) -> tuple[str, dict[str, Any]]:
        """_handle_hs_lookup。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        tool_result = hs_lookup(message)
        reply = f"{tool_result.get('category')}：{tool_result.get('note')}"
        return reply, tool_result

    def _handle_ops_snapshot(
        self,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """_handle_ops_snapshot。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :return: 返回处理结果。
        """
        if db is None or not effective_tenant:
            reply = "经营快照需登录租户。"
            tool_result = {"available": False}
        else:
            from app.services.ubrain.inquiry_context_service import tenant_ops_snapshot
            tool_result = tenant_ops_snapshot(db, str(effective_tenant))
            reply = (
                f"待处理询盘 {tool_result['pending_inquiries']} 条"
                f"（带手机 {tool_result['pending_with_phone']}）。"
                f"待开发信候选 {tool_result['prospects_draft_ready']}。"
            )
            if tool_result.get("hints"):
                reply += "\n" + "；".join(tool_result["hints"])
        return reply, tool_result

    def _handle_inquiry_draft(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_inquiry_draft。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        tone = ctx.get("tone") or memory.get("tone") or "专业、简洁"
        lang = "en" if re.search(r"英文|english", message, re.I) else "zh"
        product = memory.get("product_category") or "建材"
        tool_result = {"draft": True, "language": lang, "tone": tone}
        if db is not None and effective_tenant:
            from app.services.ubrain.inquiry_context_service import (
                build_inquiry_reply_draft,
                resolve_inquiry,
            )
            inquiry = resolve_inquiry(db, str(effective_tenant), ctx)
            if inquiry:
                reply, meta = build_inquiry_reply_draft(
                    inquiry,
                    tone=tone,
                    lang=lang,
                    product_category=product,
                )
                tool_result = {**tool_result, **meta}
            else:
                reply = "当前租户暂无询盘记录，请先通过独立域表单收一条线索。"
                tool_result["available"] = False
            record_tool_use(db, str(effective_tenant), "inquiry_draft")
        elif lang == "en":
            reply = (
                f"【{tone} · draft】\n"
                f"Thank you for your inquiry on {product}. "
                "Please share quantity, destination port and required specs."
            )
        else:
            reply = (
                f"【{tone} · 询盘回复草稿】\n"
                f"感谢咨询{product}。请补充数量、目的港与规格。"
            )
        return reply, tool_result

    def _handle_publish_status(self) -> tuple[str, dict[str, Any]]:
        """_handle_publish_status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        tool_result = {"queue": "ops_publish_worker", "hint": "调用 /ops/publish-worker/run 或查看发布日志"}
        reply = "最近发布任务：请在「内容管理 → 发布记录」查看；如需我代查队列状态，请提供任务 ID。"
        return reply, tool_result

    def _handle_ssl_status(self, ctx: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """_handle_ssl_status。

        参数说明：
        :param self: 参数 self
        :param ctx: 参数 ctx
        :return: 返回处理结果。
        """
        domain = ctx.get("domain") or "您的独立域"
        tool_result = {"domain": domain, "check": "/api/v1/domain"}
        reply = f"正在查询 {domain} 的 SSL 状态，请稍后在「独立域」页面刷新；已签发会显示过期日。"
        return reply, tool_result

    def _handle_general_reply(
        self,
        message: str,
        ctx: dict[str, Any],
        db: Session | None,
        effective_tenant: str | None,
        memory: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """_handle_general_reply。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :param ctx: 参数 ctx
        :param db: 参数 db
        :param effective_tenant: 参数 effective_tenant
        :param memory: 参数 memory
        :return: 返回处理结果。
        """
        reply, tool_result = self._general_llm_reply(
            message,
            memory,
            db=db,
            tenant_id=str(effective_tenant) if effective_tenant else None,
            context=ctx,
        )
        tool_result = {
            **tool_result,
            "memory": memory,
            "suggested_tools": self.TOOLS[:8],
        }
        return reply, tool_result

    def _finalize_chat_response(
        self,
        intent: str,
        reply: str,
        tool_result: dict[str, Any],
        tenant_id: str | None,
        memory: dict[str, Any],
        effective_tenant: str | None,
        db: Session | None,
    ) -> dict[str, Any]:
        """_finalize_chat_response。

        参数说明：
        :param self: 参数 self
        :param intent: 参数 intent
        :param reply: 参数 reply
        :param tool_result: 参数 tool_result
        :param tenant_id: 参数 tenant_id
        :param memory: 参数 memory
        :param effective_tenant: 参数 effective_tenant
        :param db: 参数 db
        :return: 返回处理结果。
        """
        needs_confirm = intent in (
            "inquiry_draft",
            "matrix_publish",
            "outreach_letter_pack",
            "negotiation_draft",
            "flywheel_loop",
            "proforma_invoice",
            "osint_check",
        )
        extra_disclaimer = None
        if intent in ("find_buyers", "outreach_letter_pack"):
            extra_disclaimer = tool_result.get("disclaimer")
        disclaimer = (
            DISCLAIMER
            if intent in ("export_feasibility", "blue_ocean", "hs_lookup")
            else extra_disclaimer
        )
        if db is not None and effective_tenant:
            try:
                from app.models.tenant import Tenant
                from app.services.ai_traffic_connect_service import (
                    NVIDIA_USAGE_POLICY_NOTICE,
                    build_connect_status,
                    ensure_tenant_ai_connectivity,
                )
                ensure_tenant_ai_connectivity(db, str(effective_tenant))
                tenant = db.query(Tenant).filter(Tenant.id == effective_tenant).first()
                if tenant and build_connect_status(db, tenant).get("free_tier"):
                    disclaimer = (
                        f"{disclaimer}\n\n{NVIDIA_USAGE_POLICY_NOTICE}"
                        if disclaimer
                        else NVIDIA_USAGE_POLICY_NOTICE
                    )
            except Exception as exc:
                logger.warning("ubrain ai_connect disclaimer skipped: %s", exc)
        return {
            "intent": intent,
            "reply": reply.strip(),
            "tool": intent,
            "tool_result": tool_result,
            "disclaimer": disclaimer,
            "tenant_id": tenant_id,
            "memory_snapshot": memory if memory else None,
            "needs_confirmation": needs_confirm,
        }


ubrain_orchestrator = UBrainOrchestrator()
