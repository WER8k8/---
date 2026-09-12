"""AI 开发信生成 — FIX-48

基于客户画像自动生成个性化开发信：
- 模板变量替换
- AI 内容生成（基于 LLM）
- A/B 测试变体生成
- 质量评估
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    """邮件模板。"""
    id: str
    name: str
    name_cn: str
    subject: str
    body: str
    category: str
    tone: str  # professional, casual, friendly, bold
    variables: list[str] = field(default_factory=list)
    best_for: str = ""


# 预置邮件模板
EMAIL_TEMPLATES: dict[str, EmailTemplate] = {
    "intro-professional": EmailTemplate(
        id="intro-professional",
        name="Professional Introduction",
        name_cn="专业介绍型",
        subject="Exploring partnership opportunities with {company_name}",
        body="""Dear {first_name},

I hope this email finds you well. I've been following {company_name}'s work in the {industry} sector and am impressed by your {highlight}.

I'm reaching out from {sender_company}, where we specialize in helping {industry} companies {value_proposition}.

We've recently helped {similar_company} achieve {specific_result}, and I believe we could deliver similar results for {company_name}.

Would you be open to a brief call next week to explore potential collaboration?

Best regards,
{sender_name}
{sender_title}
{sender_company}""",
        category="outreach",
        tone="professional",
        variables=["first_name", "company_name", "industry", "highlight", "sender_company", "value_proposition", "similar_company", "specific_result", "sender_name", "sender_title"],
        best_for="B2B制造企业初次接触",
    ),
    "intro-casual": EmailTemplate(
        id="intro-casual",
        name="Casual Introduction",
        name_cn="轻松介绍型",
        subject="Quick question about {company_name}",
        body="""Hi {first_name},

I came across {company_name} and noticed you're doing some interesting things in {industry}.

Quick question: how are you currently handling {pain_point}?

We've built a solution that helps companies like yours {benefit}. Happy to share more if you're interested.

{sender_name}""",
        category="outreach",
        tone="casual",
        variables=["first_name", "company_name", "industry", "pain_point", "benefit", "sender_name"],
        best_for="SOHO/小型外贸企业",
    ),
    "follow-up-value": EmailTemplate(
        id="follow-up-value",
        name="Value Follow-up",
        name_cn="价值跟进型",
        subject="Thought you'd find this useful: {topic}",
        body="""Hi {first_name},

I recently put together some research on {topic} that I think would be relevant for {company_name}.

Key insight: {key_insight}

No pitch — just thought you might find it valuable. Let me know if you'd like me to send over the full analysis.

{sender_name}""",
        category="followup",
        tone="professional",
        variables=["first_name", "company_name", "topic", "key_insight", "sender_name"],
        best_for="跟进邮件（提供价值而非硬推销）",
    ),
    "case-study": EmailTemplate(
        id="case-study",
        name="Case Study Share",
        name_cn="案例分享型",
        subject="How {similar_company} achieved {result}",
        body="""Hi {first_name},

I thought you might be interested in how {similar_company}, a {industry} company similar to {company_name}, achieved {result} using our platform.

Here's a quick overview:
- Challenge: {challenge}
- Solution: {solution}
- Result: {result}

Would you like me to share the full case study?

{sender_name}""",
        category="followup",
        tone="professional",
        variables=["first_name", "company_name", "industry", "similar_company", "challenge", "solution", "result", "sender_name"],
        best_for="分享成功案例建立信任",
    ),
    "last-attempt": EmailTemplate(
        id="last-attempt",
        name="Last Attempt",
        name_cn="最后尝试型",
        subject="Closing the loop: {company_name}",
        body="""Hi {first_name},

I've reached out a few times and haven't heard back — totally understand, you're busy.

I'll keep this brief: if {pain_point} is something you're thinking about, I'm here to help. If not, no worries at all.

Either way, I've attached a free resource on {resource_topic} that I hope you find useful.

Wishing you and {company_name} all the best.

