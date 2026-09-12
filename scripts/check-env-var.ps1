$pythonScript = @'
import os
print(f"N8N_WEBHOOK_SECRET: '{os.getenv('N8N_WEBHOOK_SECRET', '')}'")
print(f"MEM0_API_URL: '{os.getenv('MEM0_API_URL', '')}'")
print(f"POSTHOG_PROJECT_API_KEY: '{os.getenv('POSTHOG_PROJECT_API_KEY', '')}'")
print(f"DEERFLOW_SIDECAR_URL: '{os.getenv('DEERFLOW_SIDECAR_URL', '')}'")
'@

cd c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend
python -c $pythonScript