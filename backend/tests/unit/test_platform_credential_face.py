# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199304817). All rights reserved.
"""模块5 · M6 凭据面配对反证测试（docs/模块5-凭据面收口契约-2026-09-28.md §4）。

- connect：凭据只进 Vault（AAD 四元），platform_accounts 明文列恒 NULL，
  login_status 恒 logged_out（凭据已存 ≠ 会话已验证）；
- 连通性：connect 后 resolve_publish_credential（M2 出口）必须 source=vault
  且能解回原信封 —— M5↔M6 artifact_type 统一为 api_token 的回归锁；
- disconnect：vault revoked + ref 清空 + 幂等；
- accounts：租户隔离 + 零明文；check：三态（有/无/吊销）；
- logs/stats：租户作用域真查询；501 余量 3 端点由 deadlock_guard 锁覆盖。
"""
from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
from app.models.content import Platform, PlatformAccount, PublishLog, PublishTask
from app.models.vault import CredentialGrant, VaultCredential
from app.services.publish_service import PublishService

# ⚠ 常量前缀勿用「数字+e」开头（如 7e66…）：去横线后会被 SQLite 数字亲和性
# 当科学计数法转成 REAL inf（UUID 列回读即崩）。用字母开头或无 e 形态。
TENANT_A = "7a666666-6666-4666-8666-666666666666"
TENANT_B = "7a777777-7777-4777-8777-777777777777"


@pytest.fixture
def db_session():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(
        eng,
        tables=[
            Platform.__table__,
            PlatformAccount.__table__,
            PublishTask.__table__,
            PublishLog.__table__,
            VaultCredential.__table__,
            CredentialGrant.__table__,
        ],
    )
    session = Session(bind=eng)
    yield session
    session.close()
    eng.dispose()


@pytest.fixture
def platform_row(db_session):
    p = Platform(
        id=str(uuid.uuid4()),
        name=f"平台-{uuid.uuid4().hex[:6]}",
        platform_type="b2b",
        is_active=True,
    )
    db_session.add(p)
    db_session.commit()
    return p


def _connect(db, platform, *, tenant=TENANT_A, token=None):
    return PublishService(db).connect_platform(
        tenant_id=tenant,
        platform_id=str(platform.id),
        account_name="主账号",
        token_data=token or {"app_id": "APP-1", "secret": "SEC-1"},
    )


class TestConnect:
    def test_stores_in_vault_only(self, db_session, platform_row):
        out = _connect(db_session, platform_row)

        assert out["session_verified"] is False
        assert out["login_status"] == "logged_out"
        assert out["credential_kind"] == "token"
        acct = db_session.query(PlatformAccount).filter(
            PlatformAccount.id == out["account_id"]).one()
        assert acct.credential_ref and acct.credential_ref.startswith("vault://credential/")
        assert acct.cookie_data is None and acct.token_data is None, "明文列必须恒 NULL"
        assert acct.login_status == "logged_out"

        cred = db_session.query(VaultCredential).one()
        assert cred.status == "active"
        assert "SEC-1" not in str(cred.ciphertext)[:64]  # 密文非明文（ smoke）

    def test_resolves_through_m2_exit(self, db_session, platform_row):
        """M6 存 → M2 出口解析：artifact_type 统一后 AAD 必匹配（跨批次回归锁）。"""
        _connect(db_session, platform_row)
        out = PublishService(db_session).resolve_publish_credential(
            TENANT_A, str(platform_row.id)
        )
        assert out["source"] == "vault"
        envelope = json.loads(out["values"]["_vault_resolved"])
        assert envelope["kind"] == "token"
        assert envelope["payload"]["app_id"] == "APP-1"

    def test_missing_payload_rejected(self, db_session, platform_row):
        with pytest.raises(ValueError, match="credential_payload_required"):
            PublishService(db_session).connect_platform(
                tenant_id=TENANT_A, platform_id=str(platform_row.id),
                account_name="x",
            )
        assert db_session.query(PlatformAccount).count() == 0
        assert db_session.query(VaultCredential).count() == 0

    def test_unknown_platform_rejected(self, db_session):
        with pytest.raises(LookupError, match="platform_not_found"):
            PublishService(db_session).connect_platform(
                tenant_id=TENANT_A, platform_id=str(uuid.uuid4()),
                account_name="x", token_data={"a": "b"},
            )

    def test_upsert_reconnect_replaces_ref(self, db_session, platform_row):
        first = _connect(db_session, platform_row)
        second = _connect(db_session, platform_row, token={"app_id": "APP-2"})
        assert first["account_id"] == second["account_id"], "同账号重连应 upsert 同一行"
        rows = db_session.query(PlatformAccount).count()
        assert rows == 1
        acct = db_session.query(PlatformAccount).one()
        assert acct.credential_ref == second["credential_ref"]


