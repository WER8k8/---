# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""开发信 SPF/DKIM/DMARC 邮件认证 —— §5 缺口补齐。

为租户发信域生成三类 DNS 记录 + DKIM 密钥对管理 + 送达率监控，
提升开发信（outbound email）的收件箱到达率、降低进垃圾箱概率。

设计原则：
- DNS 记录生成是纯字符串拼接，可离线单测
- 密钥用内置 RSA（cryptography），无密钥时降级为 mock 并明确标记（no_fake_delivery）
- 送达率监控解析 bounce/backscatter，低分预警
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# ── SPF ──────────────────────────────────────────────────────────
def generate_spf_record(domain: str, mail_servers: List[str], include_domains: Optional[List[str]] = None) -> str:
    """生成 SPF TXT 记录字符串。

    :param domain: 发信域（仅作记录命名，不进值）
    :param mail_servers: 允许发信的主机/网段列表，如 ["203.0.113.5", "198.51.100.0/24"]
    :param include_domains: 需 include 的第三方发信域，如 ["sendgrid.net"]
    """
    parts = ["v=spf1"]
    for server in mail_servers or []:
        s = (server or "").strip()
        if not s:
            continue
        # 网段 → ip4:，裸 IP → ip4: 前缀更明确
        if s.count(".") == 3 and not s.startswith("ip4"):
            parts.append(f"ip4:{s}")
        else:
            parts.append(s)
    for inc in include_domains or []:
        inc = (inc or "").strip()
        if inc:
            parts.append(f"include:{inc}")
    parts.append("-all")  # 硬失败：非授权源一律拒绝
    return " ".join(parts)


# ── DKIM ─────────────────────────────────────────────────────────
@dataclass
class DKIMKeyPair:
    selector: str
    public_key_base64: str   # DNS TXT 值（单行）
    private_key_pem: str
    key_size_bits: int = 2048
    mock: bool = False