{sender_name}""",
        category="followup",
        tone="friendly",
        variables=["first_name", "company_name", "pain_point", "resource_topic", "sender_name"],
        best_for="序列最后一步，礼貌退出",
    ),
    "referral-ask": EmailTemplate(
        id="referral-ask",
        name="Referral Request",
        name_cn="推荐请求型",
        subject="Question about {industry} connections",
        body="""Hi {first_name},

I hope you're doing well! I was wondering if you might know anyone in the {industry} space who's looking to {goal}.

We specialize in {value_proposition}, and we're always looking to connect with the right people.

If anyone comes to mind, I'd really appreciate an introduction. And of course, I'm happy to return the favor!

{sender_name}""",
        category="networking",
        tone="friendly",
        variables=["first_name", "industry", "goal", "value_proposition", "sender_name"],
        best_for="请求推荐和转介绍",
    ),
}


class AIEmailGenerator:
    """AI 开发信生成器。"""
    @staticmethod
    def get_templates(category: Optional[str] = None, tone: Optional[str] = None) -> list[dict]:
        """获取模板列表。"""
        templates = list(EMAIL_TEMPLATES.values())
        if category:
            templates = [t for t in templates if t.category == category]
        if tone:
            templates = [t for t in templates if t.tone == tone]
        return [
            {
                "id": t.id,
                "name": t.name,
                "name_cn": t.name_cn,
                "subject": t.subject,
                "category": t.category,
                "tone": t.tone,
                "best_for": t.best_for,
                "variables": t.variables,
            }
            for t in templates
        ]

    @staticmethod
    def render(
        template_id: str,
        variables: dict[str, str],
    ) -> dict:
        """渲染邮件模板。

        Args:
            template_id: 模板ID
            variables: 变量值字典

        Returns:
            {"subject": str, "body": str}
        """
        template = EMAIL_TEMPLATES.get(template_id)
        if not template:
            return {"error": f"模板不存在: {template_id}"}

        subject = template.subject
        body = template.body
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))

        # 检查未替换的变量
        import re
        missing = set(re.findall(r"\{(\w+)\}", subject + body))
        missing = missing - set(variables.keys())
        return {
            "template_id": template_id,
            "subject": subject,
            "body": body,
            "missing_variables": list(missing) if missing else [],
            "is_complete": len(missing) == 0,
        }

    @staticmethod
    async def generate_with_ai(
        lead_data: dict[str, Any],
        template_id: Optional[str] = None,
        tone: str = "professional",
        language: str = "en",
    ) -> dict:
        """使用 AI 生成个性化开发信。

        当有 LLM 可用时，调用 AI 生成；否则使用模板渲染。
        """
        try:
            # 尝试使用 AI 生成
            from app.services.ubrain.ubrain_service import UbrainService
            prompt = AIEmailGenerator._build_prompt(lead_data, tone, language)
            ai_result = await UbrainService.generate_text(prompt, max_tokens=500)
            if ai_result:
                # 解析 AI 生成的邮件
                subject, body = AIEmailGenerator._parse_ai_response(ai_result)
                return {
                    "method": "ai",
                    "subject": subject,
                    "body": body,
                    "lead_data": lead_data,
                }
        except Exception as e:
            log.warning("[AI Email] AI 生成失败，回退到模板: %s", e)

        # 回退到模板渲染
        if template_id:
            return AIEmailGenerator.render(template_id, _extract_variables(lead_data))

        return {
            "method": "fallback",
            "subject": f"Exploring opportunities with {lead_data.get('company', 'your company')}",
            "body": "AI generation unavailable. Please use a template.",
        }

    @staticmethod
    def generate_ab_variants(
        template_id: str,
        variables: dict[str, str],
        num_variants: int = 2,
    ) -> list[dict]:
        """生成 A/B 测试变体。

        基于同一模板，通过调整语气、开头、CTA 等生成多个变体。
        """
        base = AIEmailGenerator.render(template_id, variables)
        variants = [base]
        # 变体策略
        strategies = [
            {"name": "原版", "modify": lambda s, b: (s, b)},
            {
                "name": "短版",
                "modify": lambda s, b: (
                    s.replace("Exploring partnership opportunities", "Partnership opportunity"),
                    "\n".join(b.split("\n")[:len(b.split("\n")) // 2]) + "\n\nBest,\n" + variables.get("sender_name", ""),
                ),
            },
            {
                "name": "问题开头",
                "modify": lambda s, b: (
                    s,
                    b.replace(
                        f"Dear {variables.get('first_name', 'there')},",
                        f"Hi {variables.get('first_name', 'there')},\n\nQuick question: how are you handling {variables.get('pain_point', 'lead generation')}?",
                    ),
                ),
            },
            {
                "name": "数据驱动",
                "modify": lambda s, b: (
                    s,
                    b.replace(
                        f"Dear {variables.get('first_name', 'there')},",
                        f"Hi {variables.get('first_name', 'there')},\n\nDid you know that {variables.get('industry', 'B2B')} companies using AI-powered outreach see {variables.get('stat', '3x')} more replies?",
                    ),
                ),
            },
        ]
        for strategy in strategies[1:num_variants]:
            new_subject, new_body = strategy["modify"](base["subject"], base["body"])
            variants.append({
                "template_id": template_id,
                "variant": strategy["name"],
                "subject": new_subject,
                "body": new_body,
            })

        return variants[:num_variants]

    @staticmethod
    def _build_prompt(lead_data: dict, tone: str, language: str) -> str:
        """构建 AI 提示词。"""
        return f"""Write a {tone} cold outreach email to a potential B2B client.

