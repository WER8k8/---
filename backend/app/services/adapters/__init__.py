"""Adapter 层（Execution Plane 平级适配器集合，总纲 §3.1）。

本包只放外部能力的适配桥接，禁止业务逻辑；所有适配器必须：
1. 不持有链路状态（状态归 ai_tasks / Control Plane）；
2. 不绕过 Policy / 租户隔离；
3. 可整体替换（冻结原则 §1.2-2）。
"""
