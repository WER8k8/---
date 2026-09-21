# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
外贸 8 大经典异议智能反击与谈判助攻中枢 (Objection Copilot)。

外贸谈判铁律：
1. 绝不白白降价：每一次让步必须换取同等价值的商业条件（订货量↑、付款方式更优、交期放宽、现货备货）；
2. 绝不凭空担保：质量与交期必有物理证据链背书；
3. 将抗拒转化为闭环成交的台阶。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ObjectionCopilot:
    """8 大外贸异议谈判专家级助攻中枢。"""

    OBJECTIONS: Dict[str, Dict[str, Any]] = {
        "price_high": {
            "key": "price_high",
            "name_cn": "价格偏高 (Target Price Gap)",
            "name_en": "Your price is higher than other suppliers",
            "psychology": "采购商通常只是试探底线，或者拿二线小作坊的低配报价（偷厚度、降等级、不含熏蒸木箱）来砍价。",
            "bottom_line_rules": [
                "绝对不要直接在原配置上单向降价（会让客户觉得报价水分极大）；",
                "提供减配降本方案（如 20mm 改 18mm，或标准磨边替代复杂法国边）；",
                "用订货量置换：整柜 27 吨装满平摊海运费，给予 3-5% 阶梯返点；",
            ],
            "response_en": (
                "Dear Partner, thank you for your candid feedback.\n\n"
                "In building materials, price is always directly tied to the raw block grade, strict thickness tolerance (±0.5mm vs others' ±1.5mm), and reinforced export wooden bundling that withstands 30-day sea journeys without chipping.\n\n"
                "If budget constraint is currently your top priority, we have two viable solutions:\n"
                "1. Value Engineering: Adjusting slab thickness from 20mm to 18mm, reducing product cost by 8-10% while fully meeting standard structural tensile requirements.\n"
                "2. Volume Optimization: Consolidating to 2 full 20GP containers (27 tons each) to lower your average sea freight per square meter by $1.80/m².\n\n"
                "Could we review your exact site specifications to tailor the best balance between cost and performance?"
            ),
            "response_cn": (
                "剖析 BOM 成本与厚度/公差标准。提供【价值工程方案】（微调厚度/工艺）或【起订量增益方案】（整柜装满摊薄海运费）。"
            ),
        },
        "long_oa": {
            "key": "long_oa",
            "name_cn": "索要长账期 (O/A 60/90 Days)",
            "name_en": "We require O/A 60 or 90 days after B/L date",
            "psychology": "试图将资金占用与汇率风险转嫁给中国工厂，新客户直接要 OA 存在极高的国际欺诈和坏账风险。",
            "bottom_line_rules": [
                "首笔订单坚决不做纯 O/A（中国出口信用保险公司中信保未批复额度前严禁放行）；",
                "首选置换为即期不可撤销信用证 (100% Irrevocable L/C at Sight)；",
                "次选 T/T 30% 定金 + 70% 见正本提单 Copy 见款电放。",
            ],
            "response_en": (
                "We completely understand your focus on working capital flexibility.\n\n"
                "As an enterprise listed on the state export registry, our internal compliance and Sinosure (China Export & Credit Insurance Corporation) mandate that for initial transactions, we utilize 100% Irrevocable Letter of Credit (L/C at Sight) issued by a top-tier international bank, or standard 30% T/T deposit with balance against B/L copy.\n\n"
                "Once our initial cooperation is successfully concluded, we will gladly apply for a revolving credit limit under Sinosure to offer you 60-day open account terms for subsequent regular shipments.\n\n"
                "Shall we draft the initial proforma invoice on L/C at Sight to protect both parties' security?"
            ),
            "response_cn": (
                "首单搬出中信保合规红线，将 O/A 引导为即期信用证 (L/C at sight) 或标准定金，并承诺老客后续向中信保申请额度。"
            ),
        },
        "quality_cert": {
            "key": "quality_cert",
            "name_cn": "质疑质量与认证 (Certifications & Quality)",
            "name_en": "How do you guarantee quality and batch color uniformity?",
            "psychology": "担心货不对板、暗裂、色差超标、无法通过目的港海关检验（如沙特 SABER、欧洲 CE）。",
            "bottom_line_rules": [
                "出示经官方核验的检测报告 (SGS / Intertek / TÜV) 与 SABER PCoC 证书；",
                "支持由客户指定的第三方检验机构到厂进行装柜前独立验货 (PSI)；",
                "合同中明确注明公差范围，不虚假夸大。",
            ],
            "response_en": (
                "Quality and strict adherence to international building codes are the bedrock of our business.\n\n"
                "Every production run adheres strictly to EN 14411 and ASTM standards. We invite your local inspection agent (such as SGS, Bureau Veritas, or TÜV) to conduct on-site random inspection and loading supervision at our factory prior to container sealing.\n\n"
                "Attached please find our latest official lab test certificate and SABER registration proof. Would you like us to include pre-loading photo/video sign-off clauses directly in the Sales Contract?"
            ),
            "response_cn": (
                "主动开放第三方验货 (SGS/BV)，把检验权前置在出厂装柜前，化被动为主动。"
            ),
        },
        "sample_fee": {
            "key": "sample_fee",
            "name_cn": "争议样品费与快递费 (Sample Freight Dispute)",
            "name_en": "Why should we pay for samples and international courier fees?",
            "psychology": "客户希望零成本测样，同时测试供应商的诚意与实力。",
            "bottom_line_rules": [
                "样品本身完全免费提供 (Free Samples)；",
                "国际快递费承诺在大货正式下单后全额从货款中抵扣 (100% Deductible)；",
                "若客户有 DHL/FedEx 到付账号，鼓励提供账号由我们负责包装。",
            ],
            "response_en": (
                "We are more than happy to provide our premium product samples 100% free of charge to your engineering team.\n\n"
                "Regarding the express courier fee (approx $45-$65 via DHL/FedEx), our company policy guarantees that this entire courier amount will be fully credited back and deducted from your first official container order proforma invoice.\n\n"
                "Alternatively, if you have a corporate FedEx/DHL collect account number, please share it and we will dispatch the sealed sample box within 24 hours."
            ),
            "response_cn": (
                "样品免费，运费下单 100% 抵扣大货款，既筛选了严肃买家又体现了诚意。"
            ),
        },
        "existing_supplier": {
            "key": "existing_supplier",
            "name_cn": "已有固定老供应商 (Existing Supplier Locked)",
            "name_en": "We already have long-term reliable suppliers in China",
            "psychology": "转换成本高，担心试水新供应商踩坑，但潜意识里对老供应商的涨价或交期变慢有所不满。",
            "bottom_line_rules": [
                "绝不诋毁客户的老供应商；",
                "将自己定位为“战略备胎供应链 (Secondary Backup Supplier)”，防范供应链单一来源风险；",
                "提供老供应商不具备的差异化优势（如 20GP 极限制重装载或现货特快出厂）。",
            ],
            "response_en": (
                "That is wonderful to hear. Having established, reliable supply partners is the foundation of smooth operations, and we hold great respect for long-term relationships.\n\n"
                "We certainly do not expect you to replace your current suppliers overnight. Instead, top tier developers often maintain us as an active Secondary Backup Supplier to hedge against factory production bottlenecks, ocean freight spikes, or emergency stock shortages.\n\n"
                "May we simply stay on your approved vendor candidate list and share our quarterly price benchmarks so you have a valuable comparative reference?"
            ),
            "response_cn": (
                "不做非此即彼的强行替换，以“二供备份”切入，建立备用供应商档案与定期比价窗口。"
            ),
        },
        "moq_high": {
            "key": "moq_high",
            "name_cn": "起订量偏高 (MOQ Concerns)",
            "name_en": "Your MOQ is too high for our current initial trial",
            "psychology": "新项目试水，不想一次性压一个整柜的资金与库存。",
            "bottom_line_rules": [
                "解释大宗建材整柜起运的根本原因（散货拼箱 LCL 极易产生碎石破损与高昂的港口拆箱杂费）；",
                "提供【多花色/多规格混合装柜 (Mixed Container)】方案，一个 20GP 内拼 2~3 种热销花色；",
                "查询是否有发往该目的港的现有客户拼柜批次。",
            ],
            "response_en": (
                "We understand your desire to start with a prudent test batch.\n\n"
                "In building ceramics and stone slabs, shipping less than a full container load (LCL) carries a high risk of heavy forklift transit damage and disproportionate destination de-consolidation fees. \n\n"
                "To resolve your MOQ concern without exposing the tiles to breakages, we can offer a 'Mixed Container' arrangement: combining up to 2-3 compatible popular SKU specs within a single 20GP container.\n\n"
                "Would a mixed container trial fit your current warehousing schedule?"
            ),
            "response_cn": (
                "科普散货破损风险，提出【同柜混装 2-3 种花色】或寻找同港口拼柜方案。"
            ),
        },
        "urgent_delivery": {
            "key": "urgent_delivery",
            "name_cn": "交期急迫 (Urgent Lead Time)",
            "name_en": "We need the goods on site within 20 days",
            "psychology": "现场工程施工催货，工期临近延误面临甲方巨额违约罚款。",
            "bottom_line_rules": [
                "诚实评估海运船期（中国到沙特通常需 16-20 天，到欧洲需 25-30 天），严禁虚假承诺违约；",
                "调取工厂现货库存 (Ready Stock) 启动 72h 绿色装箱通道；",
                "推荐快船直达航线并预订加急拖车。",
            ],
            "response_en": (
                "We recognize the critical urgency of your project timeline and the pressure from site contractors.\n\n"
                "Pure maritime transit from Chinese ports to your destination port strictly takes 16-18 days under direct express loops. To meet your timeline, we cannot wait for custom production; however, we have 4,500 SQM of AAA-grade ready stock in standard export dimensions currently resting in our warehouse.\n\n"
                "If we finalize the proforma invoice today, we can initiate priority stuffing within 72 hours and secure the earliest vessel sailing next Tuesday.\n\n"
                "Shall we reserve this inventory batch for you immediately?"
            ),
            "response_cn": (
                "诚实告知海运客观物理周期，调度工厂现货库存，开启 72h 极速报关装柜通道。"
            ),
        },
        "ghosting": {
            "key": "ghosting",
            "name_cn": "已读不回 / 消失断联 (No Response After Quote)",
            "name_en": "Buyer stopped replying after receiving formal proforma invoice",
            "psychology": "可能在忙于内部审批、在跟其他供应商比价、或者因关键条款卡壳不好意思拒绝。",
            "bottom_line_rules": [
                "严禁发送“Did you receive my email?”这种无效催促；",
                "提供全新维度的增量价值（如海运费变动提醒、原材料保价期最后 48h、现场施工公差指导书）；",
                "给予客户体面的台阶与一键回复选择题。",
            ],
            "response_en": (
                "Dear Partner, I hope you are having a productive week.\n\n"
                "I know you have numerous urgent priorities across your construction schedule, so no need for a lengthy reply. \n\n"
                "Just wanted to flag that our ocean shipping carrier has notified us of a general rate increase effective at the end of this week. We have locked in the competitive freight rates in your proforma invoice until this Thursday.\n\n"
                "If the project timeline has shifted or if you need us to modify the specifications, just reply with '1' for Postponed, '2' for Need Revision, or '3' for Ready to Proceed.\n\n"
                "Warm regards,\nSupply Coordination Team"
            ),
            "response_cn": (
                "制造运费限时锁定契机，提供极简 1/2/3 单选回复，消除客户长篇大论沟通的心理负担。"
            ),
        },
    }

    @classmethod
    def get_objection_solution(
        cls,
        objection_key: str,
        *,
        db: Optional[Any] = None,
        tenant_id: str = "",
        inquiry_id: str = "",
    ) -> Dict[str, Any]:
        """获取指定外贸抗拒场景的专业反击战术与话术，并异步记录至进化环。"""
        clean_key = (objection_key or "price_high").strip().lower()
        solution = cls.OBJECTIONS.get(clean_key)
        if not solution:
            solution = cls.OBJECTIONS["price_high"]

        # 挂接经验环 (Evolution Engine)，沉淀谈判战术调用记录
        if db is not None:
            try:
                from app.services.acquisition.experience_feed import record_acquisition_event
                record_acquisition_event(
                    db,
                    tenant_id=tenant_id or "default_tenant",
                    event="objection_consulted",
                    inquiry_id=inquiry_id or "",
                    success=True,
                    detail=f"objection={clean_key}|strategy={solution.get('name_cn', '')}",
                    executor_id="objection_copilot",
                )
            except Exception:
                pass

        return solution

    @classmethod
    def list_all_objections(cls) -> List[Dict[str, Any]]:
        """获取全部 8 大外贸经典抗拒场景摘要。"""
        return [
            {
                "key": v["key"],
                "name_cn": v["name_cn"],
                "name_en": v["name_en"],
                "psychology": v["psychology"],
            }
            for v in cls.OBJECTIONS.values()
        ]

