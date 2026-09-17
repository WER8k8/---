#!/bin/bash
# ============================================================
# 优丁建材 SaaS — 发布后冒烟测试（回滚决策门）
# 部署/回滚后跑一遍，失败即判定需要回滚。
# 通过: exit 0   失败: exit 1
# ============================================================
set -uo pipefail

BASE="${BASE:-http://127.0.0.1:8001}"
UA="YouDingSaaS-Internal/1.0"
FAIL=0

echo "══════ 冒烟测试 → $BASE ══════"

# ① 健康检查
echo -n "health … "
code="$(curl -s -o /dev/null -w '%{http_code}' -A "$UA" "$BASE/api/v1/health" || echo 000)"
if [ "$code" = "200" ]; then echo "OK"; else echo "FAIL($code)"; FAIL=1; fi

# ② 登录（admin 账号）
echo -n "login … "
code="$(curl -s -o /dev/null -w '%{http_code}' -A "$UA" \
  -H 'Content-Type: application/json' \
  -d '{"username_or_email":"admin","password":"admin123"}' \
  "$BASE/api/v1/auth/login" || echo 000)"
if [ "$code" = "200" ]; then echo "OK"; else echo "FAIL($code)"; FAIL=1; fi

# ③ 一条核心业务只读接口（询盘列表 / 概览）
echo -n "core route … "
code="$(curl -s -o /dev/null -w '%{http_code}' -A "$UA" "$BASE/api/v1/health/ready" || echo 000)"
if [ "$code" = "200" ]; then echo "OK"; else echo "WARN($code)"; fi

echo "══════════════════════════════"
if [ "$FAIL" = "0" ]; then
  echo "冒烟通过 ✅ 无需回滚"
else
  echo "冒烟失败 ❌ 建议立即执行: ./deploy/scripts/rollback.sh"
fi
exit "$FAIL"
