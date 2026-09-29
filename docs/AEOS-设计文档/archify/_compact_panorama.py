from pathlib import Path
import json

p = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\docs\archify\youding-aeos-panorama-2026-09-24.architecture.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["meta"]["viewBox"] = [1320, 540]
pos = {
  "buyers": ([40, 36], [150, 56]),
  "shells": ([260, 36], [160, 56]),
  "login": ([490, 36], [140, 56]),
  "api": ([700, 36], [180, 56]),
  "harness": ([490, 150], [150, 56]),
  "hermes": ([700, 150], [180, 56]),
  "browser": ([960, 150], [150, 56]),
  "site": ([40, 300], [150, 56]),
  "deerflow": ([250, 300], [150, 56]),
  "trade": ([460, 300], [150, 56]),
  "goodjob": ([700, 300], [180, 56]),
  "pg": ([700, 420], [180, 56]),
}
for c in d["components"]:
    if c["id"] in pos:
        c["pos"], c["size"] = pos[c["id"]]
for c in d["connections"]:
    # tighten fan-out labelAt y to new rows
    if c.get("id") == "hermes-site":
        c["labelAt"] = [115, 275]
    elif c.get("id") == "hermes-trade":
        c["labelAt"] = [535, 275]
    elif c.get("id") == "hermes-goodjob":
        c["labelAt"] = [860, 275]
    elif c.get("id") == "harness-hermes":
        c["labelAt"] = [640, 175]
d["cards"] = [
  {"dot": "cyan", "title": "实探", "items": ["172 路由 · 1582 端点 · 37 执行器", "253 表 · selfcheck 20/20"]},
  {"dot": "emerald", "title": "八子系统", "items": ["DSH · Hermes · Site · DeerFlow", "Trade AI · GoodJob · 资产 · n8n"]},
  {"dot": "rose", "title": "主链", "items": ["获客→内容→询盘→七步履约", "SaaS · Token · IP 槽位"]},
  {"dot": "amber", "title": "端口", "items": ["PG:5433 OPEN", "其余 CLOSED 待 start-lan"]},
]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ok", p)