Recipient Info:
- Name: {lead_data.get('first_name', 'there')} {lead_data.get('last_name', '')}
- Title: {lead_data.get('title', '')}
- Company: {lead_data.get('company', '')}
- Industry: {lead_data.get('industry', '')}
- Country: {lead_data.get('country', '')}

Context:
- We help {lead_data.get('industry', 'B2B')} companies with lead generation, SEO, and digital marketing.
- Our value proposition: AI-powered overseas growth platform.

Requirements:
- Language: {language}
- Tone: {tone}
- Length: 100-150 words
- Include a clear call-to-action
- No spammy language
- Personalize based on the recipient's info

Format the response as:
SUBJECT: [subject line]
BODY: [email body]"""

    @staticmethod
    def _parse_ai_response(response: str) -> tuple[str, str]:
        """解析 AI 响应。"""
        subject = ""
        body = response
        lines = response.strip().split("\n")
        for i, line in enumerate(lines):
            if line.upper().startswith("SUBJECT:"):
                subject = line.split(":", 1)[1].strip()
                body = "\n".join(lines[i + 1:]).strip()
                break

        if body.upper().startswith("BODY:"):
            body = body.split(":", 1)[1].strip()

        return subject, body


def _extract_variables(lead_data: dict) -> dict[str, str]:
    """从线索数据提取模板变量。"""
    return {
        "first_name": lead_data.get("first_name", lead_data.get("name", "there")),
        "last_name": lead_data.get("last_name", ""),
        "company_name": lead_data.get("company", "your company"),
        "industry": lead_data.get("industry", "your industry"),
        "pain_point": "lead generation and overseas marketing",
        "benefit": "increase qualified leads by 3x",
        "value_proposition": "AI-powered overseas growth",
        "sender_name": "Your Name",
        "sender_title": "Business Development",
        "sender_company": "UJ China",
        "highlight": "recent growth",
        "similar_company": "a similar company in your space",
        "specific_result": "200% increase in qualified leads",
        "result": "200% increase in qualified leads",
        "challenge": "limited overseas marketing resources",
        "solution": "AI-powered automated outreach",
        "goal": "expand overseas",
        "topic": "B2B overseas marketing trends",
        "key_insight": "AI-powered outreach generates 3x more replies than manual methods",
        "resource_topic": "B2B overseas marketing guide",
        "stat": "3x",
    }