class TestDisconnect:
    def test_revokes_and_clears_idempotent(self, db_session, platform_row):
        out = _connect(db_session, platform_row)
        svc = PublishService(db_session)

        first = svc.disconnect_platform(tenant_id=TENANT_A, account_id=out["account_id"])
        assert first["credential_ref"] is None
        cred = db_session.query(VaultCredential).one()
        assert cred.status == "revoked"

        second = svc.disconnect_platform(tenant_id=TENANT_A, account_id=out["account_id"])
        assert second["credential_ref"] is None  # 幂等不报错

    def test_tenant_scoped(self, db_session, platform_row):
        out = _connect(db_session, platform_row, tenant=TENANT_A)
        with pytest.raises(LookupError, match="account_not_found"):
            PublishService(db_session).disconnect_platform(
                tenant_id=TENANT_B, account_id=out["account_id"]
            )


class TestListAccounts:
    def test_tenant_isolation_and_no_plaintext(self, db_session, platform_row):
        _connect(db_session, platform_row, tenant=TENANT_A)
        _connect(db_session, platform_row, tenant=TENANT_B)

        rows = PublishService(db_session).list_accounts(tenant_ids=[TENANT_A])
        assert len(rows) == 1
        blob = json.dumps(rows, ensure_ascii=False)
        assert "SEC-1" not in blob and "vault://" not in blob, "列表不得泄漏明文/ref"
        assert rows[0]["has_credential"] is True

        empty = PublishService(db_session).list_accounts(tenant_ids=[])
        assert empty == []


class TestCheckSession:
    def test_three_states(self, db_session, platform_row):
        out = _connect(db_session, platform_row)
        svc = PublishService(db_session)

        ok = svc.check_session(tenant_id=TENANT_A, account_id=out["account_id"])
        assert ok["credential_resolvable"] is True
        assert ok["session_verified"] is False, "诚实语义：非平台侧会话验证"

        svc.disconnect_platform(tenant_id=TENANT_A, account_id=out["account_id"])
        gone = svc.check_session(tenant_id=TENANT_A, account_id=out["account_id"])
        assert gone["credential_resolvable"] is False
        assert gone["reason"] == "no_credential"


class TestLogsAndStats:
    def test_logs_scoped_and_filtered(self, db_session, platform_row):
        tid_a, tid_b = TENANT_A, TENANT_B
        pa = PlatformAccount(
            tenant_id=tid_a, platform_id=str(platform_row.id), account_name="a",
        )
        pb = PlatformAccount(
            tenant_id=tid_b, platform_id=str(platform_row.id), account_name="b",
        )
        db_session.add_all([pa, pb])
        db_session.commit()
        task_a = PublishTask(
            platform_id=str(platform_row.id), account_id=str(pa.id),
            tenant_id=tid_a, status="failed",
        )
        task_b = PublishTask(
            platform_id=str(platform_row.id), account_id=str(pb.id),
            tenant_id=tid_b, status="success",
        )
        db_session.add_all([task_a, task_b])
        db_session.commit()
        db_session.add_all([
            PublishLog(task_id=str(task_a.id), level="error", message="A 失败日志"),
            PublishLog(task_id=str(task_b.id), level="info", message="B 成功日志"),
        ])
        db_session.commit()

        out = PublishService(db_session).get_publish_logs(tenant_ids=[tid_a])
        assert out["total"] == 1
        assert out["items"][0]["message"] == "A 失败日志"

        out_lv = PublishService(db_session).get_publish_logs(
            tenant_ids=[tid_a, tid_b], level="info"
        )
        assert out_lv["total"] == 1

    def test_stats_shape(self, db_session, platform_row):
        _connect(db_session, platform_row, tenant=TENANT_A)
        pa = db_session.query(PlatformAccount).one()
        db_session.add(PublishTask(
            platform_id=str(platform_row.id), account_id=str(pa.id),
            tenant_id=TENANT_A, status="pending",
        ))
        db_session.commit()

        stats = PublishService(db_session).get_publish_stats(tenant_ids=[TENANT_A])
        assert stats["tasks_by_status"] == {"pending": 1}
        assert stats["accounts_total"] == 1
        assert stats["accounts_with_credential"] == 1
        assert isinstance(stats["admitted_platform_count"], int)

    def test_empty_tenants_zero_stats(self, db_session):
        stats = PublishService(db_session).get_publish_stats(tenant_ids=[])
        assert stats["accounts_total"] == 0
        assert stats["tasks_by_status"] == {}
