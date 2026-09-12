"""Model Gateway 四维评分路由验证（垫片模式，仅标准库）。

用法：python -m tests.model_gateway_router_verify
依赖：router.py / capability.py 均为纯逻辑模块，无 app 全局依赖。

覆盖（总纲 §4.6 能力路由 + 038 四维评分）：
1. 既有行为保持：无 caps 全默认 → fallback；预算紧张 → cost_optimized（Cost>Quality）
2. 能力映射保持：REASONING→logic / CODING→code / TRANSLATION→multilingual /
   WRITING→chinese / CHEAP→cost_optimized / FAST→general；多 caps 首映射优先
3. Cost 维度：预算紧张硬覆盖（含与能力冲突时）；预算压力（0.01）软评分
4. Quality 维度：quality=low → cost_optimized 硬降级；quality=high 无 caps → high_quality
5. Speed 维度：speed=fast 无 caps → cost_optimized
6. Privacy 维度：strict 闸门过滤境外 tier（REASONING→境内档）；
   strict + CHEAP 映射兼容；strict + quality=high → deepseek 境内择优
7. 组合：quality=high + budget=0.01 → deepseek（高质量+预算压力折中）
8. 健壮性：非法维度值归一化不抛错；位置参数 (caps, budget) 向后兼容
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)


def _load_from_file(mod_name: str, path: str):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


for _pkg in ("app", "app.services", "app.services.model_gateway"):
    if _pkg not in sys.modules:
        _mod = types.ModuleType(_pkg)
        _mod.__path__ = []
        sys.modules[_pkg] = _mod

_CAP = os.path.join(_BACKEND, "app", "services", "model_gateway", "capability.py")
_RTR = os.path.join(_BACKEND, "app", "services", "model_gateway", "router.py")
capability = _load_from_file("app.services.model_gateway.capability", _CAP)
router = _load_from_file("app.services.model_gateway.router", _RTR)

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def main() -> int:
    rt = router.resolve_tier
    mr = router.ModelRouter()

    print("== 既有行为保持 ==")
    check("无caps全默认 → general", rt() == "general")
    check("自定义fallback → 兜底档", rt(fallback_tier="chinese") == "chinese")
    check(
        "ModelRouter.default_tier 兜底",
        router.ModelRouter(default_tier="article").resolve_tier() == "article",
    )
    check("预算紧张(0.001) → cost_optimized", rt(budget=0.001) == "cost_optimized")
    check(
        "预算紧张+REASONING → cost_optimized（Cost>Quality）",
        rt(["reasoning"], 0.001) == "cost_optimized",
    )

    print("== 能力映射保持 ==")
    check("REASONING → logic", rt(["reasoning"]) == "logic")
    check("CODING → code", rt(["coding"]) == "code")
    check("TRANSLATION → multilingual", rt(["translation"]) == "multilingual")
    check("WRITING → chinese", rt(["writing"]) == "chinese")
    check("CHEAP → cost_optimized", rt(["cheap"]) == "cost_optimized")
    check("FAST → general", rt(["fast"]) == "general")
    check("多caps首映射优先 [CODING,CHEAP] → code", rt(["coding", "cheap"]) == "code")
    check(
        "多caps首映射优先 [CHEAP,CODING] → cost_optimized",
        rt(["cheap", "coding"]) == "cost_optimized",
    )
    check("未知标签过滤后无caps → fallback", rt(["nonsense"]) == "general")

    print("== Cost 维度 ==")
    check("预算压力(0.01)无caps → cost_optimized", rt(budget=0.01) == "cost_optimized")
    check("宽裕预算(0.5)无caps不炸且返回合法tier", rt(budget=0.5) in router.GENERIC_TIERS)

    print("== Quality 维度 ==")
    check("quality=low+CODING → cost_optimized 硬降级", rt(["coding"], quality="low") == "cost_optimized")
    check("quality=high无caps → high_quality", rt(quality="high") == "high_quality")
    check("quality=high不影响能力映射（CODING仍→code）", rt(["coding"], quality="high") == "code")

    print("== Speed 维度 ==")
    check("speed=fast无caps → cost_optimized", rt(speed="fast") == "cost_optimized")
    check("speed=slow无caps → 境内低成本档", rt(speed="slow") in router.DOMESTIC_TIERS)

    print("== Privacy 维度 ==")
    check("strict+REASONING → cost_optimized（logic境外被闸门过滤）", rt(["reasoning"], privacy="strict") == "cost_optimized")
    check("strict+CHEAP → cost_optimized（映射兼容境内）", rt(["cheap"], privacy="strict") == "cost_optimized")
    check("strict+quality=high → deepseek（境内择优）", rt(quality="high", privacy="strict") == "deepseek")
    check("strict无caps默认维度 → cost_optimized", rt(privacy="strict") == "cost_optimized")

    print("== 四维组合 ==")
    check("quality=high+budget=0.01 → deepseek（质量+预算折中）", rt(quality="high", budget=0.01) == "deepseek")
    check("quality=high+speed=fast → 合法tier", rt(quality="high", speed="fast") in router.GENERIC_TIERS)

    print("== 健壮性 ==")
    try:
        got = rt(["reasoning"], quality="ultra", speed="warp", privacy="???")
        check("非法维度值归一化不抛错（按默认处理→logic）", got == "logic", f"got={got}")
    except Exception as exc:  # noqa: BLE001
        check("非法维度值归一化不抛错", False, str(exc))
    check(
        "位置参数(caps, budget)向后兼容",
        mr.resolve_tier(["reasoning"], None) == "logic"
        and mr.resolve_tier(["reasoning"], 0.001) == "cost_optimized",
    )
    check("budget=None 显式传参 → 能力映射正常", rt(["reasoning"], None) == "logic")

    print(f"\n总计: PASS={PASS} FAIL={FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
