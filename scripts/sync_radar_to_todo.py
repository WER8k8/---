# sync_radar_to_todo.py
# 把竞品雷达对标文档里"待排期"的 checkbox 动作，幂等地追加到 TODO.md 的
# 一个专门小节（§11 竞品雷达 · 能力跟进）。已存在的条目不会重复追加。
# 用法：python scripts/sync_radar_to_todo.py
# 设计原则：只追加、不修改 TODO.md 其它内容；幂等（重复运行安全）；找不到锚点小节就新建。

import io
import os
import re

WORKSPACE = r"C:\Users\Administrator\Documents\上线网站开发完成"
TODO_PATH = os.path.join(WORKSPACE, "TODO.md")
CAPABILITY_LEDGER_DIR = os.path.join(WORKSPACE, "docs", "能力台账")

SECTION_MARKER = "## 11. 竞品雷达 · 能力跟进（自动化维护，勿手动编辑本节，改动请改源文档）"
SECTION_NOTE = "\n> 本节由 scripts/sync_radar_to_todo.py 自动维护：来源是 docs/能力台账/ 下的竞品对标文档。"


def find_latest_radar_doc():
    files = []
    if os.path.isdir(CAPABILITY_LEDGER_DIR):
        for name in os.listdir(CAPABILITY_LEDGER_DIR):
            if name.startswith("竞品对标-") and name.endswith(".md"):
                files.append(os.path.join(CAPABILITY_LEDGER_DIR, name))
    if not files:
        return None
    return max(files)  # 文件名带日期，字典序即最新


def extract_action_items(doc_path):
    """从对标文档里提取形如 '- [ ] xxx' 的待办动作，返回 [ (body, doc_name), ...]"""
    items = []
    with open(doc_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*-\s*\[\s\]\s*(.+)$", line)
            if m:
                items.append((m.group(1).strip(), os.path.basename(doc_path)))
    return items


def normalize_todo_todo(text):
    """修正历史上被写坏的小节标题（缺 ## 前缀的情况）。"""
    bad = re.search(r"(?m)^.{0,3}11\. 竞品雷达 · 能力跟进", text)
    if bad and not re.search(re.escape("## 11. 竞品雷达 · 能力跟进"), text):
        text = text.replace(bad.group(0), SECTION_MARKER, 1)
    return text


def ensure_section(todo_text):
    if SECTION_MARKER in todo_text:
        return todo_text
    todo_text = todo_text.rstrip("\n") + "\n\n" + SECTION_MARKER + SECTION_NOTE + "\n"
    return todo_text


def idempotent_append(todo_text, items):
    """把 items 里尚未出现的（按正文精确匹配，排除带（来源：xxx）尾注的重复形态）追加到小节末尾。"""
    if not items:
        return todo_text, 0
    added = 0
    lines_to_add = []
    existing = todo_text
    for body, src in items:
        # 幂等：TODO.md 任意位置已出现该正文（含或不含来源尾注）就不重复
        if body in existing:
            continue
        lines_to_add.append(f"- [ ] {body}（来源：{src}）")
        added += 1
    if not lines_to_add:
        return todo_text, 0
    idx = todo_text.find(SECTION_MARKER)
    after = todo_text[idx + len(SECTION_MARKER):]
    mnext = re.search(r"(?m)^## ", after)
    insert_at = idx + len(SECTION_MARKER) + (mnext.start() if mnext else len(after))
    block = "\n".join(lines_to_add) + "\n"
    return todo_text[:insert_at].rstrip() + "\n" + block + todo_text[insert_at:], added


def main():
    doc = find_latest_radar_doc()
    if not doc:
        print("[sync_radar_to_todo] 未找到竞品对标文档，跳过")
        return
    items = extract_action_items(doc)
    with open(TODO_PATH, encoding="utf-8") as f:
        todo_text = f.read()
    todo_text = normalize_todo_todo(todo_text)
    todo_text = ensure_section(todo_text)
    new_text, added = idempotent_append(todo_text, items)
    with open(TODO_PATH, "w", encoding="utf-8") as f:
        f.write(new_text)
    print(f"[sync_radar_to_todo] 来源 {os.path.basename(doc)}，新增 {added} 条待办到 TODO.md §11（总 {len(items)} 条待提取）")


if __name__ == "__main__":
    main()
