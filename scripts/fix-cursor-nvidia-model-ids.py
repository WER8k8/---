"""修复 Cursor NVIDIA 配置：纠正 deepseek/ 错误 ID，默认改用最稳模型。"""
import json
import os
import sqlite3
from pathlib import Path

APP_KEY = (
    "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl."
    "persistentStorage.applicationUser"
)
OPENAI_KEY = "cursorAuth/openAIKey"
BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT = "meta/llama-3.1-8b-instruct"

ID_MAP = {
    "deepseek/deepseek-v4-flash": "deepseek-ai/deepseek-v4-flash",
    "deepseek/deepseek-v4-pro": "deepseek-ai/deepseek-v4-pro",
}

CURSOR_BUILTIN = {
    "default",
    "premium",
    "composer-2.5",
    "kimi-k2.5",
    "kimi-k2.6",
    "grok-build-0.1",
    "grok-4.3",
    "auto",
}


def normalize_id(model_id: str) -> str:
    return ID_MAP.get(model_id, model_id)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        n = normalize_id(item)
        if n not in seen:
            out.append(n)
            seen.add(n)
    return out


def load_key() -> str:
    env_path = Path(__file__).resolve().parents[1] / "backend" / "config" / "dev" / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("AI_NVIDIA_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> None:
    api_key = load_key()
    db = Path(os.environ["APPDATA"]) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    if api_key:
        cur.execute(
            "INSERT OR REPLACE INTO ItemTable(key, value) VALUES(?, ?)",
            (OPENAI_KEY, api_key),
        )

    row = cur.execute("SELECT value FROM ItemTable WHERE key=?", (APP_KEY,)).fetchone()
    data = json.loads(row[0])
    data["useOpenAIKey"] = True
    data["openAIBaseUrl"] = BASE_URL

    ai = data.setdefault("aiSettings", {})
    ai["userAddedModels"] = dedupe(ai.get("userAddedModels", []))
    for wrong in list(ID_MAP.keys()):
        if wrong in ai["userAddedModels"]:
            ai["userAddedModels"].remove(wrong)
    for right in ID_MAP.values():
        if right not in ai["userAddedModels"]:
            ai["userAddedModels"].append(right)
    if DEFAULT not in ai["userAddedModels"]:
        ai["userAddedModels"].insert(0, DEFAULT)

    ai["modelOverrideEnabled"] = dedupe(ai.get("modelOverrideEnabled", []))

    for cfg in ai.get("modelConfig", {}).values():
        name = normalize_id(cfg.get("modelName", ""))
        if name in CURSOR_BUILTIN or name in ID_MAP or name == "moonshotai/kimi-k2.6":
            name = DEFAULT
        cfg["modelName"] = name
        cfg["selectedModels"] = [{"modelId": name, "parameters": []}]

    cur.execute(
        "INSERT OR REPLACE INTO ItemTable(key, value) VALUES(?, ?)",
        (APP_KEY, json.dumps(data, ensure_ascii=False, separators=(",", ":"))),
    )
    conn.commit()
    conn.close()
    print("OK default=", DEFAULT)
    print("OK removed wrong deepseek/* ids")


if __name__ == "__main__":
    main()
