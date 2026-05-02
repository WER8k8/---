#!/usr/bin/env python3
"""
生产环境变量检查脚本
验证 .env.prod 文件中的关键配置是否正确设置
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple


def load_env_file(file_path: str) -> dict:
    """加载.env文件"""
    env_vars = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def check_variable(name: str, value: str, description: str) -> Tuple[bool, str]:
    """检查单个变量"""
    placeholder_patterns = [
        'your-',
        'change-in-production',
        'must-change',
        'example',
    ]

    is_placeholder = any(pattern in value.lower() for pattern in placeholder_patterns)

    if is_placeholder:
        return False, f"[FAIL] {name}: Still using default value\n   Description: {description}"

    if not value:
        return False, f"[WARN] {name}: Value is empty\n   Description: {description}"

    if name == 'JWT_SECRET_KEY' and len(value) < 32:
        return False, f"[FAIL] {name}: Key length < 32 chars (current: {len(value)})\n   Suggestion: python -c 'import secrets; print(secrets.token_hex(32))'"

    if name == 'DB_PASSWORD' and len(value) < 12:
        return False, f"[WARN] {name}: Password length recommended >= 12 chars (current: {len(value)})"

    return True, f"[PASS] {name}: Configured"


def main():
    """主函数"""
    print("=" * 70)
    print("生产环境变量检查工具")
    print("=" * 70)
    print()

    env_file = ".env.prod"
    if not Path(env_file).exists():
        print(f"❌ 错误: {env_file} 文件不存在")
        print("请先复制 .env.example 为 .env.prod 并配置")
        sys.exit(1)

    env_vars = load_env_file(env_file)

    # 关键变量检查列表
    critical_vars = [
        ("DOMAIN", "网站域名"),
        ("DB_NAME", "数据库名称"),
        ("DB_USER", "数据库用户名"),
        ("DB_PASSWORD", "数据库密码（需强密码）"),
        ("MINIO_ACCESS_KEY", "MinIO访问密钥"),
        ("MINIO_SECRET_KEY", "MinIO秘密密钥（需强密钥）"),
        ("JWT_SECRET_KEY", "JWT签名密钥（至少32字符）"),
        ("AI_NVIDIA_API_KEY", "NVIDIA AI API密钥"),
    ]

    optional_vars = [
        ("AI_OPENAI_API_KEY", "OpenAI API密钥（可选）"),
        ("AI_ANTHROPIC_API_KEY", "Anthropic API密钥（可选）"),
        ("AI_GEMINI_API_KEY", "Gemini API密钥（可选）"),
        ("AI_DEEPSEEK_API_KEY", "DeepSeek API密钥（可选）"),
    ]

    print("【关键变量检查】")
    print("-" * 70)

    all_passed = True
    for var_name, description in critical_vars:
        value = env_vars.get(var_name, "")
        passed, message = check_variable(var_name, value, description)
        print(message)
        if not passed:
            all_passed = False

    print()
    print("【可选变量检查】")
    print("-" * 70)

    for var_name, description in optional_vars:
        value = env_vars.get(var_name, "")
        passed, message = check_variable(var_name, value, description)
        print(message)

    print()
    print("=" * 70)

    if all_passed:
        print("[SUCCESS] All critical variables configured! Ready for production deployment.")
    else:
        print("[FAIL] Some critical variables not configured. DO NOT deploy!")
        print()
        print("Fix suggestions:")
        print("1. Open .env.prod file")
        print("2. Replace values with 'your-' or 'change-in-production'")
        print("3. Generate secure keys:")
        print("   python -c 'import secrets; print(secrets.token_hex(32))'")
        print("4. Re-run this script")

    print("=" * 70)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
