# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发信生成技能 — 对应 cold-email SKILL.md。"""

from app.services.foreign_trade.skill_registry import SkillMeta, skill_registry

COLD_EMAIL_PROMPT = """你是一位资深 B2B 外贸开发信专家，擅长写出高回复率的个性化开发信。

## 客户信息
- 公司名：{company_name}
- 国家：{country}
- 行业：{industry}
- 联系人：{contact_name}（{contact_title}）
- 官网：{website}

## 你的产品优势
{product_advantages}

## 要求
1. 像同行同事一样写信，不要像销售机器
2. 开头引用客户的行业/市场/产品，体现你做过功课
3. 一句话说清你能帮他们解决什么问题
4. 用数据或案例证明价值（不要空泛承诺）
5. 结尾用低门槛 CTA（"值得聊聊吗？"优于"约个会议"）
6. 主题行 60 字以内，吸引打开

## 输出格式（JSON）
{{
  "subject": "主题行",
  "body": "正文（纯文本，用 \\n 换行）",
  "follow_up_subject": "跟进邮件主题行",
  "follow_up_body": "跟进邮件正文（3天后发送）",
  "personalization_score": 85,
  "notes": "个性化策略说明"
}}"""

COLD_EMAIL_META = SkillMeta(
    name="cold_email",
    display_name="开发信生成",
    description="根据客户画像和产品优势，生成高回复率的个性化开发信及跟进序列",
    category="outreach",
    icon="mail",
    prompt_template=COLD_EMAIL_PROMPT,
    input_schema={
        "company_name": {"type": "string", "required": True, "label": "客户公司名"},
        "country": {"type": "string", "required": True, "label": "国家"},
        "industry": {"type": "string", "required": True, "label": "行业"},
        "contact_name": {"type": "string", "required": False, "label": "联系人", "default": "Purchasing Team"},
        "contact_title": {"type": "string", "required": False, "label": "职位", "default": "Procurement Manager"},
        "website": {"type": "string", "required": False, "label": "官网", "default": ""},
        "product_advantages": {"type": "string", "required": True, "label": "产品优势"},
    },
)

skill_registry.register(COLD_EMAIL_META)
