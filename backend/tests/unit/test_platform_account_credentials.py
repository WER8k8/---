"""平台账号凭证落地单测：三处存放位、脱敏出参、必填组口径、指引自洽。

用内存 SQLite 只建 platforms / platform_accounts / platform_configs 三张表，
避开全库 create_all 的无关依赖。
"""

from __future__ import annotations

import json
import uuid

_ID = 0


def _uid() -> str:
    """UUID_TYPE 列只收合法 UUID，测试用递增命名空间生成，便于断言。"""
    global _ID
    _ID += 1
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"test-{_ID}"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.content import Platform, PlatformAccount, PlatformConfig
from app.services import platform_credential_guide as guide
from app.services.platform_account_service import (
    apply_credentials,
    collect_credentials,
    credential_status,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    for model in (Platform, PlatformAccount, PlatformConfig):
        model.__table__.create(engine)
    maker = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = maker()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def alibaba(db):
    plat = Platform(id=_uid(), name="Alibaba.com", platform_type="b2b", region="global")
    db.add(plat)
    db.commit()
    return plat


@pytest.fixture()
def account(db, alibaba):
    acc = PlatformAccount(
        id=_uid(), platform_id=alibaba.id, account_name="旗舰店", tenant_id=_uid()
    )
    db.add(acc)
    db.commit()
    return acc


def test_cookie_goes_to_cookie_data_and_mirrors_token(db, alibaba, account):
    written = apply_credentials(
        db, account=account, platform=alibaba, payload={"cookie": "SESS=secret-value"}
    )
    db.commit()
    assert written == 1
    assert account.cookie_data == "SESS=secret-value"
    #  cookie 同时镜像进该平台的 *_cookie 字段，统一读取口径
    assert account.token_data["alibaba_session_cookie"] == "SESS=secret-value"


def test_flat_credential_keys_land_in_token_or_configs(db, alibaba, account):
    apply_credentials(
        db,
        account=account,
        platform=alibaba,
        payload={"alibaba_member_id": "m1", "column_id": "c9"},
    )
    db.commit()
    assert account.token_data["alibaba_member_id"] == "m1"
    # 非凭证类运营参数走 configs，不混进 token_data
    row = db.query(PlatformConfig).filter_by(config_key="column_id").first()
    assert row is not None and row.config_value == "c9"


def test_token_data_merges_instead_of_overwriting(db, alibaba, account):
    account.token_data = {"alibaba_member_id": "m1"}
    apply_credentials(
        db, account=account, platform=alibaba, payload={"token_data": {"alibaba_access_token": "t"}}
    )
    db.commit()
    assert account.token_data == {"alibaba_member_id": "m1", "alibaba_access_token": "t"}


def test_configs_upsert_does_not_duplicate_rows(db, alibaba, account):
    payload = {"configs": {"appid": "ax", "password": "pw"}}
    apply_credentials(db, account=account, platform=alibaba, payload=payload)
    apply_credentials(db, account=account, platform=alibaba, payload={"configs": {"appid": "ay"}})
    db.commit()
    rows = db.query(PlatformConfig).filter_by(account_id=account.id).all()
    assert len(rows) == 2
    assert {r.config_key: r.config_value for r in rows} == {"appid": "ay", "password": "pw"}


def test_collect_priority_configs_below_cookie_below_token(db, alibaba, account):
    db.add(
        PlatformConfig(
            platform_id=alibaba.id, account_id=account.id, config_key="mic_access_token", config_value="from-config"
        )
    )
    account.cookie_data = "COOKIE=abc"
    account.token_data = {"alibaba_access_token": "from-token"}
    db.commit()
    merged = collect_credentials(db, account, alibaba)
    assert merged["mic_access_token"] == "from-config"
    assert merged["alibaba_session_cookie"] == "COOKIE=abc"
    assert merged["alibaba_access_token"] == "from-token"


def test_credential_status_masks_every_secret(db, alibaba, account):
    apply_credentials(
        db,
        account=account,
        platform=alibaba,
        payload={"alibaba_member_id": "member-9527", "cookie": "SESSION=abcdefghijklmnop"},
    )
    db.commit()
    status = credential_status(db, account, alibaba)
    dumped = json.dumps(status, ensure_ascii=False)
    assert "member-9527" not in dumped
    assert "abcdefghijklmnop" not in dumped
    assert status["has_credentials"] is True
    assert status["publish_ready"] is True
    assert status["missing_fields"] == []
    assert status["guide_key"] == "alibaba"
    masked = {f["name"]: f["masked"] for f in status["credential_fields"]}
    assert masked["alibaba_member_id"].startswith("me")
    assert "*" in masked["alibaba_member_id"]


def test_credential_status_reports_missing_group(db, alibaba, account):
    status = credential_status(db, account, alibaba)
    assert status["has_credentials"] is False
    assert status["publish_ready"] is False
    # 必填组「商家 ID」+「会话凭证二选一」→ 全缺时两条都列出候选
    assert set(status["missing_fields"]) == {
        "alibaba_member_id",
        "alibaba_access_token",
        "alibaba_session_cookie",
    }


def test_unknown_platform_has_no_field_gate(db, account):
    plat = Platform(id=_uid(), name="某个没登记的平台", platform_type="other")
    db.add(plat)
    db.commit()
    status = credential_status(db, account, plat)
    assert status["publish_ready"] is False
    assert status["guide_key"] is None


def test_nurture_params_are_not_treated_as_credentials(db, alibaba, account):
    account.token_data = {"nurture_daily_limit": "5", "column_id": "c1"}
    db.commit()
    status = credential_status(db, account, alibaba)
    names = {f["name"] for f in status["credential_fields"]}
    assert names == set()
    assert status["has_credentials"] is False


def test_guides_and_requirements_stay_consistent():
    """指引里承诺的字段必须与必填组口径同源，否则前端会照着错清单去申请。"""
    for entry in guide.GUIDES:
        key = entry["key"]
        required = guide.requirements_for(key)
        listed = {str(field.get("name") or "") for field in (entry.get("fields") or [])}
        for group in required:
            assert set(group) <= listed, f"{key} 指引缺字段 {set(group) - listed}"
        # 有字段级门禁的平台：指引列出的字段必须都落在必填组里，否则会让人白申请
        if required:
            declared = {name for group in required for name in group}
            assert listed <= declared, f"{key} 指引多列 {listed - declared}"
        for name in entry.get("platform_names", []):
            assert guide.guide_for_platform(name) is not None, name
            if required:
                assert guide.required_platform_key(name) == key, name


def test_env_status_returns_booleans_only():
    rows = guide.env_credential_status()
    assert rows
    for row in rows:
        assert set(row) == {"env", "configured"}
        assert isinstance(row["configured"], bool)
