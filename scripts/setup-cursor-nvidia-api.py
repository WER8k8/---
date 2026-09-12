import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

APP_USER_KEY = (
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl."
    "persistentStorage.applicationUser"
)
OPENAI_KEY = "cursorAuth/openAIKey"

# 走本地代理（scripts/nvidia-cursor-proxy.py）→ 映射到 NVIDIA 强代码模型
PROXY_BASE_URL = "http://127.0.0.1:8765/v1"

# Cursor 服务端认得的别名（勿用 mistralai/xxx，会报 Model name is not valid）
CURSOR_MODELS = [
    "gpt-4o",           # → mistral-large-3 675B
    "gpt-4o-mini",      # → deepseek-v4-flash
    "gpt-4-turbo",    # → qwen3-coder 480B
    "o1-mini",          # → llama-3.3-70b
    "gpt-4.1",          # → llama-4-maverick
    "gpt-4.1-mini",     # → nemotron-3-super-120b
]

DEFAULT_MODEL = "gpt-4o"
FALLBACK_CHAIN = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"]


def load_api_key(explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    env_path = Path(__file__).resolve().parents[1] / "backend" / "config" / "dev" / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("AI_NVIDIA_API_KEY="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    raise SystemExit("未找到 NVIDIA API Key。")


def is_nvidia_vendor_model(model_id: str) -> bool:
    return "/" in model_id and not model_id.startswith("us.")


def merge_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def model_entry(model_id: str) -> dict:
    return {
        "modelName": model_id,
        "maxMode": False,
        "selectedModels": [{"modelId": model_id, "parameters": []}],
    }


def apply_routing(data: dict) -> None:
    ai = data.setdefault("aiSettings", {})
    ai["modelDefaultSwitchOnNewChat"] = False
    entry = model_entry(DEFAULT_MODEL)
    for section in (
        "composer",
        "cmd-k",
        "plan-execution",
        "quick-agent",
        "background-composer",
        "composer-ensemble",
        "spec",
        "deep-search",
    ):
        ai.setdefault("modelConfig", {})[section] = dict(entry)

    routing = {
        "defaultModel": DEFAULT_MODEL,
        "fallbackModels": list(FALLBACK_CHAIN),
        "bestOfNDefaultModels": [],
    }
    fmc = data.setdefault("featureModelConfigs", {})
    for key in (
        "composer",
        "cmdK",
        "planExecution",
        "quickAgent",
        "backgroundComposer",
        "spec",
        "deepSearch",
    ):
        fmc[key] = dict(routing)

    data["nvidiaRouting"] = {
        "mode": "local-proxy",
        "proxyUrl": PROXY_BASE_URL,
        "default": DEFAULT_MODEL,
        "mapScript": "scripts/nvidia-cursor-proxy.py",
    }


def main() -> int:
    api_key = load_api_key(sys.argv[1] if len(sys.argv) > 1 else None)

    db_path = Path(os.environ["APPDATA"]) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    if not db_path.exists():
        raise SystemExit(f"找不到 Cursor 配置: {db_path}")

    backup = db_path.with_name(
        f"state.vscdb.bak-nvidia-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy2(db_path, backup)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO ItemTable(key, value) VALUES(?, ?)",
        (OPENAI_KEY, api_key),
    )

    row = cur.execute("SELECT value FROM ItemTable WHERE key=?", (APP_USER_KEY,)).fetchone()
    data = json.loads(row[0])
    data["useOpenAIKey"] = True
    data["openAIBaseUrl"] = PROXY_BASE_URL

    ai = data.setdefault("aiSettings", {})
    kept = [m for m in ai.get("userAddedModels", []) if not is_nvidia_vendor_model(m)]
    ai["userAddedModels"] = merge_unique(kept + CURSOR_MODELS)
    ai["modelOverrideEnabled"] = merge_unique(CURSOR_MODELS)
    apply_routing(data)

    cur.execute(
        "INSERT OR REPLACE INTO ItemTable(key, value) VALUES(?, ?)",
        (APP_USER_KEY, json.dumps(data, ensure_ascii=False, separators=(",", ":"))),
    )
    conn.commit()
    conn.close()

    print("Cursor 已切到本地代理模式（绕过 Model name is not valid）")
    print(f"  1. 先运行: powershell -File scripts/start-nvidia-cursor-proxy.ps1")
    print(f"  2. Base URL: {PROXY_BASE_URL}")
    print(f"  3. 默认模型: {DEFAULT_MODEL} (= Mistral Large 3 675B)")
    print("  4. gpt-4o-mini = DeepSeek V4 Flash | gpt-4-turbo = Qwen3 Coder 480B")
    print("  5. Reload Window，Ask 模式选 gpt-4o，勿选 Auto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
