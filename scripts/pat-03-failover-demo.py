#!/usr/bin/env python3

"""PAT-03 · 多场景失败切换可复现 demo（无需真实 API Key）"""



from __future__ import annotations



import asyncio

import os

import sys



BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))

sys.path.insert(0, BACKEND)

os.environ.setdefault("ENVIRONMENT", "testing")

os.environ.setdefault("AI_SCENARIO_FALLBACK_ENABLED", "true")



from app.services.ai_invocation_service import _fallback_scenarios, normalize_scenario





async def demo_invoke_with_mock_failures() -> dict:

    """模拟 primary 失败、fallback 成功。"""

    from app.services import ai_invocation_service as mod



    calls: list[str] = []



    async def fake_once(db, *, prompt, scenario, max_tokens, task_type, tenant_id=None, max_retries=3):

        calls.append(scenario)

        if scenario == "article":

            raise RuntimeError("simulated primary failure")

        return {

            "content": "fallback ok",

            "scenario": scenario,

            "model_name": scenario,

            "token_usage": 12,

        }



    mod._invoke_llm_once = fake_once  # type: ignore[method-assign]



    result = await mod.invoke_llm(None, prompt="demo", scenario="article", enable_fallback=True)

    return {"calls": calls, "result": result}





def main() -> int:

    chain = _fallback_scenarios(normalize_scenario("article"))

    print("[info] fallback chain:", " -> ".join(chain))



    out = asyncio.run(demo_invoke_with_mock_failures())

    print("[info] invoke order:", out["calls"])

    print("[info] fallback flag:", out["result"].get("fallback"))

    print("[info] final scenario:", out["result"].get("scenario"))



    ok = (

        out["calls"][0] == "article"

        and len(out["calls"]) >= 2

        and out["result"].get("fallback") is True

        and out["result"].get("scenario") != "article"

    )

    print(f"[{'PASS' if ok else 'FAIL'}] PAT-03 failover demo")

    return 0 if ok else 1





if __name__ == "__main__":

    sys.exit(main())

