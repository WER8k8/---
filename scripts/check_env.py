import os

print("N8N_WEBHOOK_SECRET:", repr(os.getenv("N8N_WEBHOOK_SECRET", "")))
print("MEM0_API_URL:", repr(os.getenv("MEM0_API_URL", "")))
print("POSTHOG_PROJECT_API_KEY:", repr(os.getenv("POSTHOG_PROJECT_API_KEY", "")))
print("DEERFLOW_SIDECAR_URL:", repr(os.getenv("DEERFLOW_SIDECAR_URL", "")))