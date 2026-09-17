# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DeepSeek Harness 外层智能体运行时接入包。

把开源 "一切皆插件" Agent 运行时 DeepSeek Harness（dsh，github.com/deepseek-ai/deepseek-harness）
作为"外层编排大脑"接入 UJ 统一任务面。

设计要点（对齐总纲 / 轮次续接结论）：
- dsh 通过官方 Python SDK（`deepseek_harness`）启动一个**打包好的原生 dsh 可执行文件**作为子进程，
  经 stdio 上的 newline-delimited JSON-RPC 通信；**不依赖系统 Node.js**。
- SDK 在本包内**懒加载**（仅在真正调用时 import），因此即使未安装 SDK，后端也能正常启动，
  路由仅返回 available=false，不会炸导入期。
- dsh 的 provider/model/credentials 直接复用项目既有的 DeepSeek 配置
  （AI_DEEPSEEK_API_KEY / AI_DEEPSEEK_BASE_URL → DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL），
  无需重复配置。
- dsh_home 必须显式指定（SDK 永不自动读 ~/.dsh）。
"""
