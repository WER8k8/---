import re

path = r'backend/app/services/trade_fulfillment_store.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add provenance_metadata param to persist_whatsapp_message
text = re.sub(r'(def persist_whatsapp_message\([\s\S]*?lead_id: Optional\[str\] = None,)', r'\1\n    provenance_metadata: Optional[dict] = None,', text)
text = text.replace(
    'inquiry_id=inquiry_id,\n        lead_id=lead_id,\n    )',
    'inquiry_id=inquiry_id,\n        lead_id=lead_id,\n        provenance_metadata=provenance_metadata,\n    )'
)

# Add provenance_metadata param to persist_contact_event
text = re.sub(r'(def persist_contact_event\([\s\S]*?payload: Optional\[dict\] = None,)', r'\1\n    provenance_metadata: Optional[dict] = None,', text)
text = text.replace(
    'summary=summary,\n        payload_json=json.dumps(payload) if payload else "{}",\n    )',
    'summary=summary,\n        payload_json=json.dumps(payload) if payload else "{}",\n        provenance_metadata=provenance_metadata,\n    )'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
