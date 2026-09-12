"""实测 NVIDIA 代码模型可用性，输出可用列表。"""
import time
from pathlib import Path

import httpx

CANDIDATES = [
    "qwen/qwen3-coder-480b-a35b-instruct",
    "deepseek-ai/deepseek-v4-pro",
    "deepseek-ai/deepseek-v4-flash",
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "mistralai/codestral-22b-instruct-v0.1",
    "qwen/qwen3.5-397b-a17b",
    "qwen/qwen3.5-122b-a10b",
    "qwen/qwen3-next-80b-a3b-instruct",
    "nvidia/nemotron-3-super-120b-a12b",
    "openai/gpt-oss-120b",
    "meta/codellama-70b",
    "ibm/granite-34b-code-instruct",
    "mistralai/mistral-medium-3.5-128b",
    "mistralai/mixtral-8x22b-v0.1",
    "z-ai/glm-5.1",
    "moonshotai/kimi-k2.6",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-4-maverick-17b-128e-instruct",
    "stepfun-ai/step-3.7-flash",
    "minimaxai/minimax-m2.7",
]

env_path = Path(__file__).resolve().parents[1] / "backend" / "config" / "dev" / ".env"
key = ""
for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("AI_NVIDIA_API_KEY="):
        key = line.split("=", 1)[1].strip()
        break

base = "https://integrate.api.nvidia.com/v1"
ok_list = []
for model in CANDIDATES:
    t0 = time.time()
    try:
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Write one line Python: print(42)"}],
                "max_tokens": 40,
            },
            timeout=45,
        )
        dt = round(time.time() - t0, 1)
        if r.status_code == 200:
            ok_list.append((model, dt))
            print(f"OK  {dt:5}s  {model}")
        else:
            print(f"ERR {dt:5}s  {model}  {r.status_code}")
    except Exception as e:
        print(f"FAIL {round(time.time()-t0,1):5}s  {model}  {type(e).__name__}")

print("\n--- WORKING ---")
for m, dt in sorted(ok_list, key=lambda x: x[1]):
    print(f"{dt}s\t{m}")