def generate_dkim_keypair(selector: str = "default", bits: int = 2048) -> DKIMKeyPair:
    """生成 DKIM RSA 密钥对。

    有 cryptography 时用真实密钥；没有则降级为 mock 且 mock=True（禁止假成功）。
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding  # noqa: F401

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=int(bits))
        pub_der = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        pub_b64 = base64.b64encode(pub_der).decode("ascii")
        return DKIMKeyPair(
            selector=selector,
            public_key_base64=pub_b64,
            private_key_pem=priv_pem,
            key_size_bits=int(bits),
            mock=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EmailDNS] cryptography 不可用，DKIM 降级为 mock: %s", exc)
        return DKIMKeyPair(
            selector=selector,
            public_key_base64="MOCK-" + base64.b64encode(selector.encode()).decode("ascii"),
            private_key_pem="-----BEGIN MOCK RSA PRIVATE KEY-----\n(mock)\n-----END MOCK RSA PRIVATE KEY-----\n",
            key_size_bits=int(bits),
            mock=True,
        )


def generate_dkim_dns_record(selector: str, public_key_base64: str) -> tuple[str, str]:
    """返回 (dns子域, txt值)。DKIM 记录放在 <selector>._domainkey.<domain>。"""
    # DNS TXT 值：v=dkim1; k=rsa; p=<base64公钥>
    txt = f"v=DKIM1; k=rsa; p={public_key_base64}"
    subdomain = f"{selector}._domainkey"
    return subdomain, txt


def generate_dkim_record(domain: str, selector: str = "default", bits: int = 2048) -> dict[str, Any]:
    """一步生成 DKIM 密钥对 + DNS 记录（含真实/mock 标记）。"""
    kp = generate_dkim_keypair(selector, bits)
    subdomain, txt = generate_dkim_dns_record(selector, kp.public_key_base64)
    return {
        "domain": domain,
        "selector": selector,
        "dns_name": f"{subdomain}.{domain}",
        "dns_type": "TXT",
        "record_value": txt,
        "key_size_bits": kp.key_size_bits,
        "private_key_pem": kp.private_key_pem,
        "mock": kp.mock,
    }


# ── DMARC ────────────────────────────────────────────────────────
def generate_dmarc_record(domain: str, policy: str = "none", pct: int = 100,
                          rua: Optional[str] = None, fail_on_spf_dkim_mismatch: bool = True) -> tuple[str, str]:
    """返回 (dns子域 '_dmarc.<domain>', txt值)。

    policy: none / quarantine / reject
    """
    if policy not in ("none", "quarantine", "reject"):
        raise ValueError(f"invalid DMARC policy: {policy}")
    parts = ["v=DMARC1", f"p={policy}", f"pct={int(pct)}"]
    if fail_on_spf_dkim_mismatch:
        parts.append("adkim=s")
    parts.append("aspf=s")
    if rua:
        # rua 必须是 mailto: 地址
        if not str(rua).lower().startswith("mailto:"):
            rua = "mailto:" + rua
        parts.append(f"rua={rua}")
    return f"_dmarc.{domain}", " ".join(parts)


# ── 送达率监控 ────────────────────────────────────────────────────
_BOUNCE_MARKERS = [
    "delivery status: 4", "delivery status: 5", "user unknown",
    "mailbox unavailable", "undeliverable", "bounce", "recipient rejected",
    "message not delivered", "invalid recipient",
]


def parse_bounce(email_body: str) -> dict[str, Any]:
    """解析 bounce/backscatter 正文，返回是否投递失败 + 原因。"""
    text = (email_body or "").lower()
    reason = None
    for m in _BOUNCE_MARKERS:
        if m in text:
            reason = m
            break
    # 尝试抽取 5xx/4xx 状态码
    mcode = re.search(r"(?:4|5)(\d{2})\.\d{2}\.\d{2}", text)
    code = f"{mcode.group(0)}" if mcode else None
    return {"is_bounce": reason is not None, "reason": reason, "status_code": code}


@dataclass
class DeliverabilitySnapshot:
    domain: str
    sent: int
    delivered: int
    bounced: int
    spam: int
    score: float  # 0-100 送达率分

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_deliverability_score(sent: int, delivered: int, bounced: int = 0, spam: int = 0) -> float:
    """送达率分：投递成功占比为主，bounce/spam 额外扣分，0-100。"""
    if sent <= 0:
        return 0.0
    base = (delivered / sent) * 100.0
    penalty = ((bounced + spam) / sent) * 50.0
    return max(0.0, min(100.0, base - penalty))


LOW_DELIVERABILITY_THRESHOLD: float = 60.0


def low_deliverability_warning(score: float) -> Optional[dict[str, Any]]:
    """低于阈值返回预警 dict（供通知钩子），否则 None。"""
    if score >= LOW_DELIVERABILITY_THRESHOLD:
        return None
    return {
        "level": "warn",
        "message": f"邮件送达率 {score:.0f}% 低于阈值 {LOW_DELIVERABILITY_THRESHOLD:.0f}%，建议检查 SPF/DKIM/DMARC 配置与发信信誉",
        "score": round(score, 2),
    }


def build_dns_records(domain: str, *,
                      mail_servers: Optional[List[str]] = None,
                      include_domains: Optional[List[str]] = None,
                      dkim_selector: str = "default",
                      dkim_bits: int = 2048,
                      dmarc_policy: str = "none",
                      dmarc_rua: Optional[str] = None) -> dict[str, Any]:
    """一站式产出某发信域所需的全部 DNS 记录（SPF + DKIM + DMARC）。"""
    spf = generate_spf_record(domain, mail_servers or [], include_domains)
    dkim = generate_dkim_record(domain, dkim_selector, dkim_bits)
    dmarc_sub, dmarc_txt = generate_dmarc_record(domain, dmarc_policy, rua=dmarc_rua)
    return {
        "domain": domain,
        "spf": {"name": domain, "type": "TXT", "value": spf},
        "dkim": {k: v for k, v in dkim.items() if k != "private_key_pem"},  # 私钥不出 DNS
        "dmarc": {"name": dmarc_sub, "type": "TXT", "value": dmarc_txt},
        "dkim_private_key_pem": dkim["private_key_pem"],  # 单独存，不进 DNS
        "dkim_mock": dkim["mock"],
        "notes": "将 spf/dkim/dmarc 三条 TXT 记录加入域名 DNS；私钥用于 SMTP 发信签名。",
    }
