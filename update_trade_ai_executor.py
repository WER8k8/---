import os

path = r'backend/app/services/hermes/executors/trade_ai_agent_executor.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '"prospect.enrich",\n',
    '"prospect.enrich", "scraper", "prospecting", "lead-research-assistant", "data_cleaner",\n'
)
text = text.replace(
    '"outreach.whatsapp", "whatsapp_send",\n',
    '"outreach.whatsapp", "whatsapp_send", "auto_sender", "social",\n'
)
text = text.replace(
    '"outreach.email", "email_campaign", "cold_email",\n',
    '"outreach.email", "email_campaign", "cold_email", "emails",\n'
)
text = text.replace(
    '"inbox.classify", "intent_classify",\n',
    '"inbox.classify", "intent_classify", "ai_reply", "rag",\n'
)

text = text.replace(
    'capability in ("prospect.scrape", "prospect_search", "scrape_prospects", "prospect.enrich"):',
    'capability in ("prospect.scrape", "prospect_search", "scrape_prospects", "prospect.enrich", "scraper", "prospecting", "lead-research-assistant", "data_cleaner"):'
)
text = text.replace(
    'capability in ("outreach.whatsapp", "whatsapp_send"):',
    'capability in ("outreach.whatsapp", "whatsapp_send", "auto_sender", "social"):'
)
text = text.replace(
    'capability in ("outreach.email", "email_campaign", "cold_email"):',
    'capability in ("outreach.email", "email_campaign", "cold_email", "emails"):'
)

# For inbox classify we don't have it directly in the trade_ai_agent_executor yet! Let's check if it exists.
if 'capability in ("inbox.classify", "intent_classify"):' in text:
    text = text.replace(
        'capability in ("inbox.classify", "intent_classify"):',
        'capability in ("inbox.classify", "intent_classify", "ai_reply", "rag"):'
    )
else:
    # Add it
    new_block = """
        if capability in ("inbox.classify", "intent_classify", "ai_reply", "rag"):
            out = native.classify_inbox(
                tenant_id=context.tenant_id,
                message=str(params.get("message") or ""),
                contact_id=str(params.get("contact_id") or "") or None,
                db=db,
                params=params,
            )
            return ExecutorResult(
                node_id=node.id,
                status="succeeded" if out.get("success") else "failed",
                output={**out, "executor": self.get_executor_name(), "capability": capability},
                error=None if out.get("success") else str(out.get("error") or "native_classify_failed"),
            )
"""
    # Insert before the last return
    text = text.replace('        return ExecutorResult(\n            node_id=node.id,\n            status="skipped",\n            output={"capability": capability},\n            error=f"Unimplemented trade_ai_agent capability={capability}",\n        )', new_block + '\n        return ExecutorResult(\n            node_id=node.id,\n            status="skipped",\n            output={"capability": capability},\n            error=f"Unimplemented trade_ai_agent capability={capability}",\n        )')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
