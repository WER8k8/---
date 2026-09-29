from pathlib import Path
import json
p = Path(r"C:\Users\Administrator\Documents\上线网站开发完成\docs\archify\youding-aeos-panorama-2026-09-24.architecture.json")
d = json.loads(p.read_text(encoding="utf-8"))
for c in d["connections"]:
    if c["id"] == "harness-hermes":
        c.pop("labelDy", None)
        c["labelAt"] = [620, 215]
    if c["id"] == "api-hermes":
        c["labelAt"] = [800, 118]
    if c["id"] == "api-harness":
        c["labelAt"] = [560, 120]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("labels fixed")
