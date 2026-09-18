#!/usr/bin/env python3
"""Hermes 执行器覆盖率验证脚本。

验证所有已注册执行器都被至少一个 L1 模板驱动，防止"注册但未串联"的死组件。
同时验证所有 input_from 引用都命中真实执行器输出契约。

用法：
    python scripts/verify_hermes_executor_coverage.py
"""
from __future__ import annotations

import sys
from typing import Any
import io

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    """主入口：返回 0=通过，1=失败。"""
    try:
        from app.services.hermes.executors import ExecutorRegistry
        from app.services.hermes.planner_service import (
            _TEMPLATES,
            _site_launch_graph,
            _research_graph,
            _outreach_graph,
            _fulfillment_graph,
            _social_outreach_graph,
            _product_launch_graph,
            _research_analysis_graph,
            _lead_generation_graph,
            _browser_evidence_graph,
            _ubrain_assistant_graph,
        )
    except ImportError as exc:
        print(f"❌ 导入失败: {exc}", file=sys.stderr)
        return 1

    # ① 收集所有已注册执行器
    registered = set(ExecutorRegistry.list_executors())
    print(f"✓ 已注册执行器: {len(registered)} 个")
    print(f"  {sorted(registered)}")

    # ② 收集所有 L1 模板使用的执行器
    seen_builders = set()
    templates = []
    for keywords, builder in _TEMPLATES:
        if builder not in seen_builders:
            seen_builders.add(builder)
            templates.append((builder.__name__, builder))

    driven_executors: set[str] = set()
    all_nodes: list[Any] = []

    for name, builder in templates:
        graph = builder("test_plan", "test_event", {})
        executors = {n.executor for n in graph.nodes}
        driven_executors |= executors
        all_nodes.extend(graph.nodes)
        print(f"✓ 模板 {name}: 驱动 {len(executors)} 个执行器 {sorted(executors)}")

    # ③ 检查未驱动的执行器
    undriven = registered - driven_executors
    if undriven:
        print(f"\n❌ 发现 {len(undriven)} 个已注册但未驱动的执行器:")
        for exe in sorted(undriven):
            print(f"  - {exe}")
        return 1

    print(f"\n✓ 所有 {len(registered)} 个执行器都被 L1 模板驱动")

    # ④ 验证所有 input_from 引用都命中真实输出契约
    print("\n── 验证 input_from 引用一致性 ──")
    errors: list[str] = []

    for name, builder in templates:
        graph = builder("test_plan", "test_event", {})
        nodes_by_id = {n.id: n for n in graph.nodes}

        for node in graph.nodes:
            # 检查 depends_on
            for dep in node.depends_on or []:
                if dep not in nodes_by_id:
                    errors.append(f"[{name}] {node.id}.depends_on 引用不存在的节点 {dep}")

            # 检查 input_from
            for target, ref in (node.input_from or {}).items():
                parts = ref.split(".output.")
                if len(parts) != 2:
                    errors.append(f"[{name}] {node.id}.input_from.{target} 格式错误: {ref}")
                    continue

                src_id, field = parts
                if src_id not in nodes_by_id:
                    errors.append(f"[{name}] {node.id}.input_from.{target} 引用不存在的节点 {src_id}")
                    continue

                src_node = nodes_by_id[src_id]
                # 获取源执行器声明的输出
                try:
                    src_executor = ExecutorRegistry.get(src_node.executor)
                    caps = src_executor.get_capabilities()
                    cap_meta = caps.get(src_node.capability, {})
                    declared_outputs = set(cap_meta.get("output") or [])

                    if declared_outputs and field not in declared_outputs:
                        errors.append(
                            f"[{name}] {node.id}.{target} 引用了 {src_node.executor}.{src_node.capability} "
                            f"未声明的输出字段 {field!r}（已声明: {sorted(declared_outputs)}）"
                        )
                except Exception as exc:
                    errors.append(f"[{name}] 获取 {src_node.executor} 能力声明失败: {exc}")

    if errors:
        print(f"\n❌ 发现 {len(errors)} 处 input_from 引用错误:")
        for err in errors:
            print(f"  {err}")
        return 1

    print(f"✓ 所有 {len(all_nodes)} 个节点的 input_from 引用都命中真实输出契约")

    # ⑤ 汇总
    print("\n" + "=" * 60)
    print("✅ Hermes 执行器覆盖率验证通过")
    print(f"  - 已注册执行器: {len(registered)} 个")
    print(f"  - L1 模板数: {len(templates)} 个")
    print(f"  - 总节点数: {len(all_nodes)} 个")
    print(f"  - 所有执行器都被驱动: ✓")
    print(f"  - 所有 input_from 引用合法: ✓")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
