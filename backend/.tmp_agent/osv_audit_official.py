"""只读 OSV 审计：官网运行源 主要备份/上线网站/frontend 的 lock。"""
import json, time
import httpx

LOCK = r"C:\Users\Administrator\Documents\上线网站开发完成\主要备份\上线网站\frontend\package-lock.json"
with open(LOCK, encoding="utf-8") as f:
    lock = json.load(f)

pkgs = {}
for k, v in lock.get("packages", {}).items():
    if not k or not v.get("version"):
        continue
    pkgs[k.split("node_modules/")[-1]] = v["version"]

queries = [{"package": {"name": n, "ecosystem": "npm"}, "version": v} for n, v in pkgs.items()]
results = {}

with httpx.Client(timeout=60) as c:
    pending = list(range(0, len(queries), 100))
    for round_no in range(12):
        if not pending:
            break
        next_pending = []
        for i in pending:
            batch = queries[i:i + 100]
            try:
                r = c.post("https://api.osv.dev/v1/querybatch", json={"queries": batch})
                r.raise_for_status()
                for q, res in zip(batch, r.json().get("results", [])):
                    name = q["package"]["name"]
                    vulns = [v.get("id") for v in (res or {}).get("vulns", [])]
                    if vulns:
                        results[name] = (q["version"], vulns)
            except Exception:
                next_pending.append(i)
        pending = next_pending
        if pending:
            time.sleep(5)
    for i in pending:
        for q in queries[i:i + 100]:
            name = q["package"]["name"]
            for attempt in range(6):
                try:
                    r = c.post("https://api.osv.dev/v1/query",
                               json={"package": {"name": name, "ecosystem": "npm"}, "version": q["version"]})
                    r.raise_for_status()
                    vulns = [v.get("id") for v in r.json().get("vulns", [])]
                    if vulns:
                        results[name] = (q["version"], vulns)
                    break
                except Exception:
                    if attempt == 5:
                        print(f"  UNREACHABLE {name}@{q['version']}")
                    time.sleep(3)

print(f"\nchecked: {len(pkgs)}/{len(pkgs)}  vulnerable: {len(results)}")
for name in sorted(results):
    ver, vulns = results[name]
    print(f"  {name}@{ver}: {','.join(vulns)}")
