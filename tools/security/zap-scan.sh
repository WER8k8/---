#!/usr/bin/env bash
# OWASP ZAP 安全扫描自动化脚本
#
# 覆盖：OWASP Top 10 自动扫描
# 用法：bash tools/security/zap-scan.sh [TARGET_URL]

set -euo pipefail

TARGET="${1:-http://127.0.0.1:8001}"
REPORT_DIR="reports/security/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "=== OWASP ZAP 安全扫描 ==="
echo "目标: $TARGET"
echo "报告目录: $REPORT_DIR"

if ! command -v zap-cli &> /dev/null; then
  echo "[WARN] zap-cli 未安装，使用 Docker 方式"
  docker run --rm -v "$(pwd)/$REPORT_DIR:/zap/wrk" \
    -t ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py \
    -t "$TARGET" \
    -r zap_report.html \
    -J zap_report.json \
    -l WARN \
    || true
else
  zap-cli quick-scan \
    -s all \
    --alert-threshold Warning \
    -r "$REPORT_DIR/zap_report.html" \
    "$TARGET"
fi

echo ""
echo "=== 扫描完成 ==="
echo "报告: $REPORT_DIR/zap_report.html"

if [ -f "$REPORT_DIR/zap_report.json" ]; then
  HIGH=$(python3 -c "
import json
with open('$REPORT_DIR/zap_report.json') as f:
    data = json.load(f)
alerts = data.get('site', [{}])[0].get('alerts', []) if isinstance(data.get('site'), list) else data.get('site', {}).get('alerts', [])
high = sum(1 for a in alerts if a.get('riskcode') == '3')
print(f'High/Critical: {high}')
" 2>/dev/null || echo "无法解析 JSON 报告")
  echo "$HIGH"
fi
