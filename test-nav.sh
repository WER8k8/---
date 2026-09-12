#!/bin/bash
# 自动化测试脚本 - 遍历导航栏菜单并捕获控制台错误

SESSION="youding-test"
BASE_URL="http://localhost:5176"

# 菜单列表
MENUS=(
  "产品管理"
  "询盘留言"
  "文章内容"
  "SEO总览"
  "AI配置"
  "系统设置"
  "租户列表"
  "财务概览"
  "流量看板"
)

# 清空控制台日志函数
clear_console() {
  agent-browser --session $SESSION eval "console.clear && console.log('=== Console cleared ===')"
  agent-browser --session $SESSION wait 500
}

# 获取控制台日志函数
get_console_errors() {
  agent-browser --session $SESSION console 2>&1 | grep -E "(error|warning|Error|Warning)" || echo "No errors/warnings found"
}

# 主测试流程
echo "Starting navigation test..."

for menu in "${MENUS[@]}"; do
  echo "Testing: $menu"
  clear_console

  # 点击菜单
  agent-browser --session $SESSION eval "Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('$menu'))?.click()"

  # 等待页面加载
  agent-browser --session $SESSION wait 2000

  # 获取当前URL
  URL=$(agent-browser --session $SESSION eval "window.location.href")

  echo "  URL: $URL"

  # 获取控制台错误
  ERRORS=$(get_console_errors)
  if [ -n "$ERRORS" ]; then
    echo "  ERRORS: $ERRORS"
  fi

  echo ""
done

echo "Test completed."
