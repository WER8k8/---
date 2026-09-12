#!/usr/bin/env python3
"""平台存储探测 CLI — 供 setup-platform-storage.ps1 与 CI 调用。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# 探测前注入 JWT 占位，避免 config 校验失败
if not os.environ.get("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "probe-" + ("x" * 32)
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "probe-" + ("x" * 32)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Qiniu / R2 platform storage")
    parser.add_argument(
        "--target",
        choices=("qiniu", "r2", "all"),
        default="all",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--qiniu-access-key",
        default=os.environ.get("QINIU_ACCESS_KEY"),
    )
    parser.add_argument(
        "--qiniu-secret-key",
        default=os.environ.get("QINIU_SECRET_KEY"),
    )
    parser.add_argument("--qiniu-bucket", default=os.environ.get("QINIU_BUCKET"))
    parser.add_argument(
        "--qiniu-public-base-url",
        default=os.environ.get("QINIU_PUBLIC_BASE_URL"),
    )
    parser.add_argument(
        "--qiniu-upload-host",
        default=os.environ.get("QINIU_UPLOAD_HOST", "https://upload.qiniup.com"),
    )
    parser.add_argument(
        "--r2-account-id",
        default=os.environ.get("MEDIA_R2_ACCOUNT_ID"),
    )
    parser.add_argument(
        "--r2-access-key-id",
        default=os.environ.get("MEDIA_R2_ACCESS_KEY_ID"),
    )
    parser.add_argument(
        "--r2-secret-access-key",
        default=os.environ.get("MEDIA_R2_SECRET_ACCESS_KEY"),
    )
    parser.add_argument("--r2-bucket", default=os.environ.get("MEDIA_R2_BUCKET"))
    parser.add_argument(
        "--r2-public-base-url",
        default=os.environ.get("MEDIA_R2_PUBLIC_BASE_URL"),
    )
    args = parser.parse_args()

    from app.services.platform_storage_provision_service import (
        QiniuCredentials,
        R2Credentials,
        build_platform_storage_status,
        verify_current,
        verify_qiniu,
        verify_r2,
    )

    qiniu_explicit = all(
        [
            args.qiniu_access_key,
            args.qiniu_secret_key,
            args.qiniu_bucket,
            args.qiniu_public_base_url,
        ]
    )
    r2_explicit = all(
        [
            args.r2_account_id,
            args.r2_access_key_id,
            args.r2_secret_access_key,
            args.r2_bucket,
        ]
    )

    if args.target == "all" and not qiniu_explicit and not r2_explicit:
        payload = verify_current(target="all")
        payload["status"] = build_platform_storage_status()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Overall: {payload['overall']}")
            for r in payload["results"]:
                print(f"  [{r.get('status')}] {r.get('target')}: {r.get('message')}")
        return 0 if payload["overall"] in ("pass", "skip", "warn") else 1

    results: list[dict] = []

    if args.target in ("qiniu", "all"):
        if qiniu_explicit:
            creds = QiniuCredentials(
                access_key=args.qiniu_access_key,
                secret_key=args.qiniu_secret_key,
                bucket=args.qiniu_bucket,
                public_base_url=args.qiniu_public_base_url,
                upload_host=args.qiniu_upload_host,
            )
            results.append(verify_qiniu(creds))
        else:
            results.append(verify_current(target="qiniu")["results"][0])

    if args.target in ("r2", "all"):
        if r2_explicit:
            creds = R2Credentials(
                account_id=args.r2_account_id,
                access_key_id=args.r2_access_key_id,
                secret_access_key=args.r2_secret_access_key,
                bucket=args.r2_bucket,
                public_base_url=args.r2_public_base_url or "",
            )
            results.append(verify_r2(creds))
        elif args.target == "r2":
            results.append(verify_current(target="r2")["results"][0])
        else:
            results.append(
                {
                    "target": "r2",
                    "status": "skip",
                    "message": "R2 参数不全，跳过",
                }
            )

    statuses = {r.get("status") for r in results}
    overall = "fail" if "fail" in statuses else ("pass" if "pass" in statuses else "skip")
    payload = {
        "overall": overall,
        "results": results,
        "status": build_platform_storage_status(),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Overall: {overall}")
        for r in results:
            tag = r.get("status", "?")
            print(f"  [{tag}] {r.get('target')}: {r.get('message')}")
            if r.get("hint"):
                print(f"         hint: {r['hint']}")
            if r.get("warn"):
                print(f"         warn: {r['warn']}")

    return 0 if overall in ("pass", "skip", "warn") else 1


if __name__ == "__main__":
    raise SystemExit(main())
