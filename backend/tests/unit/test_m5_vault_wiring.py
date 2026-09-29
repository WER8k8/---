# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块 5 · M5 凭据 Vault 接线配对反证测试（契约 §4.3 优先级①）。

负向（2）：
1. test_vault_missing_ref_falls_back_to_tenant_account  —— 无 ref 不触 Vault
2. test_vault_failure_is_fail_closed                    —— Vault 解析失败不回退明文

正向（3）：
3. test_vault_success_returns_vault_source              —— ref 命中 → source=vault
4. test_vault_aad_binding_uses_tenant_platform_ids      —— AAD 四元绑定参数正确
5. test_credential_ref_column_persists_roundtrip        —— ORM 列 roundtrip（迁移 133 已建列）
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.content import PlatformAccount, PublishTask
from app.services.publish_service import PublishService


# ── 负向 ─────────────────────────────────────────────────────────

def test_vault_missing_ref_falls_back_to_tenant_account():
    """无 credential_ref → 不触 Vault，走优先级② tenant_account。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models import Base  # noqa
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng, tables=[
        PlatformAccount.__table__,
        PublishTask.__table__,
    ])
    session = Session(bind=eng)

    tid = str(uuid.uuid4())
    pid = str(uuid.uuid4())
    acct = PlatformAccount(
        tenant_id=tid, platform_id=pid,
        account_name="t", token_data={"app_id": "X"},
        is_active=True,
    )
    session.add(acct)
    session.commit()
    session.expunge_all()

    out = PublishService(session).resolve_publish_credential(tid, pid)
    assert out["source"] == "tenant_account"
    assert out["values"]["app_id"] == "X"
    assert out["credential_ref"] is None


def test_vault_failure_is_fail_closed():
    """有 credential_ref 但 Vault 解析失败 → fail-closed：不回退明文，直接 credential_missing。"""
    from app.services.vault.credential_service import (
        CredentialNotFoundError,
        CredentialVaultService,
    )

    db = MagicMock()
    # 让 PlatformAccount 查询返回带 ref 的账号
    fake_acct = MagicMock()
    fake_acct.id = "acct-1"
    fake_acct.credential_ref = "vault://credential/missing-id"
    fake_acct.token_data = {"app_id": "SHOULD_NOT_LEAK"}  # 故意带明文，验证不回落
    fake_acct.cookie_data = None
    q = MagicMock()
    q.filter.return_value.filter.return_value.filter.return_value.first.return_value = fake_acct
    db.query.side_effect = [q, MagicMock()]  # 1st: PlatformAccount, 2nd: PlatformConfig

    svc = PublishService.__new__(PublishService)
    svc.db = db

    with patch.object(
        CredentialVaultService, "resolve_credential",
        side_effect=CredentialNotFoundError("credential_not_found: missing-id"),
    ):
        out = svc.resolve_publish_credential("t1", "p1")

    # fail-closed：来源 none + credential_missing + 明文未泄漏
    assert out["source"] == "none"
    assert out["error_code"] == "credential_missing"
    assert out["values"] == {}
    assert "SHOULD_NOT_LEAK" not in str(out["values"])


# ── 正向 ─────────────────────────────────────────────────────────

def test_vault_success_returns_vault_source():
    """ref 命中 → source=vault + 解明文在 values['_vault_resolved']。

    代码路径：account.credential_ref 非空 → 走优先级 ① Vault；
    测试 mock 的 PlatformConfig 查询（db.query().filter().first()）必须返回 None，
    否则代码会落到 tenant_account 分支返回 MagicMock。
    """
    from app.services.vault.credential_service import CredentialVaultService

    class _Acct:
        id = "acct-2"
        credential_ref = "vault://credential/c1"

    # 代码内 `db.query(PlatformAccount)` 之后接 2 次 .filter() 再 .first()。
    # db.query 的 side_effect 必须精确：第 1 次调用返回 PlatformAccount 查询链（_Acct），
    # 第 2 次调用（PlatformConfig）返回 None。
    acct_q = MagicMock()
    acct_q.filter.return_value.filter.return_value.first.return_value = _Acct()
    cfg_q = MagicMock()
    cfg_q.filter.return_value.first.return_value = None  # 缺行即关
    db = MagicMock()
    db.query.side_effect = [acct_q, cfg_q]

    svc = PublishService.__new__(PublishService)
    svc.db = db

    with patch.object(
        CredentialVaultService, "resolve_credential",
        return_value="PLAINTEXT_SECRET",
    ) as m:
        out = svc.resolve_publish_credential("t9", "p9")

    # Vault 必须被调用一次
    m.assert_called_once()
    assert out["source"] == "vault"
    assert out["values"]["_vault_resolved"] == "PLAINTEXT_SECRET"
    assert out["credential_ref"] == "vault://credential/c1"
    assert out["error_code"] is None


def test_vault_aad_binding_uses_tenant_platform_ids():
    """AAD 四元绑定参数按契约 §4.3：owner_type='tenant' / owner_id=tenant_id /
    connection_type='platform' / connection_id=platform_id / artifact_type='api_token'。

    （2026-09-28 修正：原断言 'platform_credential' 不在 vault ARTIFACT_TYPES 词表，
    真实 resolve 恒抛 VaultError——M5 测试因全程 mock 未触雷；M6 统一两侧为 'api_token'。）"""
    from app.services.vault.credential_service import CredentialVaultService

    db = MagicMock()
    fake_acct = MagicMock()
    fake_acct.id = "acct-3"
    fake_acct.credential_ref = "vault://credential/c2"
    q = MagicMock()
    q.filter.return_value.filter.return_value.filter.return_value.first.return_value = fake_acct
    db.query.side_effect = [q, MagicMock()]

    svc = PublishService.__new__(PublishService)
    svc.db = db

    with patch.object(
        CredentialVaultService, "resolve_credential",
        return_value="X",
    ) as m:
        svc.resolve_publish_credential("tenant-A", "platform-B")

    # 校验 AAD 绑定参数
    call = m.call_args
    kwargs = call.kwargs
    assert kwargs["tenant_id"] == "tenant-A"
    assert kwargs["owner_type"] == "tenant"
    assert kwargs["owner_id"] == "tenant-A"
    assert kwargs["connection_type"] == "platform"
    assert kwargs["connection_id"] == "platform-B"
    assert kwargs["artifact_type"] == "api_token"


def test_credential_ref_column_persists_roundtrip():
    """ORM 列 roundtrip：迁移 133 已建列，写入/读回 credential_ref 应一致。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models import Base
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng, tables=[PlatformAccount.__table__])
    session = Session(bind=eng)

    acct = PlatformAccount(
        tenant_id=str(uuid.uuid4()),
        platform_id=str(uuid.uuid4()),
        account_name="t",
        credential_ref="vault://credential/c42",
        is_active=True,
    )
    session.add(acct)
    session.commit()
    session.expunge_all()

    got = session.query(PlatformAccount).filter(
        PlatformAccount.account_name == "t",
    ).first()
    assert got.credential_ref == "vault://credential/c42"
