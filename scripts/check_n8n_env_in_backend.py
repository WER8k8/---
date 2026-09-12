import os

print("=== Environment Variables ===")
print(f"N8N_WEBHOOK_SECRET: '{os.getenv('N8N_WEBHOOK_SECRET', '')}'")
print(f"N8N_WEBHOOK_SECRET (repr): {repr(os.getenv('N8N_WEBHOOK_SECRET', ''))}")
print(f"MEM0_API_URL: '{os.getenv('MEM0_API_URL', '')}'")
print(f"POSTHOG_PROJECT_API_KEY: '{os.getenv('POSTHOG_PROJECT_API_KEY', '')}'")
print(f"DEERFLOW_SIDECAR_URL: '{os.getenv('DEERFLOW_SIDECAR_URL', '')}'")

print("\n=== Checking if N8N_WEBHOOK_SECRET is truthy ===")
n8n_secret = (os.getenv("N8N_WEBHOOK_SECRET") or "").strip()
print(f"n8n_secret after strip: '{n8n_secret}'")
print(f"bool(n8n_secret): {bool(n8n_secret)}")