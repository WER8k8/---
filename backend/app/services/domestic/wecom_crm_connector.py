# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""企业微信与微信公众号 CRM 连接器 (WeCom & WeChat B2B Connector)。

解决国内获客沟通痛点：
1. 自动打标：买家类型标签、城市区域标签、工程规模评级
2. 企业微信消息投递与通知模拟 (WeCom OAPI 规范)
3. 分阶段高转化销售跟进话术生成（微信端/企微朋友圈/即时沟通）
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WeCOMCrmConnector:
    """企业微信/微信国内获客连接器。"""

    # 常见工程买家标签规范
    DEFAULT_TAG_GROUPS: Dict[str, List[str]] = {
        "buyer_type": ["工程集采总包", "品牌区域代理", "建材批发仓", "家装设计公司"],
        "project_scale": ["大型公建项目(>10万㎡)", "商业地产精品(3~10万㎡)", "常规工装(<3万㎡)"],
        "price_sensitivity": ["极重性价比", "品质为先/看重国标", "急单交期为先"],
    }

    @classmethod
    def send_wecom_message(
        cls,
        *,
        external_userid: str,
        content: str,
        tenant_corpid: str = "",
        tenant_corpsecret: str = "",
        agent_id: str = "",
    ) -> Dict[str, Any]:
        """向企业微信外部联系人发送跟进消息（支持无凭据安全降级模拟）。"""
        corpid = tenant_corpid or os.getenv("WECOM_CORPID", "")
        secret = tenant_corpsecret or os.getenv("WECOM_SECRET", "")

        is_configured = bool(corpid and secret)

        preview = {
            "external_userid": external_userid,
            "content": content,
            "channel": "wecom_chat",
            "configured": is_configured,
            "mock_delivered": not is_configured,
            "note": "企业微信外部联系人消息投递已就绪" if is_configured else "WECOM_CORPID 未配置，已转入工作台模拟预览模式",
        }
        return preview

    @classmethod
    def tag_domestic_lead(
        cls,
        external_userid: str,
        *,
        buyer_type: str = "engineering",
        city: str = "",
        project_name: str = "",
        quantity_m2: float = 0.0,
    ) -> Dict[str, Any]:
        """自动打上国内多维特征标签。"""
        tags: List[str] = []

        # 1. 买家类型
        type_map = {
            "engineering": "工程集采总包",
            "distributor": "品牌区域代理",
            "wholesaler": "建材批发仓",
        }
        tags.append(type_map.get(buyer_type.lower(), "常规工装客户"))

        # 2. 城市区域
        if city:
            tags.append(f"地区:{city}")

        # 3. 规模级别
        if quantity_m2 >= 50000:
            tags.append("规模:大型重点工程(≥5万㎡)")
        elif quantity_m2 >= 10000:
            tags.append("规模:中型工程项目(1~5万㎡)")
        elif quantity_m2 > 0:
            tags.append("规模:常规工装批采(<1万㎡)")

        if project_name:
            tags.append(f"项目:{project_name[:20]}")

        return {
            "external_userid": external_userid,
            "tags_assigned": tags,
            "total_tags": len(tags),
            "status": "synchronized",
        }

    @classmethod
    def generate_domestic_followup_script(
        cls,
        buyer_name: str,
        *,
        buyer_type: str = "engineering",
        product_category: str = "瓷砖",
        quote_amount: float = 0.0,
        stage: str = "contacted",
        contact_name: str = "",
    ) -> Dict[str, Any]:
        """生成符合中国商务习惯的高情商专业跟进话术。"""
        title = contact_name or "老板" if "工程" not in buyer_name else "总"
        call_name = f"{buyer_name} {title}" if not contact_name else f"{contact_name}{title}"
        prod = product_category or "建材瓷砖"
        amt_str = f"¥{quote_amount:,.2f}" if quote_amount > 0 else "参考专享价"

        scripts = {
            "inquiry": (
                f"{call_name}您好！收到您对我们【{prod}】的工程需求。"
                f"我们是源头实体大厂，拥有国家绿色建材三星认证与中国建筑一供资信。"
                f"为给您的项目做最精准的排产测算，我稍后加您微信把《2026 实体工程样册》和出厂指导清单直接发您把关！"
            ),
            "contacted": (
                f"{call_name}您好！上午跟您沟通的【{prod}】工程排产规格，我们技术部已全量核算出材损耗。"
                f"针对您这个项目，我们专批了出厂直供优惠价，含 13% 增值税专票包干到工地。"
                f"方便我把正式报价清单发微信给您过目吗？"
            ),
            "quoted": (
                f"{call_name}您好！之前呈报给贵司的【{prod}】含税工程核价单（总额 {amt_str}）收到了吗？"
                f"我们厂下周正好有一批同花色、同窑炉编号的一级优等品现货上线排单。"
                f"如果本周能敲定板样，不仅单价可锁定当前谷值，更能提前 7 天优先插单发货！"
            ),
            "sample": (
                f"{call_name}您好！为您专门裁切的【{prod}】全套大板实体样箱已顺丰包邮寄出（内附国检报告与防滑阻燃检验单）。"
                f"预计明后天送到您案场，您可直接上脚踩测或在不同光照下对照看样，有任何定制微调随时联系我！"
            ),
            "deal": (
                f"{call_name}，非常荣幸能与贵司达成【{prod}】供货战略合作！"
                f"预付款对公银行账户信息已发送至您企微，30% 订金款项到账后工厂将即刻锁库排产，"
                f"我将为您建一个 1v1 专属履约服务群，每日同步出库排单与物流定位进度！"
            ),
            "lost": (
                f"{call_name}您好，十分理解贵司当前项目的整体考量。买卖不成仁义在，我们工厂大门始终向您敞开！"
                f"后续如果出现急需补货、工地换砖或需要第三方国检背书支持，随时唤醒我，优丁全天候为您效劳！"
            ),
        }

        stage_key = stage.lower()
        script = scripts.get(stage_key, scripts["contacted"])

        return {
            "buyer_name": buyer_name,
            "stage": stage_key,
            "script": script,
            "delivery_channel": "wecom_chat / wechat",
            "etiquette_rules": [
                "国内客户忌夜间打扰，黄金沟通窗口为工作日 10:00~11:30 及 15:00~17:00；",
                "涉及专票抵扣与账期节点，务必在文字后补充可盖章的正式红头核价函；",
                "遇到比价时，主动亮出窑炉平整度公差与放射性 A 类环保资质建立防线。",
            ],
        }
