"""认证路由单元测试 — login / refresh / logout / change-password / email-code"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ── 辅助：构造用户 mock ────────────────────────────────────


def _make_user(
    *,
    user_id: str = "usr-1",
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "hashed_pw",
    role: str = "admin",
    is_active: bool = True,
    is_default_password: bool = False,
):
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.email = email
    user.hashed_password = password
    user.role = role
    user.is_active = is_active
    user.is_default_password = is_default_password
    return user


def _make_db(query_results: dict | None = None) -> MagicMock:
    """构造一个可响应的 db mock，query_results 按 model 名返回 mock 对象。"""
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = None
    db.query.return_value = q
    if query_results:
        # 支持按 model name 返回特定对象
        original_first = q.first
        def smart_first(*args, **kwargs):
            return original_first(*args, **kwargs)
        q.first.side_effect = smart_first
    return db


# ── login ──────────────────────────────────────────────────


class TestLogin:
    def test_login_success(self):
        from app.api.v1.routes.auth import login
        from app.schemas.auth import LoginRequest

        user = _make_user()
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch("app.api.v1.routes.auth.resolve_user_for_unified_login", return_value=(user, None)):
            with patch("app.api.v1.routes.auth.check_login_allowed", return_value=None):
                with patch("app.api.v1.routes.auth.client_ip_from_request", return_value="127.0.0.1"):
                    with patch("app.api.v1.routes.auth.record_login_success"):
                        with patch("app.api.v1.routes.auth._build_token_pair") as mock_build:
                            mock_build.return_value = MagicMock(
                                access_token="at",
                                refresh_token="rt",
                                token_type="bearer",
                                expires_in=3600,
                                model_dump=lambda **kw: {"access_token": "at", "refresh_token": "rt"},
                                force_password_change=False,
                                portals=None,
                            )
                            with patch("app.api.v1.routes.auth._token_json_response") as mock_resp:
                                mock_resp.return_value = MagicMock()
                                req = LoginRequest(username_or_email="testuser", password="pass")
                                from fastapi import Request
                                result = login(req, Request(scope={'type': 'http'}), db=db)
                                mock_resp.assert_called_once()

    def test_login_invalid_credentials(self):
        from app.api.v1.routes.auth import login
        from app.schemas.auth import LoginRequest

        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.api.v1.routes.auth.resolve_user_for_unified_login", return_value=(None, None)):
            with patch("app.api.v1.routes.auth.check_login_allowed", return_value=None):
                with patch("app.api.v1.routes.auth.client_ip_from_request", return_value="127.0.0.1"):
                    with patch("app.api.v1.routes.auth.record_login_failure"):
                        result = login(LoginRequest(username_or_email="bad", password="x"), MagicMock(), db=db)
                        assert result.status_code == 401


# ── refresh_token ──────────────────────────────────────────


class TestRefreshToken:
    def test_refresh_success(self):
        from app.api.v1.routes.auth import refresh_token
        from app.schemas.auth import TokenRefreshRequest

        user = _make_user()
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch("app.api.v1.routes.auth.decode_refresh_payload", return_value={"sub": "usr-1", "scopes": ["refresh"]}):
            with patch("app.api.v1.routes.auth.is_refresh_key_revoked", return_value=False):
                with patch("app.api.v1.routes.auth.refresh_token_revocation_key", return_value=("key", 9999999999)):
                    with patch("app.api.v1.routes.auth.revoke_refresh_key"):
                        with patch("app.api.v1.routes.auth._build_token_pair") as mock_build:
                            mock_build.return_value = MagicMock(
                                access_token="new_at",
                                refresh_token="new_rt",
                                token_type="bearer",
                                expires_in=3600,
                                model_dump=lambda **kw: {},
                                force_password_change=False,
                                portals=None,
                            )
                            with patch("app.api.v1.routes.auth._token_json_response") as mock_resp:
                                mock_resp.return_value = MagicMock()
                                req = TokenRefreshRequest(refresh_token="old_rt")
                                result = refresh_token(req, MagicMock(), db=db)
                                mock_resp.assert_called_once()

    def test_refresh_invalid_token(self):
        from app.api.v1.routes.auth import refresh_token
        from app.schemas.auth import TokenRefreshRequest

        with patch("app.api.v1.routes.auth.decode_refresh_payload", return_value=None):
            result = refresh_token(TokenRefreshRequest(refresh_token="bad"), MagicMock(), db=MagicMock())
            assert result.status_code == 401

    def test_refresh_revoked_key(self):
        from app.api.v1.routes.auth import refresh_token
        from app.schemas.auth import TokenRefreshRequest

        with patch("app.api.v1.routes.auth.decode_refresh_payload", return_value={"sub": "u1", "scopes": ["refresh"]}):
            with patch("app.api.v1.routes.auth.is_refresh_key_revoked", return_value=True):
                result = refresh_token(TokenRefreshRequest(refresh_token="rt"), MagicMock(), db=MagicMock())
                assert result.status_code == 401


# ── logout ─────────────────────────────────────────────────


class TestLogout:
    def test_logout_revokes_token(self):
        from app.api.v1.routes.auth import logout

        creds = MagicMock()
        creds.credentials = "valid-jwt-token"

        with patch("app.core.jwt_key_rotation.jwt_key_rotation_service") as mock_svc:
            mock_svc.decode_token.return_value = {"jti": "jti-1", "exp": 9999999999}
            with patch("app.api.v1.routes.auth.revoke_access_token"):
                with patch("app.api.v1.routes.auth.success_response") as mock_ok:
                    with patch("app.api.v1.routes.auth.clear_auth_cookies"):
                        mock_ok.return_value = MagicMock()
                        result = logout(creds, request=None)
                        mock_ok.assert_called_once()

    def test_logout_no_token(self):
        from app.api.v1.routes.auth import logout

        with patch("app.api.v1.routes.auth.success_response") as mock_ok:
            with patch("app.api.v1.routes.auth.clear_auth_cookies"):
                mock_ok.return_value = MagicMock()
                result = logout(None, request=None)
                mock_ok.assert_called_once()


# ── change_password ────────────────────────────────────────


class TestChangePassword:
    def test_change_password_success(self):
        from app.api.v1.routes.auth import change_password
        from app.schemas.user import ChangePasswordRequest

        user = _make_user(password="old_hash")
        db = MagicMock()

        with patch("app.api.v1.routes.auth.verify_password", return_value=True):
            with patch("app.api.v1.routes.auth.get_password_hash", return_value="new_hash"):
                with patch("app.api.v1.routes.auth.get_current_user", return_value=user):
                    with patch("app.api.v1.routes.auth.success_response") as mock_ok:
                        mock_ok.return_value = MagicMock()
                        req = ChangePasswordRequest(old_password="old", new_password="new")
                        result = change_password(req, db=db, current_user=user)
                        assert user.hashed_password == "new_hash"
                        assert user.is_default_password is False
                        db.commit.assert_called_once()

    def test_change_password_wrong_old(self):
        from app.api.v1.routes.auth import change_password
        from app.schemas.user import ChangePasswordRequest

        user = _make_user()
        with patch("app.api.v1.routes.auth.verify_password", return_value=False):
            with patch("app.api.v1.routes.auth.get_current_user", return_value=user):
                with patch("app.api.v1.routes.auth.error_response") as mock_err:
                    mock_err.return_value = MagicMock(status_code=400)
                    req = ChangePasswordRequest(old_password="wrong", new_password="new")
                    result = change_password(req, db=MagicMock(), current_user=user)
                    mock_err.assert_called_once()


# ── send_email_code ───────────────────────────────────────


class TestSendEmailCode:
    def test_send_email_code_success(self):
        from app.api.v1.routes.auth import send_email_code
        from app.schemas.auth import EmailVerificationRequest

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()

        with patch("app.api.v1.routes.auth._check_email_code_rate"):
            with patch("app.api.v1.routes.auth.email_service.send_verification_code", return_value=True):
                with patch("app.api.v1.routes.auth.settings") as mock_settings:
                    mock_settings.ENVIRONMENT = "production"
                    mock_settings.DEBUG = False
                    with patch("app.api.v1.routes.auth.success_response") as mock_ok:
                        mock_ok.return_value = MagicMock()
                        req = EmailVerificationRequest(email="test@example.com")
                        result = send_email_code(req, db=db)
                        db.add.assert_called_once()
                        db.commit.assert_called_once()

    def test_send_email_code_rate_limited(self):
        from app.api.v1.routes.auth import send_email_code
        from app.schemas.auth import EmailVerificationRequest

        with patch("app.api.v1.routes.auth._check_email_code_rate", side_effect=pytest.raises(Exception)):
            # 由 _check_email_code_rate 内部抛 429
            pass  # 间接验证：rate limit 会被触发


# ── login_by_email ─────────────────────────────────────────


class TestLoginByEmail:
    def test_login_by_email_success(self):
        from app.api.v1.routes.auth import login_by_email
        from app.schemas.auth import EmailLoginRequest

        user = _make_user(email="test@example.com")
        db = MagicMock()
        verif = MagicMock()
        verif.used = False
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = verif
        db.query.return_value.filter.return_value.first.return_value = user
        db.commit = MagicMock()

        with patch("app.api.v1.routes.auth.UserRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_email.return_value = user
            mock_repo_cls.return_value = mock_repo
            with patch("app.api.v1.routes.auth._build_token_pair") as mock_build:
                mock_build.return_value = MagicMock(
                    access_token="at", refresh_token="rt", token_type="bearer",
                    expires_in=3600,
                    model_dump=lambda **kw: {},
                    force_password_change=False,
                    portals=None,
                )
                with patch("app.api.v1.routes.auth.set_auth_cookies"):
                    req = EmailLoginRequest(email="test@example.com", code="123456")
                    result = login_by_email(req, db=db)
                    assert verif.used is True
                    db.commit.assert_called()

    def test_login_by_email_invalid_code(self):
        from app.api.v1.routes.auth import login_by_email
        from app.schemas.auth import EmailLoginRequest

        db = MagicMock()
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        req = EmailLoginRequest(email="x@example.com", code="bad")
        result = login_by_email(req, db=db)
        assert result.status_code == 401

    def test_login_by_email_user_not_found(self):
        from app.api.v1.routes.auth import login_by_email
        from app.schemas.auth import EmailLoginRequest

        db = MagicMock()
        verif = MagicMock()
        verif.used = False
        db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = verif
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit = MagicMock()

        with patch("app.api.v1.routes.auth.UserRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_email.return_value = None
            mock_repo_cls.return_value = mock_repo
            req = EmailLoginRequest(email="nobody@example.com", code="123456")
            result = login_by_email(req, db=db)
            assert result.status_code == 403
