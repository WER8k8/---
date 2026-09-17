# competitor_radar.py
# 竞品雷达：监控 Accio Work / Qwen / Alibaba AIDC 等对象的公开信息源，
# 与上次快照做差异比对，有变化才产出新快照 + 落盘到 .workbuddy/memory/竞品雷达-YYYY-MM-DD.md。
# 用法：python scripts/competitor_radar.py
# 设计原则（与 AGENTS.md §交付求真 一致）：拉不到源就在输出里显式标注"网络受限降级"，绝不编造内容。

import datetime
import json
import os
import re
import ssl
import urllib.parse
import urllib.request

WORKSPACE = r"C:\Users\Administrator\Documents\上线网站开发完成"
MEMORY_DIR = os.path.join(WORKSPACE, ".workbuddy", "memory")
STATE_FILE = os.path.join(MEMORY_DIR, ".competitor_radar_state.json")
TEMPLATE_FILE = os.path.join(MEMORY_DIR, "竞品雷达-模板-2026-09-13.md")

# 监控对象：每个对象一组检索 URL。优先走 Wikipedia API（稳定、无需 key），
# 后续可扩展官方 changelog / 新闻 RSS 源。
WATCH_TARGETS = [
    {"name": "Qwen (Alibaba)", "urls": [
        "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Qwen%20Accio%20sourcing&format=json&srlimit=8",
        "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Accio%20Work%20agentic&format=json&srlimit=8",
    ]},
    {"name": "Alibaba Group", "urls": [
        "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Alibaba%20agentic%20commerce&format=json&srlimit=8",
    ]},
]

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def http_get(url: str, timeout: int = 30) -> str:
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    req = urllib.request.Request(url, headers={"User-Agent": "CompetitorRadar/1.0"})
    return opener.open(req, timeout=timeout).read().decode("utf-8", "ignore")


def extract_signals(target: dict) -> list:
    """返回 [{snippet, source}] 列表；网络失败返回 None（降级标记）。"""
    signals = []
    for url in target["urls"]:
        try:
            raw = http_get(url)
            data = json.loads(raw)
            for hit in data.get("query", {}).get("search", []):
                snippet = re.sub(r"<[^>]+>", "", hit.get("snippet", ""))
                snippet = re.sub(r"\s+", " ", snippet).strip()
                if snippet:
                    signals.append({
                        "snippet": snippet[:300],
                        "source": f"{target['name']} / {urllib.parse.unquote(url.split('title=')[-1]) if 'title=' in url else url}",
                        "ts": hit.get("timestamp", ""),
                    })
        except Exception as e:
            signals.append({"error": f"{target['name']}: {e.__class__.__name__}: {e}", "degraded": True})
    return signals


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"known_snippets": {}, "last_run": None}


def save_state(state: dict):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def diff_signals(all_signals: list, state: dict) -> tuple:
    """返回 (new_signals, unchanged_count, degraded_count)。"""
    known = state.get("known_snippets", {})
    new, degraded = [], 0
    for sig in all_signals:
        if sig.get("degraded"):
            degraded += 1
            new.append(sig)  # 降级信号也要写进快照，提示网络受限
            continue
        key = sig["snippet"]
        if key not in known:
            new.append(sig)
    return new, degraded


def write_snapshot(new_signals: list, degraded_count: int, today: str):
    template = ""
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, encoding="utf-8") as f:
            template = f.read()
    snapshot_path = os.path.join(MEMORY_DIR, f"竞品雷达-{today}.md")
    signal_lines = "\n".join(
        f"- **{s.get('source','?')}**：{s['snippet']}（ts={s.get('ts','?')}）"
        for s in new_signals if not s.get("error")
    )
    error_lines = "\n".join(f"- ⚠ 网络受限降级：{s['error']}" for s in new_signals if s.get("error"))
    degraded_note = f"\n> ⚠ 本期有 {degraded_count} 个监控源拉取失败，以上信号可能不完整，请勿据此下结论。\n" if degraded_count else ""

    body = (
        f"# 竞品雷达 | 快照 {today}\n\n"
        f"> 自动生成：scripts/competitor_radar.py\n"
        f"{degraded_note}\n"
        f"## 本期新信号\n\n{signal_lines or '（无新增信号，所有检索结果与上期一致）'}\n"
        + (f"\n## 拉取异常留痕\n\n{error_lines}\n" if error_lines else "")
        + f"\n## 待人工判定（映射 8 大子系统 + 三态）\n\n"
        f"见模板 .workbuddy/memory/竞品雷达-模板-2026-09-13.md 的 §二/§三，逐项填写后归档到 docs/。\n"
    )
    with open(snapshot_path, "w", encoding="utf-8") as f:
        f.write(body)
    return snapshot_path


def main():
    today = datetime.date.today().isoformat()
    all_signals = []
    for target in WATCH_TARGETS:
        all_signals.extend(extract_signals(target))

    state = load_state()
    new, degraded_count = diff_signals(all_signals, state)

    # 更新状态：所有（非降级）信号都记为已知
    known = state.get("known_snippets", {})
    for sig in all_signals:
        if not sig.get("degraded") and "snippet" in sig:
            known[sig["snippet"]] = today
    state["known_snippets"] = known
    state["last_run"] = today

    has_new_content = any(not s.get("error") for s in new)
    if has_new_content or not os.path.exists(STATE_FILE):
        path = write_snapshot(new, degraded_count, today)
        save_state(state)
        print(f"[competitor_radar] 快照已生成：{path}（新信号 {sum(1 for s in new if not s.get('error'))} 条，降级 {degraded_count} 条）")
    else:
        save_state(state)
        print(f"[competitor_radar] 无新增信号，跳过快照生成（降级 {degraded_count} 条，已留痕到 state）")


if __name__ == "__main__":
    main()
