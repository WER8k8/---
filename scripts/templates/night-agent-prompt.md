# 夜间无人全自动开发 · Cursor Agent 指令

## 硬约束
- 权威: docs/出海计/商业飞轮OS-开发总文档.md
- 主方向: 字节 DeerFlow + 阿里 AccioWork 对标复刻，禁止改向
- 本夜最多完成 night-autodev-queue.yaml 中 3 条任务（P0 优先）
- 禁止: git push、自动发信、删 skill-catalog 对标项、大规模无关重构

## 执行
1. Read docs/出海计/night-autodev-queue.yaml，选未完成任务
2. 按 workflows/night-autodev-flywheel.yaml 执行（规划→实现→pytest→review）
3. 产出写入 {{OUT_DIR}}/MORNING.md（完成了什么、测试结果、明早 3 件事）
4. 验证: cd backend; python -m pytest tests/unit/test_commercial_os_flywheel.py tests/unit/test_accio_sales.py -q

## 队列文件
{{QUEUE_PATH}}

## 机械门禁
见同目录 GATE_REPORT.md（{{STAMP}}）
