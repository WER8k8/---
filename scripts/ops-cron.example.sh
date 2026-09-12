#!/usr/bin/env bash
# 生产 crontab 示例 — Hermes 自愈齿轮 + 业务批处理
# 安装: crontab -e 粘贴下方行（改 /opt/youding 为实际路径）
#
# Hermes 7×24：backend 生产启动后 site_patrol_scheduler 每 15 分钟跑 full ops cycle
# （技术雷达 + 巡站 + 安全自愈 + 飞书告警）。以下 cron 为兜底 / 无 scheduler 时备用。

DEPLOY=/opt/youding
PY=$DEPLOY/backend/.venv/bin/python
OPS="$PY $DEPLOY/backend/scripts/run_ops_jobs.py"

# 租户到期冻结 — 每日 02:00
# 0 2 * * * cd $DEPLOY/backend && $OPS --job tenant-expiry >> /var/log/youding/tenant-expiry.log 2>&1

# 发布 Worker — 每 15 分钟
# */15 * * * * cd $DEPLOY/backend && $OPS --job publish-worker >> /var/log/youding/publish-worker.log 2>&1

# 英伟达免费通道模型探测 — 1:00 / 12:00 / 20:00（生产 backend 内 scheduler 已覆盖，此为兜底）
# 0 1,12,20 * * * cd $DEPLOY/backend && $OPS --job nvidia-probe >> /var/log/youding/nvidia-probe.log 2>&1

# Hermes 完整运维循环（巡站+自愈+技术雷达）— 每 30 分钟兜底
# */30 * * * * cd $DEPLOY/backend && $OPS --job hermes-ops >> /var/log/youding/hermes-ops.log 2>&1

# DeerFlow 定时市场研究 — 每日 07:30（backend scheduler 已覆盖）
# 30 7 * * * cd $DEPLOY/backend && $OPS --job deerflow-schedule >> /var/log/youding/deerflow.log 2>&1

# 海关贸易情报刷新 — 每周一 03:30
# 30 3 * * 1 cd $DEPLOY/backend && $OPS --job trade-intel-refresh >> /var/log/youding/trade-intel.log 2>&1

# Agency LLM Ollama 模型保活（可选，部署后 cloud-post-deploy 已 pull）
# 0 4 * * 0 HERMES_AGENCY_AUTO_DOCKER_OLLAMA=1 bash $DEPLOY/scripts/setup-agency-llm-providers.sh --start-ollama >> /var/log/youding/agency-llm.log 2>&1

# 周五 cert:gate（构建机或 CI，非生产 runtime 必需）
# 0 18 * * 5 cd $DEPLOY/frontend/admin && npm run cert:gate >> /var/log/youding/cert-gate.log 2>&1
