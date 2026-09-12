import re

path = r"c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend\config\dev\.env"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

env_vars = {}
pattern = re.compile(r'^\s*([^#][^=]+)=(.*)$')

for i, line in enumerate(lines):
    match = pattern.match(line)
    if match:
        k = match.group(1).strip()
        v = match.group(2).strip()
        env_vars[k] = v
        if k.startswith('N8N') or k.startswith('MEM0') or k.startswith('POSTHOG') or k.startswith('DEERFLOW'):
            print(f"Line {i+1}: {k}={v}")

print(f"\nTotal env vars loaded: {len(env_vars)}")
print(f"N8N_WEBHOOK_SECRET in env_vars: {'N8N_WEBHOOK_SECRET' in env_vars}")
print(f"MEM0_API_URL in env_vars: {'MEM0_API_URL' in env_vars}")