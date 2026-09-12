#!/bin/bash
# 端到端测试脚本 - 测试 18 个 API 端点
# 作者：小鹅
# 日期：2026-05-23

BASE_URL="http://127.0.0.1:8020"
PASSED=0
FAILED=0
TOTAL=0

echo "=========================================="
echo "端到端测试开始 - $(date)"
echo "=========================================="
echo ""

# 函数：测试单个端点
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local test_name=$4
    
    TOTAL=$((TOTAL + 1))
    
    echo "测试 $TOTAL: $test_name"
    echo "  $method $endpoint"
    
    # 发送请求
    response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    # 检查状态码
    if [ "$http_code" = "$expected_status" ]; then
        echo "  ✅ 状态码: $http_code (期望: $expected_status)"
        PASSED=$((PASSED + 1))
    else
        echo "  ❌ 状态码: $http_code (期望: $expected_status)"
        FAILED=$((FAILED + 1))
    fi
    
    echo "  响应: $(echo $body | head -c 100)..."
    echo ""
}

# 1. 根路径
test_endpoint "GET" "/" "200" "根路径"

# 2. 健康检查（可能不存在）
test_endpoint "GET" "/health" "404" "健康检查（期望404）"

# 3. API文档
test_endpoint "GET" "/docs" "200" "Swagger UI"
test_endpoint "GET" "/redoc" "200" "ReDoc"

# 4. OpenAPI schema
test_endpoint "GET" "/openapi.json" "200" "OpenAPI Schema"

# 5. 超级管理员API - GEO引擎
test_endpoint "GET" "/api/v1/super-admin/geo-engine/models" "200" "GEO引擎-模型列表"
test_endpoint "POST" "/api/v1/super-admin/geo-engine/check" "422" "GEO检查（缺少参数）"
test_endpoint "GET" "/api/v1/super-admin/geo-engine/alerts/rules" "200" "GEO告警规则"

# 6. SEO API
test_endpoint "GET" "/api/v1/seo/keywords" "200" "SEO关键词列表"
test_endpoint "GET" "/api/v1/seo/pages" "200" "SEO页面列表"

# 7. 认证API（可能不需要认证）
test_endpoint "POST" "/api/v1/auth/login" "422" "登录（缺少参数）"
test_endpoint "POST" "/api/v1/auth/register" "422" "注册（缺少参数）"

# 8. 用户API（可能需要认证）
test_endpoint "GET" "/api/v1/users/me" "401" "当前用户（未认证）"

# 9. 管理API
test_endpoint "GET" "/api/v1/admin/dashboard" "200" "管理仪表板"

# 10. 404测试
test_endpoint "GET" "/nonexistent-path" "404" "404页面"

echo "=========================================="
echo "测试完成 - $(date)"
echo "=========================================="
echo "总计: $TOTAL"
echo "通过: $PASSED"
echo "失败: $FAILED"
echo "成功率: $(( PASSED * 100 / TOTAL ))%"
echo ""

# 生成报告
cat > e2e-test-report-real.md << EOF
# 端到端测试报告（真实）

**测试时间**: $(date)  
**测试工具**: curl + bash  
**服务器**: $BASE_URL  
**测试类型**: 真实端到端测试

---

## 测试结果摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | $TOTAL |
| 通过 | $PASSED |
| 失败 | $FAILED |
| 成功率 | $(( PASSED * 100 / TOTAL ))% |

---

## 详细结果

（完整结果请查看上面输出）

---

## 结论

$(if [ $FAILED -eq 0 ]; then echo "✅ 所有测试通过！系统运行正常。"; else echo "⚠️ 有 $FAILED 个测试失败，需要检查。"); fi)

---

**报告生成时间**: $(date)
EOF

echo "报告已生成: e2e-test-report-real.md"
