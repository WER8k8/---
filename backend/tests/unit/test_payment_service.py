"""支付服务 API 单元测试 — WeChatPayService / PaymentService / 验签 / 幂等"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ── WeChatPayService ──────────────────────────────────────


class TestWeChatPayService:
    def test_is_configured_false_when_empty(self):
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        assert svc.is_configured is False

    def test_is_configured_true_when_mchid_appid_key_set(self, monkeypatch):
        from app.services.payment_service import WeChatPayService
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.load_wechat_pay_v3_config",
            lambda **kw: MagicMock(is_live=False),
        )
        svc = WeChatPayService(appid="wx123", mchid="mch456", api_key="key789")
        assert svc.is_configured is True

    def test_create_native_order_mock(self, monkeypatch):
        from app.services.payment_service import WeChatPayService
        mock_cfg = MagicMock()
        mock_cfg.is_live = False
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.load_wechat_pay_v3_config",
            lambda **kw: mock_cfg,
        )
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.payment_mock_allowed",
            lambda: True,
        )
        svc = WeChatPayService(notify_url="http://example.com/notify")
        result = svc.create_native_order("ord-001", 1000, "订阅续费")
        assert "code_url" in result
        assert "MOCK_ord-001" in result["code_url"]

    def test_create_native_order_not_configured_no_mock(self, monkeypatch):
        from app.services.payment_service import WeChatPayService
        mock_cfg = MagicMock()
        mock_cfg.is_live = False
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.load_wechat_pay_v3_config",
            lambda **kw: mock_cfg,
        )
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.payment_mock_allowed",
            lambda: False,
        )
        svc = WeChatPayService(appid="wx1", mchid="mch1")
        with pytest.raises(RuntimeError, match="微信支付未配置"):
            svc.create_native_order("ord-x", 100, "x")

    def test_verify_notify_no_secret_not_strict(self, monkeypatch):
        monkeypatch.delenv("PAYMENT_STRICT_VERIFY", raising=False)
        monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET", raising=False)
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        assert svc.verify_notify({"out_trade_no": "o1", "total_fee": "100"}, "") is True

    def test_verify_notify_no_secret_strict_mode(self, monkeypatch):
        monkeypatch.setenv("PAYMENT_STRICT_VERIFY", "1")
        monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET", raising=False)
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        # strict 且无 secret：未配置 sign 时返回 False
        assert svc.verify_notify({"out_trade_no": "o1"}, "") is False
        monkeypatch.delenv("PAYMENT_STRICT_VERIFY", raising=False)

    def test_verify_notify_hmac_valid(self, monkeypatch):
        import hmac, hashlib
        monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "mysecret")
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        data = {"out_trade_no": "o1", "total_fee": "500"}
        payload = "o1:500"
        sig = hmac.new(
            b"mysecret", payload.encode(), hashlib.sha256
        ).hexdigest()
        assert svc.verify_notify(data, sig) is True
        monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET", raising=False)

    def test_verify_notify_hmac_invalid(self, monkeypatch):
        monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "mysecret")
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        assert svc.verify_notify({"out_trade_no": "o1"}, "bad-sign") is False
        monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET", raising=False)

    def test_refund_mock(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.payment_mock_allowed",
            lambda: True,
        )
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        result = svc.refund("ord-1", 200, 1000)
        assert result["status"] == "SUCCESS"
        assert result["out_refund_no"].startswith("REF")

    def test_refund_not_configured_raises(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.wechat_pay_v3.payment_mock_allowed",
            lambda: False,
        )
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService()
        with pytest.raises(RuntimeError, match="微信退款未配置"):
            svc.refund("ord-1", 100, 500)

    def test_md5_sign(self):
        from app.services.payment_service import WeChatPayService
        svc = WeChatPayService(api_key="testkey")
        sig = svc._md5_sign({"nonce": "abc", "total_fee": "100"})
        assert isinstance(sig, str)
        assert len(sig) == 32  # MD5 hex length


# ── PaymentService ─────────────────────────────────────────


class TestPaymentService:
    def test_init(self):
        from app.services.payment_service import PaymentService
        db = MagicMock()
        svc = PaymentService(db)
        assert svc.db == db

    def test_verify_notify_hmac_match(self):
        from app.services.payment_service import PaymentService
        db = MagicMock()
        svc = PaymentService(db)
        import hmac, hashlib, os
        secret = "test-secret"
        os.environ["PAYMENT_WEBHOOK_SECRET"] = secret
        try:
            data = {"out_trade_no": "o1", "total_fee": "200"}
            payload = "o1:200"
            sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
            assert svc.verify_notify(data, sig) is True
        finally:
            del os.environ["PAYMENT_WEBHOOK_SECRET"]

    def test_verify_notify_hmac_mismatch(self):
        from app.services.payment_service import PaymentService
        db = MagicMock()
        svc = PaymentService(db)
        import os
        os.environ["PAYMENT_WEBHOOK_SECRET"] = "s1"
        try:
            assert svc.verify_notify({"out_trade_no": "o1"}, "wrong-sig") is False
        finally:
            del os.environ["PAYMENT_WEBHOOK_SECRET"]

    def test_verify_notify_no_secret_not_strict(self):
        from app.services.payment_service import PaymentService
        db = MagicMock()
        svc = PaymentService(db)
        import os
        os.environ.pop("PAYMENT_WEBHOOK_SECRET", None)
        os.environ.pop("PAYMENT_STRICT_VERIFY", None)
        assert svc.verify_notify({"out_trade_no": "o1"}, "") is True
