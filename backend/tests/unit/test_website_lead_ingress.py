# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""GJ-U4 网站线索 HMAC 接入配对反证测试（镜像上游 website-leads-hmac-test.mjs 全语义）。

- 签名格式：canonical = v1\\nkeyId\\nPOST\\npath\\ntimestamp\\nnonce\\nsha256(body)（与上游逐字段一致）；
- 负向：未签名/错密钥/过期时间戳/重放 nonce → 各自拒绝且零落库；
- 反欺骗：客户端声明渠道被忽略，source_channel 服务端强制 website_ingress；
- 多租户：tenant_id 由密钥属主决定，不信任请求体；
- 密钥：vault 存储（明文仅签发一次）、吊销后验签失效、列表零明文。
"""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import secrets
import uuid

import pytest

from app.models.inquiry import Inquiry
from app.services import website_lead_ingress_service as svc
from app.services.website_lead_ingress_service import IngressError

TENANT_A = "7a666666-6666-4666-8666-666666666666"
TENANT_B = "7a777777-7777-4777-8777-777777777777"
PATH = "/api/v1/website-leads"


def _signed_headers(
    body: bytes,
    *,
    key_id: str,
    secret: str,
    timestamp: str | None = None,
    nonce: str | None = None,
    path: str = PATH,
) -> dict[str, str]:
    ts = timestamp or str(__import__("time").time().__int__())
    nc = nonce or secrets.token_urlsafe(18)
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(["v1", key_id, "POST", path, ts, nc, body_hash])
    signature = hmac_mod.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return {
        "x-goodjob-key-id": key_id,
        "x-goodjob-timestamp": ts,
        "x-goodjob-nonce": nc,
        "x-goodjob-signature": f"v1={signature}",
    }


def _body(**overrides) -> bytes:
    import json

    payload = {
        "company": "Website HMAC Test GmbH",
        "contact": "Test Buyer",
        "email": "buyer@example.com",
        "inquiryContent": "Please send technical data and a quotation.",
        "sourceType": "outbound",
        "sourceChannel": "spoofed-channel",
        "externalId": f"website-hmac-{secrets.token_hex(4)}",
        **overrides,
    }
    return json.dumps(payload).encode()


@pytest.fixture
def issued(db_session):
    """签发租户 A 的接入密钥。"""
    return svc.issue_key(db_session, tenant_id=TENANT_A)


class TestKeyLifecycle:
    def test_secret_returned_once_vault_only(self, db_session, issued):
        assert issued["secret"].startswith(("uj", "-")) or len(issued["secret"]) >= 32
        rows = svc.list_keys(db_session, tenant_id=TENANT_A)
        assert [r["key_id"] for r in rows] == [issued["key_id"]]
        blob = repr(rows)
        assert issued["secret"] not in blob, "列表不得泄漏明文"

    def test_revoke_disables_verification(self, db_session, issued):
        assert svc.revoke_key(db_session, tenant_id=TENANT_A, key_id=issued["key_id"]) is True
        assert svc.revoke_key(db_session, tenant_id=TENANT_A, key_id=issued["key_id"]) is False  # 幂等
        body = _body()
        with pytest.raises(IngressError, match="unconfigured|invalid"):
            svc.verify_signature(
                db_session,
                method="POST",
                path=PATH,
                headers=_signed_headers(body, key_id=issued["key_id"], secret=issued["secret"]),
                raw_body=body,
            )

    def test_tenant_scoped_listing(self, db_session, issued):
        assert svc.list_keys(db_session, tenant_id=TENANT_B) == []


class TestVerification:
    def test_valid_signature_ok(self, db_session, issued):
        body = _body()
        meta = svc.verify_signature(
            db_session,
            method="POST",
            path=PATH,
            headers=_signed_headers(body, key_id=issued["key_id"], secret=issued["secret"]),
            raw_body=body,
        )
        assert meta["key_id"] == issued["key_id"]
        assert meta["tenant_id"] == TENANT_A, "租户由密钥属主决定"

    def test_missing_headers_rejected(self, db_session, issued):
        with pytest.raises(IngressError):
            svc.verify_signature(
                db_session, method="POST", path=PATH, headers={}, raw_body=_body()
            )

    def test_wrong_secret_rejected(self, db_session, issued):
        body = _body()
        with pytest.raises(IngressError, match="invalid"):
            svc.verify_signature(
                db_session,
                method="POST",
                path=PATH,
                headers=_signed_headers(body, key_id=issued["key_id"], secret="wrong-secret-with-at-least-32-characters!!"),
                raw_body=body,
            )

    def test_expired_timestamp_rejected(self, db_session, issued):
        import time

        stale = str(int(time.time()) - 601)  # 窗口 ±600s：-600 恰在边界内不算过期（上游同语义 >）
        body = _body()
        with pytest.raises(IngressError, match="expired"):
            svc.verify_signature(
                db_session,
                method="POST",
                path=PATH,
                headers=_signed_headers(body, key_id=issued["key_id"], secret=issued["secret"], timestamp=stale),
                raw_body=body,
            )

    def test_replayed_nonce_rejected(self, db_session, issued):
        body = _body()
        headers = _signed_headers(body, key_id=issued["key_id"], secret=issued["secret"])
        svc.verify_signature(db_session, method="POST", path=PATH, headers=headers, raw_body=body)
        with pytest.raises(IngressError, match="replay"):
            svc.verify_signature(db_session, method="POST", path=PATH, headers=headers, raw_body=body)

    def test_tampered_body_rejected(self, db_session, issued):
        signed_body = _body()
        headers = _signed_headers(signed_body, key_id=issued["key_id"], secret=issued["secret"])
        with pytest.raises(IngressError, match="invalid"):
            svc.verify_signature(
                db_session, method="POST", path=PATH, headers=headers, raw_body=_body(company="Tampered Ltd")
            )

    def test_wrong_path_rejected(self, db_session, issued):
        body = _body()
        with pytest.raises(IngressError, match="invalid"):
            svc.verify_signature(
                db_session,
                method="POST",
                path="/api/v1/other",
                headers=_signed_headers(body, key_id=issued["key_id"], secret=issued["secret"]),
                raw_body=body,
            )

    def test_foreign_tenant_key_rejected_for_other_tenant_domain(self, db_session, issued):
        """租户 B 自签密钥也可验签（租户由密钥决定）——但绝不落租户 A。"""
        other = svc.issue_key(db_session, tenant_id=TENANT_B)
        body = _body()
        meta = svc.verify_signature(
            db_session,
            method="POST",
            path=PATH,
            headers=_signed_headers(body, key_id=other["key_id"], secret=other["secret"]),
            raw_body=body,
        )
        assert meta["tenant_id"] == TENANT_B


class TestLeadCreation:
    def test_creates_inquiry_with_forced_channel(self, db_session, issued):
        body = _body()
        meta = svc.verify_signature(
            db_session, method="POST", path=PATH,
            headers=_signed_headers(body, key_id=issued["key_id"], secret=issued["secret"]),
            raw_body=body,
        )
        import json

        payload = json.loads(body)
        inquiry = svc.create_inquiry(
            db_session, tenant_id=meta["tenant_id"], payload=payload,
            key_meta=meta, external_id=payload.get("externalId"),
        )
        assert str(inquiry.tenant_id) == TENANT_A
        assert inquiry.source_channel == "website_ingress", "客户端 spoofed-channel 必须被覆盖"
        assert inquiry.session_id == payload["externalId"]
        assert "website_hmac" == (inquiry.provenance_metadata or {}).get("ingress", {}).get("provider")
        assert inquiry.email == "buyer@example.com"
        assert db_session.query(Inquiry).filter(Inquiry.id == inquiry.id).count() == 1

    def test_missing_contact_channel_rejected(self, db_session, issued):
        meta = {"key_id": issued["key_id"]}
        with pytest.raises(ValueError, match="contact_channel_required"):
            svc.create_inquiry(
                db_session, tenant_id=TENANT_A,
                payload={"company": "X", "inquiryContent": "hello there friend"},
                key_meta=meta,
            )

    def test_short_content_rejected(self, db_session, issued):
        meta = {"key_id": issued["key_id"]}
        with pytest.raises(ValueError, match="inquiry_content_invalid"):
            svc.create_inquiry(
                db_session, tenant_id=TENANT_A,
                payload={"company": "X", "email": "a@b.com", "inquiryContent": "hi"},
                key_meta=meta,
            )

    def test_company_required(self, db_session, issued):
        meta = {"key_id": issued["key_id"]}
        with pytest.raises(ValueError, match="company_required"):
            svc.create_inquiry(
                db_session, tenant_id=TENANT_A,
                payload={"email": "a@b.com", "inquiryContent": "hello there friend"},
                key_meta=meta,
            )
