#!/usr/bin/env python3
"""ARCH-04 · 生成本地 staging 自签 SSL（docker/nginx/ssl）。"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSL_DIR = ROOT / "docker/nginx/ssl"
REPORT = ROOT / "docs/arch-04-https-compose-latest.json"


def main() -> int:
    SSL_DIR.mkdir(parents=True, exist_ok=True)
    fullchain = SSL_DIR / "fullchain.pem"
    privkey = SSL_DIR / "privkey.pem"
    generated = False

    if not fullchain.exists() or not privkey.exists():
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.x509.oid import NameOID
        except ImportError:
            print(json.dumps({"ok": False, "error": "pip install cryptography"}, indent=2))
            return 1

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "demo.youding.local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Youding Staging"),
            ]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName(n) for n in ("demo.youding.local", "localhost")]
                ),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        privkey.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        fullchain.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        generated = True

    report = {
        "ok": True,
        "task": "ARCH-04",
        "ssl_dir": str(SSL_DIR.relative_to(ROOT)),
        "fullchain": fullchain.exists(),
        "privkey": privkey.exists(),
        "generated_self_signed": generated,
        "domain_staging": "demo.youding.local",
        "compose_prod": "docker-compose.prod.yml",
        "note": "生产域证书由 Owner/Certbot 替换；本脚本仅 staging 自签",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
