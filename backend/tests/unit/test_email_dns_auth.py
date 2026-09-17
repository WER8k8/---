"""§5 SPF/DKIM/DMARC 邮件认证服务单元测试（纯逻辑，不依赖真实 DNS/cryptography）。"""

from __future__ import annotations

from app.services.email_dns_auth_service import (
    build_dns_records,
    compute_deliverability_score,
    generate_dkim_keypair,
    generate_dkim_record,
    generate_dmarc_record,
    generate_spf_record,
    low_deliverability_warning,
    parse_bounce,
)


class TestSPF:
    def test_spf_contains_v_all(self):
        rec = generate_spf_record("mail.example.com", ["203.0.113.5"], ["sendgrid.net"])
        assert rec.startswith("v=spf1")
        assert rec.endswith("-all")
        assert "include:sendgrid.net" in rec
        assert "ip4:203.0.113.5" in rec

    def test_spf_minimal(self):
        rec = generate_spf_record("d.com", ["10.0.0.1"])
        assert "v=spf1" in rec and "-all" in rec


class TestDKIM:
    def test_keypair_shape(self):
        kp = generate_dkim_keypair("sel1", 2048)
        assert kp.selector == "sel1"
        assert kp.key_size_bits == 2048
        # 无论 mock 还是真实，公钥值非空
        assert kp.public_key_base64
        assert not kp.private_key_pem.startswith("MISSING")

    def test_record_dns_name(self):
        rec = generate_dkim_record("mail.example.com", "sel1")
        assert rec["dns_name"] == "sel1._domainkey.mail.example.com"
        assert rec["dns_type"] == "TXT"
        assert rec["record_value"].startswith("v=DKIM1")
        assert "p=" in rec["record_value"]


class TestDMARC:
    def test_dmarc_reject_policy(self):
        sub, txt = generate_dmarc_record("d.com", "reject", rua="admin@d.com")
        assert sub == "_dmarc.d.com"
        assert "p=reject" in txt
        assert "rua=mailto:admin@d.com" in txt

    def test_dmarc_invalid_policy_raises(self):
        import pytest
        with pytest.raises(ValueError):
            generate_dmarc_record("d.com", "bogus")


class TestDeliverability:
    def test_score_full_deliver(self):
        assert compute_deliverability_score(100, 100) == 100.0

    def test_score_penalty(self):
        s = compute_deliverability_score(100, 80, bounced=10, spam=5)
        assert 0 <= s < 80.0

    def test_zero_sent(self):
        assert compute_deliverability_score(0, 0) == 0.0

    def test_low_warn(self):
        w = low_deliverability_warning(40.0)
        assert w and w["level"] == "warn"
        assert low_deliverability_warning(95.0) is None


class TestBounceParse:
    def test_bounce_detected(self):
        r = parse_bounce("Delivery Status: 5.1.1 User unknown - <no@x.com>")
        assert r["is_bounce"] is True

    def test_normal_delivery(self):
        r = parse_bounce("250 2.0.0 OK delivered successfully")
        assert r["is_bounce"] is False


class TestBuildAll:
    def test_build_dns_records(self):
        out = build_dns_records("mail.example.com", mail_servers=["203.0.113.5"], dmarc_policy="quarantine")
        assert "spf" in out and "dkim" in out and "dmarc" in out
        assert out["dmarc"]["value"].startswith("v=DMARC1")
        # 私钥不出 DNS 区（dkim 块内无 private key），单独字段保留
        assert "private_key_pem" not in out["dkim"]
        assert "dkim_private_key_pem" in out
