import re

path = r'backend/app/services/hermes/planner_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

new_graph = """def _social_outreach_graph(plan_id: str, event_id: str, payload: dict[str, Any]) -> TaskGraph:
    \"\"\"社媒/WhatsApp 拓客： trade_ai_agent 履约。包含多通道降级 (WhatsApp -> Email) 和 RAG 清洗。\"\"\"
    keyword = str(payload.get("keyword") or payload.get("message") or "").strip()
    country = str(payload.get("country") or "Global").strip()
    return TaskGraph(
        plan_id=plan_id, event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(
            max_parallel=2,
            approval_required=["outreach.whatsapp", "outreach.email"],
            degradation="skip",
        ),
        nodes=[
            TaskNode(
                id="n1", executor="trade_ai_agent", capability="prospect.scrape",
                depends_on=[],
                input={"keyword": keyword, "country": country, "channel": "social"},
                on_fail="abort",
            ),
            TaskNode(
                id="n1_enrich", executor="trade_ai_agent", capability="prospect.enrich",
                depends_on=["n1"],
                input_from={"prospects": "n1.output.prospects"},
                input={"strategy": "MEDDPICC", "min_score": 60},
                on_fail="skip",
            ),
            TaskNode(
                id="n2_wa", executor="trade_ai_agent", capability="outreach.whatsapp",
                depends_on=["n1_enrich"],
                input_from={"prospects": "n1_enrich.output.prospects"},
                input={"country": country, "locale": payload.get("locale") or "en", "human_send_required": True},
                on_fail="skip",
                budget={"max_tokens": 20000},
            ),
            TaskNode(
                id="n2_email", executor="trade_ai_agent", capability="outreach.email",
                depends_on=["n1_enrich"],
                input_from={"prospects": "n1_enrich.output.prospects"},
                input={"country": country, "locale": payload.get("locale") or "en", "fallback_from": "n2_wa"},
                condition="n2_wa.status == 'failed' or n2_wa.status == 'degraded'",
                on_fail="skip",
                budget={"max_tokens": 20000},
            ),
            TaskNode(
                id="n3", executor="trade_ai_agent", capability="inbox.classify",
                depends_on=["n2_wa", "n2_email"],
                input={"purpose": "acquisition_reply_triage"},
                on_fail="skip",
            ),
        ],
    )"""

text = re.sub(r'def _social_outreach_graph.*?return TaskGraph\([^\)]+\]\,\n    \)', new_graph, text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
