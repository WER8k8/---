import os
import time
from pathlib import Path

import httpx

key = ""
env_path = Path(__file__).resolve().parents[1] / "backend" / "config" / "dev" / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("AI_NVIDIA_API_KEY="):
        key = line.split("=", 1)[1].strip()
        break

base = "https://integrate.api.nvidia.com/v1"
print("KEY", key[:15], "len", len(key))

r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
print("GET /models", r.status_code, "count", len(r.json().get("data", [])))

tests = [
    ("deepseek-ai/deepseek-v4-flash", "CORRECT"),
    ("deepseek/deepseek-v4-flash", "WRONG prefix"),
    ("meta/llama-3.1-8b-instruct", "CORRECT fast"),
    ("deepseek/deepseek-v4-pro", "WRONG in Cursor"),
]

for model, note in tests:
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "ok"}], "max_tokens": 5},
            timeout=30,
        )
        dt = round(time.time() - t0, 1)
        print(f"{note:20} {model:40} {resp.status_code} {dt}s {resp.text[:100]}")
    except Exception as e:
        print(f"{note:20} {model:40} FAIL {round(time.time()-t0,1)}s {e}")
