import re

path = r'backend/app/services/tradeai/native_acquisition.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import_str = "from app.core.audit_logger import AuditLogger\n"
if import_str not in text:
    text = text.replace("import os\n", "import os\n" + import_str)

# In outreach_whatsapp
wa_log = """
    AuditLogger.log_event(
        event_type="OUTBOUND_WHATSAPP",
        actor="system",
        action="whatsapp_send_attempt",
        details={"phone": phone, "message": message, "success": out["success"]}
    )
"""
text = text.replace(
    'out["note"] = "模拟 sent (无 WhatsApp Key)"\n',
    'out["note"] = "模拟 sent (无 WhatsApp Key)"\n' + wa_log
)
text = text.replace(
    'out["note"] = "原生发出 (需真实网关)"\n',
    'out["note"] = "原生发出 (需真实网关)"\n' + wa_log
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
