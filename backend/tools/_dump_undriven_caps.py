import json
from app.services.hermes.executors import ExecutorRegistry

UNDRIVEN = ["ai_engine", "billing", "browser", "engagement", "forum", "lead",
            "media", "product", "research", "seo", "ubrain", "wangcai"]
for name in UNDRIVEN:
    ex = ExecutorRegistry.get(name)
    if ex is None:
        print(f"{name}: NOT REGISTERED")
        continue
    caps = ex.get_capabilities()
    print(f"### {name}")
    for cap, meta in caps.items():
        print("   ", cap, "| input=", meta.get("input"),
              "| output=", meta.get("output"),
              "| approve=", meta.get("needs_approval"),
              "|", meta.get("desc", "")[:80])
    print()