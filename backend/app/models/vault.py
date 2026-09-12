"""凭证库持久化模型（总纲 §1.2 / §4.6 / §8 迁移 087；轮20）。

credentials：统一密钥入库加密（AES-256-GCM 默认 / SM4 国密可选），
AAD 四元绑定（租户/属主/连接/工件）——解密必须携带与加密时一致的
四元上下文，防止凭证跨租户、跨连接挪用。授权关系 credential_grants
控制谁能读哪个凭证（默认仅属主上下文可读）。

对应总纲裁决：
- §3.1「credential Vault（复用 field_crypto + gm_crypto，AAD 绑定）」；
- §8 087_credential_vault「credentials（SM4，AAD 四元绑定）+ 授权关系」；
- §7.2 出站必经 Policy 裁决，token 一律入 Vault（AAD 绑定 tenant+account）。
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import UUID_TYPE, Base

# 凭证状态：active 可用；rotated 已轮换（被新凭证替代）；revoked 已吊销
CREDENTIAL_STATUSES = ("active", "rotated", "revoked")

# 属主类型：凭证归谁所有
OWNER_TYPES = ("tenant", "agent", "user", "plugin", "mcp_server", "channel_account")

# 连接类型：凭证服务于哪类外部连接
CONNECTION_TYPES = (
    "mcp_server",
    "email",
    "whatsapp",
    "api",
    "datasource",
    "model_provider",
    "platform",
)

# 工件类型：凭证本身是什么形态
ARTIFACT_TYPES = (
    "api_key",
    "api_token",
    "password",
    "oauth_refresh_token",
    "oauth_client_secret",
    "webhook_secret",
    "sm2_private_key",
)

# 加密后端：aes_gcm（默认，AAD 原生绑定）/ sm4（国密合规，AAD 经指纹绑定）
CRYPTO_BACKENDS = ("aes_gcm", "sm4")

# 授权对象类型
GRANTEE_TYPES = ("agent", "skill", "service", "user")

# 授权状态
GRANT_STATUSES = ("active", "revoked")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VaultCredential(Base):
    __tablename__ = "credentials"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)

    # ---- AAD 四元绑定：租户 / 属主 / 连接 / 工件 ----
    owner_type = Column(String(40), nullable=False)
    owner_id = Column(String(64), nullable=False)
    connection_type = Column(String(40), nullable=False)
    connection_id = Column(String(64), nullable=False, default="")
    artifact_type = Column(String(40), nullable=False)

    name = Column(String(120), nullable=False)
    # 密文（base64，含 nonce/IV；SM4 后端为 base64(nonce + ct)）
    ciphertext = Column(Text, nullable=False)
    # 四元绑定的指纹（sha256 hex），解密前先比对，快速拒绝跨上下文访问
    aad_fingerprint = Column(String(64), nullable=False)
    crypto_backend = Column(String(20), nullable=False, default="aes_gcm")
    key_version = Column(Integer, nullable=False, default=1)

    status = Column(String(20), nullable=False, default="active")
    rotated_from_id = Column(UUID_TYPE, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class CredentialGrant(Base):
    """授权关系：哪个执行体（agent/skill/service/user）被授权读取哪个凭证。"""

    __tablename__ = "credential_grants"

    id = Column(UUID_TYPE, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(UUID_TYPE, ForeignKey("tenants.id"), nullable=True, index=True)
    credential_id = Column(
        UUID_TYPE, ForeignKey("credentials.id"), nullable=False, index=True
    )

    grantee_type = Column(String(20), nullable=False)
    grantee_id = Column(String(64), nullable=False)
    scope_json = Column(Text, nullable=True)  # e.g. ["read"]

    granted_by = Column(String(64), nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active")
