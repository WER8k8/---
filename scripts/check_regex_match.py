import re

lines = [
    'N8N_WEBHOOK_SECRET=dev-n8n-webhook-secret-change-in-production',
    'MEM0_API_URL=https://api.mem0.ai',
]

pattern = r'^\s*([^#][^=]+)=(.*)$'

for line in lines:
    match = re.match(pattern, line)
    print(f"Line: {repr(line)}")
    print(f"Match: {match}")
    if match:
        print(f"  k={repr(match.group(1).strip())}")
        print(f"  v={repr(match.group(2).strip())}")
    print()