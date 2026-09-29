# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""DSH 沙箱治理测试（修正设计稿 模块15 / Gate G10）。

锁定语义：
- 令牌：签发→验签往返；篡改/伪造 401；过期 401；载荷不含任何 DB/Redis 凭据；
- 网络 allowlist：白名单内 allow；未授权目标 deny + 审计落库；
- 生产 fail-closed：ENVIRONMENT=production 且 mode=in_process → ensure 503 + 审计 deny；
- governed_run_turn：开发 in_process 调用 client.run_turn（monkeypatch）并审计 allow；
- 模块15.6：所有 deny 决策在 harness_security_events 可查。
"""
from __future__ import annotations

import base64
import json

import pytest

from app.models.harness_security import HarnessSecurityEvent
from app.services import harness_sandbox_service as hss

TENANT = "9a111111-1111-4111-8111-111111111111"  # ⚠ sqlite UUID 列须含字母（见 outbox 坑位记录）


class TestTaskToken:
    def test_roundtrip(self):
        token = hss.issue_task_token(tenant_id=TENANT, task_id="task-1", ttl_seconds=60)
        payload = hss.verify_task_token(token)
        assert payload["tenant_id"] == TENANT
        assert payload["task_id"] == "task-1"

    def test_payload_contains_no_credentials(self):
        token = hss.issue_task_token(tenant_id=TENANT, task_id="task-1")
        body = token.split(".", 1)[0]
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        blob = json.dumps(payload)
        for forbidden in ("DATABASE_URL", "REDIS_PASSWORD", "SECRET_KEY", "postgres"):
            assert forbidden.lower() not in blob.lower(), forbidden

    def test_forged_token_rejected(self):
        token = hss.issue_task_token(tenant_id=TENANT, task_id="task-1")
        body, _sig = token.split(".", 1)
        forged = f"{body}." + "0" * 64  # 篡改签名
        with pytest.raises(hss.SandboxViolation) as ei:
            hss.verify_task_token(forged)
        assert ei.value.status_code == 401

    def test_expired_token_rejected(self, monkeypatch):
        token = hss.issue_task_token(tenant_id=TENANT, task_id="task-1", ttl_seconds=-1)
        with pytest.raises(hss.SandboxViolation) as ei:
            hss.verify_task_token(token)
        assert ei.value.code == "sandbox_token_expired"


class TestEgressAllowlist:
    def test_allowlisted_target_passes(self, db_session, monkeypatch):
        monkeypatch.setenv("DSH_EGRESS_ALLOWLIST", "api.deepseek.com")
        assert hss.check_network_target(
            db_session, "https://api.deepseek.com/v1", tenant_id=TENANT, trace_id="tr-1"
        ) is True

    def test_denied_target_audited(self, db_session, monkeypatch):
        monkeypatch.setenv("DSH_EGRESS_ALLOWLIST", "api.deepseek.com")
        with pytest.raises(hss.SandboxViolation) as ei:
            hss.check_network_target(
                db_session, "https://evil.example.com/exfil", tenant_id=TENANT, trace_id="tr-2"
            )
        assert ei.value.status_code == 403
        row = (
            db_session.query(HarnessSecurityEvent)
            .filter_by(operation="egress_check", decision="deny")
            .one()
        )
        assert row.network_target == "evil.example.com"
        assert row.policy == "egress_allowlist"


class TestProductionFailClosed:
    def test_production_auto_tightens_to_sandbox(self, monkeypatch):
        """生产未显式配置时自动收紧为 sandbox（绝不回退 in_process —— fail-closed）。"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("DSH_SANDBOX_MODE", raising=False)
        mode, _reason = hss.resolve_mode()
        assert mode == "sandbox"
        # 且放行后受 runner 门控：未部署 runner 时 governed 路径 503（见另一用例）

    def test_production_with_sandbox_ok(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DSH_SANDBOX_MODE", "sandbox")
        assert hss.resolve_mode()[0] == "sandbox"

    def test_dev_defaults_in_process(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("DSH_SANDBOX_MODE", raising=False)
        assert hss.resolve_mode()[0] == "in_process"


class TestGovernedRunTurn:
    def test_dev_in_process_calls_client_and_audits(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("DSH_SANDBOX_MODE", raising=False)
        monkeypatch.setattr(
            "app.services.deepseek_harness.client.run_turn",
            lambda prompt, **kw: {"final_response": "ok", "session_id": "s1",
                                  "finish_reason": None, "event_count": 0,
                                  "provider": "p", "model": "m", "profile": "prof"},
        )
        result = hss.governed_run_turn(db_session, tenant_id=TENANT, prompt="帮我找德国瓷砖买家")
        assert result["dispatch"] == "in_process"
        assert result["final_response"] == "ok"
        allow = (
            db_session.query(HarnessSecurityEvent)
            .filter_by(operation="mode_check", decision="allow")
            .one()
        )
        assert allow.policy == "sandbox_mode"

    def test_production_fail_closed_audited(self, db_session, monkeypatch):
        """显式 in_process + 生产 → fail-closed deny + 审计（设计稿 15.3 fail-closed）。"""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DSH_SANDBOX_MODE", "in_process")
        with pytest.raises(hss.SandboxViolation) as ei:
            hss.governed_run_turn(db_session, tenant_id=TENANT, prompt="x")
        assert ei.value.status_code == 503
        deny = (
            db_session.query(HarnessSecurityEvent)
            .filter_by(operation="mode_check", decision="deny")
            .one()
        )
        assert deny.policy == "sandbox_mode"

    def test_sandbox_mode_without_runner_is_honest_503(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DSH_SANDBOX_MODE", "sandbox")
        with pytest.raises(hss.SandboxViolation) as ei:
            hss.governed_run_turn(db_session, tenant_id=TENANT, prompt="x")
        assert ei.value.code == "sandbox_runner_not_deployed"
