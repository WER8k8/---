#!/usr/bin/env python3
"""
Production deployment security check script.
Checks that all required secrets and passwords are properly configured.

Usage: python scripts/check_production_secrets.py [--strict]
       --strict: exit with non-zero code if weak secrets detected
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Weak password patterns
WEAK_PATTERNS = [
    "change-me", "change_me", "changeme",
    "your-secret", "your-jwt", "replace-me",
    "your-password", "your-key", "your-api",
    "123456", "password", "admin",
    "secret-key", "secret_key",
]

# Required secrets (empty or containing weak patterns => error)
REQUIRED_SECRETS = {
    "JWT_SECRET_KEY": {
        "min_length": 32,
        "files": [".env.prod", "backend/.env"],
        "description": "JWT signing key",
    },
    "DB_PASSWORD": {
        "min_length": 16,
        "files": [".env.prod"],
        "description": "Database password",
    },
    "REDIS_PASSWORD": {
        "min_length": 16,
        "files": [".env.prod"],
        "description": "Redis password",
    },
    "MINIO_ACCESS_KEY": {
        "min_length": 16,
        "files": ["backend/.env"],
        "description": "MinIO access key",
    },
    "MINIO_SECRET_KEY": {
        "min_length": 32,
        "files": ["backend/.env"],
        "description": "MinIO secret key",
    },
    "GRAFANA_PASSWORD": {
        "min_length": 16,
        "files": [".env.prod"],
        "description": "Grafana admin password",
    },
}

# Recommended but optional production secrets
RECOMMENDED_SECRETS = {
    "SMTP_PASSWORD": "Email service password",
    "AI_NVIDIA_API_KEY": "NVIDIA AI API key",
    "FEISHU_APP_SECRET": "Feishu app secret",
    "MAIN_ADMIN_JWT_SECRET": "seo-backend main admin JWT (must match JWT_SECRET_KEY)",
}


def parse_env_file(filepath):
    """Parse .env file into key -> value dict"""
    env = {}
    if not filepath.exists():
        return env
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = value
    return env


def check_weak_pattern(value):
    """Check if value contains weak password patterns"""
    found = []
    lower = value.lower()
    for pat in WEAK_PATTERNS:
        if pat in lower:
            found.append(pat)
    return found


def main():
    strict = "--strict" in sys.argv
    issues = []
    warnings = []
    ok_count = 0

    print("=" * 60)
    print("  Youding - Production Secret Security Check")
    print("=" * 60)
    print()

    # 1. Check required secrets
    for var_name, config in REQUIRED_SECRETS.items():
        found_valid = False
        checked_files = []

        for file_rel in config["files"]:
            filepath = ROOT / file_rel
            env = parse_env_file(filepath)
            value = env.get(var_name, "")
            checked_files.append(str(file_rel))

            if not value:
                continue

            # Check weak patterns
            weak = check_weak_pattern(value)
            if weak:
                issues.append(
                    f"[FAIL] {var_name} ({config['description']}) "
                    f"in {file_rel} contains weak patterns: {weak}"
                )
                continue

            # Check length
            if len(value) < config["min_length"]:
                issues.append(
                    f"[FAIL] {var_name} ({config['description']}) "
                    f"in {file_rel} length too short ({len(value)} < {config['min_length']})"
                )
                continue

            found_valid = True
            ok_count += 1
            print(f"  [OK] {var_name:25s} -> {file_rel} (len={len(value)})")
            break

        if not found_valid:
            files_str = ", ".join(checked_files)
            issues.append(
                f"[FAIL] {var_name} ({config['description']}) "
                f"not found in any of: {files_str}"
            )

    print()

    # 2. Check recommended secrets
    for var_name, desc in RECOMMENDED_SECRETS.items():
        env = parse_env_file(ROOT / "backend" / ".env")
        value = env.get(var_name, "")
        if not value:
            env = parse_env_file(ROOT / ".env.prod")
            value = env.get(var_name, "")

        if not value:
            warnings.append(f"[WARN] {var_name} ({desc}) not configured")
        else:
            weak = check_weak_pattern(value)
            if weak:
                warnings.append(
                    f"[WARN] {var_name} ({desc}) contains weak patterns: {weak}"
                )
            else:
                print(f"  [~]  {var_name:25s} -> configured (len={len(value)})")

    # 3. Output results
    print()
    print("=" * 60)
    print(f"  Result: {ok_count} passed, {len(issues)} failed, {len(warnings)} warnings")
    print("=" * 60)

    if issues:
        print()
        print("[CRITICAL] Must fix:")
        for issue in issues:
            print(f"  {issue}")

    if warnings:
        print()
        print("[WARNING] Should fix:")
        for warn in warnings:
            print(f"  {warn}")

    if issues:
        print()
        print("[TIP] Generate strong random secrets with:")
        print('  python -c "import secrets; print(secrets.token_hex(32))"')
        if strict:
            sys.exit(1)
        return 1

    if warnings and strict:
        print()
        print("[!] Warnings present (--strict mode: non-zero exit)")
        sys.exit(1)
        return 1

    print()
    print("[PASS] All security checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
