# -*- coding: utf-8 -*-
"""Wave1 诚实接线：OAuth providers 明细 / QQ POST / referral 首付费幂等。"""
from __future__ import annotations

import uuid

from app.core.config import settings
from app.services.oauth_login import (
    SUPPORTED_OAUTH_PROVIDERS,
    oauth_providers_status_detail,
    verify_wechat_signature,
)


def test_oauth_providers_detail_lists_all_and_hints():
    detail = oauth_providers_status_detail()
    assert set(detail.keys()) == set(SUPPORTED_OAUTH_PROVIDERS)
    for p, info in detail.items():
        assert "enabled" in info and "configured" in info
        assert "missing_env" in info and "hint" in info
        if not info["configured"]:
            assert info["missing_env"], p


def test_wechat_signature_rejects_when_token_missing():
    old = settings.WECHAT_VERIFICATION_TOKEN
    try:
        settings.WECHAT_VERIFICATION_TOKEN = ""
        assert verify_wechat_signature("x", "1", "2") is False
        settings.WECHAT_VERIFICATION_TOKEN = "tok"
        assert verify_wechat_signature("0" * 40, "1", "2") is False
    finally:
        settings.WECHAT_VERIFICATION_TOKEN = old


def test_qq_token_exchange_uses_post(monkeypatch):
    import app.services.oauth_login as ol

    calls = {}

    class _Resp:
        status_code = 200
        text = '{"access_token":"AT","expires_in":7776000}'

        def raise_for_status(self):
            return None

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, **kw):
            if "token" in url:
                calls["token_method"] = "POST"
                calls["token_data"] = kw.get("data") or {}
                calls["token_params"] = kw.get("params")
            return _Resp()

        def get(self, url, **kw):
            calls.setdefault("get_params", []).append(kw.get("params"))
            return _Resp()

    monkeypatch.setattr(ol.httpx, "Client", _Client)
    monkeypatch.setattr(settings, "QQ_APP_ID", "appid", raising=False)
    monkeypatch.setattr(settings, "QQ_APP_KEY", "secret", raising=False)
    monkeypatch.setattr(ol, "_redirect_uri", lambda: "http://localhost/cb")
    try:
        ol._exchange_qq("code123")
    except Exception:
        pass
    assert calls.get("token_method") == "POST"
    assert calls.get("token_data", {}).get("client_secret") == "secret"
    assert calls.get("token_params") is None
    for p in calls.get("get_params") or []:
        if isinstance(p, dict):
            assert "client_secret" not in p


def test_referral_mark_invite_qualified_idempotent():
    """内存 SQLite：pending→rewarded 幂等，二次调用不再累加 total_earned。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.database import Base
    from app.models.referral import ReferralCode, ReferralRecord
    from app.models.tenant import Tenant
    from app.services.referral_service import ReferralService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    from app.models.tenant import TenantPlan

    plan = TenantPlan(id=str(uuid.uuid4()), name="Free", code=f"free-{uuid.uuid4().hex[:6]}")
    db.add(plan)
    db.flush()
    inviter = Tenant(id=str(uuid.uuid4()), name="Inviter", domain=f"inv-{uuid.uuid4().hex[:8]}.local", plan_id=plan.id)
    invited = Tenant(id=str(uuid.uuid4()), name="Invited", domain=f"invd-{uuid.uuid4().hex[:8]}.local", plan_id=plan.id)
    db.add_all([inviter, invited])
    db.flush()
    code = ReferralCode(tenant_id=inviter.id, code="ABCD1234", is_active=True, total_referred=1)
    db.add(code)
    db.flush()
    db.add(
        ReferralRecord(
            code_id=code.id,
            inviter_tenant_id=inviter.id,
            invited_tenant_id=invited.id,
            status="pending",
        )
    )
    db.commit()

    svc = ReferralService(db)
    r1 = svc.mark_invite_qualified(invited.id)
    assert r1["qualified"] is True and r1["updated"] == 1
    earned_after_first = db.query(ReferralCode).filter(ReferralCode.id == code.id).one().total_earned
    r2 = svc.mark_invite_qualified(invited.id)
    assert r2["updated"] == 0
    earned_after_second = db.query(ReferralCode).filter(ReferralCode.id == code.id).one().total_earned
    assert earned_after_second == earned_after_first
    stats = svc.get_referral_stats(str(inviter.id))
    assert stats["qualification_rule"] == "first_paid"
    assert stats["total_rewarded"] == 1
    db.close()


def test_egress_payload_honest_fields():
    from app.services.egress_supplier_service import build_providers_page_payload
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        payload = build_providers_page_payload(db)
        assert "auto_purchase_ready" in payload
        assert "mode_hint" in payload
        assert payload.get("checklist")
        for p in payload.get("providers") or []:
            assert "has_token" in p
            assert "ready" in p
    finally:
        db.close()
