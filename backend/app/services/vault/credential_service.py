"""凭证库服务（总纲 §3.1/§8 迁移 087；轮20）。

统一密钥入库：store（加密+AAD 四元绑定）→ resolve（解密，校验绑定与
授权）→ rotate（轮换，旧凭证置 rotated）→ revoke（吊销）。
授权关系 grant_access/revoke_grant 控制 agent/skill/service/user 可读。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.vault import (
    ARTIFACT_TYPES,
    CONNECTION_TYPES,
    CREDENTIAL_STATUSES,
    CRYPTO_BACKENDS,
    GRANTEE_TYPES,
    OWNER_TYPES,
    CredentialGrant,
    VaultCredential,
)
from app.services.vault.crypto import (
    AadMismatchError,
    aad_fingerprint,
    decrypt_with_aad,
    encrypt_with_aad,
)

VAULT_REF_PREFIX = "vault://credential/"


class VaultError(ValueError):
    """凭证库业务错误（参数/状态/授权）。"""


class CredentialNotFoundError(VaultError):
    pass


class CredentialRevokedError(VaultError):
    pass


class GrantDeniedError(VaultError):
    pass


def make_vault_ref(credential_id: str) -> str:
    return f"{VAULT_REF_PREFIX}{credential_id}"


def parse_vault_ref(ref: str) -> str:
    """校验 vault 引用格式，返回凭证 ID。"""
    if not ref or not ref.startswith(VAULT_REF_PREFIX):
        raise VaultError(f"非法 vault ref: {ref!r}（应为 {VAULT_REF_PREFIX}<id>）")
    cred_id = ref[len(VAULT_REF_PREFIX):]
    if not cred_id:
        raise VaultError(f"非法 vault ref: {ref!r}（缺少凭证 ID）")
    return cred_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(dt: datetime) -> datetime:
    """SQLite 读回的 naive datetime 统一按 UTC 解释，避免 aware/naive 比较报错。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _expired(expires_at: datetime | None) -> bool:
    return expires_at is not None and _to_utc(expires_at) <= _utcnow()


class CredentialVaultService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------- 存入
    def store_credential(
        self,
        *,
        secret: str,
        tenant_id: str | None = None,
        owner_type: str,
        owner_id: str,
        connection_type: str,
        connection_id: str = "",
        artifact_type: str,
        name: str,
        crypto_backend: str = "aes_gcm",
        expires_at: datetime | None = None,
    ) -> VaultCredential:
        if owner_type not in OWNER_TYPES:
            raise VaultError(f"非法 owner_type: {owner_type!r}")
        if connection_type not in CONNECTION_TYPES:
            raise VaultError(f"非法 connection_type: {connection_type!r}")
        if artifact_type not in ARTIFACT_TYPES:
            raise VaultError(f"非法 artifact_type: {artifact_type!r}")
        if crypto_backend not in CRYPTO_BACKENDS:
            raise VaultError(f"非法 crypto_backend: {crypto_backend!r}")
        if not name or not name.strip():
            raise VaultError("凭证名不能为空")

        aad = aad_fingerprint(
            tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
        )
        ciphertext = encrypt_with_aad(
            secret,
            _aad_string_of(
                tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
            ),
            crypto_backend,
        )
        cred = VaultCredential(
            tenant_id=tenant_id,
            owner_type=owner_type,
            owner_id=str(owner_id),
            connection_type=connection_type,
            connection_id=str(connection_id or ""),
            artifact_type=artifact_type,
            name=name.strip(),
            ciphertext=ciphertext,
            aad_fingerprint=aad,
            crypto_backend=crypto_backend,
            status="active",
            expires_at=expires_at,
        )
        self.db.add(cred)
        self.db.commit()
        self.db.refresh(cred)
        return cred

    # ------------------------------------------------------------- 解析
    def resolve_credential(
        self,
        ref: str,
        *,
        tenant_id: str | None = None,
        owner_type: str,
        owner_id,
        connection_type: str,
        connection_id: str = "",
        artifact_type: str,
        grantee_type: str | None = None,
        grantee_id: str | None = None,
        touch: bool = True,
    ) -> str:
        """解密凭证：校验状态/过期/AAD 四元绑定/授权，返回明文。"""
        cred_id = parse_vault_ref(ref) if ref.startswith(VAULT_REF_PREFIX) else ref
        cred = self.db.query(VaultCredential).filter(VaultCredential.id == cred_id).first()
        if not cred:
            raise CredentialNotFoundError(f"credential_not_found: {cred_id}")
        if cred.status == "revoked":
            raise CredentialRevokedError(f"credential_revoked: {cred_id}")
        if cred.status != "active":
            raise CredentialRevokedError(f"credential_not_active: {cred.status}")
        if _expired(cred.expires_at):
            raise CredentialRevokedError(f"credential_expired: {cred_id}")

        fp = aad_fingerprint(
            tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
        )
        if fp != cred.aad_fingerprint:
            raise AadMismatchError(
                f"aad_mismatch: 凭证 {cred.name} 不属于当前上下文（租户/属主/连接/工件）"
            )

        if grantee_type is not None and grantee_id is not None:
            if grantee_type not in GRANTEE_TYPES:
                raise VaultError(f"非法 grantee_type: {grantee_type!r}")
            self._require_grant(cred, grantee_type, str(grantee_id))

        plaintext = decrypt_with_aad(
            cred.ciphertext,
            _aad_string_of(
                tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
            ),
            cred.crypto_backend,
        )
        if touch:
            cred.last_used_at = _utcnow()
            self.db.commit()
        return plaintext

    def _require_grant(self, cred: VaultCredential, grantee_type: str, grantee_id: str) -> None:
        grants = (
            self.db.query(CredentialGrant)
            .filter(
                CredentialGrant.credential_id == cred.id,
                CredentialGrant.grantee_type == grantee_type,
                CredentialGrant.grantee_id == grantee_id,
                CredentialGrant.status == "active",
            )
            .all()
        )
        for g in grants:
            if _expired(g.expires_at):
                continue
            return
        raise GrantDeniedError(
            f"grant_denied: {grantee_type}={grantee_id} 无凭证 {cred.name} 的有效授权"
        )

    # ------------------------------------------------------------- 轮换/吊销
    def rotate_credential(
        self,
        ref: str,
        *,
        new_secret: str,
        grantee_type: str | None = None,
        grantee_id: str | None = None,
    ) -> VaultCredential:
        """轮换：旧凭证置 rotated，新凭证继承四元绑定与授权。"""
        cred_id = parse_vault_ref(ref) if ref.startswith(VAULT_REF_PREFIX) else ref
        old = self.db.query(VaultCredential).filter(VaultCredential.id == cred_id).first()
        if not old:
            raise CredentialNotFoundError(f"credential_not_found: {cred_id}")
        if old.status != "active":
            raise CredentialRevokedError(f"credential_not_active: {old.status}")

        new = self.store_credential(
            secret=new_secret,
            tenant_id=old.tenant_id,
            owner_type=old.owner_type,
            owner_id=old.owner_id,
            connection_type=old.connection_type,
            connection_id=old.connection_id,
            artifact_type=old.artifact_type,
            name=old.name,
            crypto_backend=old.crypto_backend,
            expires_at=None,
        )
        new.rotated_from_id = old.id

        old.status = "rotated"
        # 授权平移到新凭证；旧凭证上的授权保留但随 rotated 状态失效
        grants = (
            self.db.query(CredentialGrant)
            .filter(
                CredentialGrant.credential_id == old.id,
                CredentialGrant.status == "active",
            )
            .all()
        )
        for g in grants:
            self.db.add(
                CredentialGrant(
                    tenant_id=g.tenant_id,
                    credential_id=new.id,
                    grantee_type=g.grantee_type,
                    grantee_id=g.grantee_id,
                    scope_json=g.scope_json,
                    granted_by=g.granted_by,
                    expires_at=g.expires_at,
                    status="active",
                )
            )
        self.db.commit()
        self.db.refresh(new)
        return new

    def revoke_credential(self, ref: str) -> VaultCredential:
        cred_id = parse_vault_ref(ref) if ref.startswith(VAULT_REF_PREFIX) else ref
        cred = self.db.query(VaultCredential).filter(VaultCredential.id == cred_id).first()
        if not cred:
            raise CredentialNotFoundError(f"credential_not_found: {cred_id}")
        cred.status = "revoked"
        for g in (
            self.db.query(CredentialGrant)
            .filter(
                CredentialGrant.credential_id == cred.id,
                CredentialGrant.status == "active",
            )
            .all()
        ):
            g.status = "revoked"
            g.revoked_at = _utcnow()
        self.db.commit()
        self.db.refresh(cred)
        return cred

    # ------------------------------------------------------------- 授权关系
    def grant_access(
        self,
        ref: str,
        *,
        grantee_type: str,
        grantee_id,
        granted_by: str | None = None,
        expires_at: datetime | None = None,
        scope=("read",),
    ) -> CredentialGrant:
        cred_id = parse_vault_ref(ref) if ref.startswith(VAULT_REF_PREFIX) else ref
        cred = self.db.query(VaultCredential).filter(VaultCredential.id == cred_id).first()
        if not cred:
            raise CredentialNotFoundError(f"credential_not_found: {cred_id}")
        if cred.status != "active":
            raise CredentialRevokedError(f"credential_not_active: {cred.status}")
        if grantee_type not in GRANTEE_TYPES:
            raise VaultError(f"非法 grantee_type: {grantee_type!r}")

        grant = CredentialGrant(
            tenant_id=cred.tenant_id,
            credential_id=cred.id,
            grantee_type=grantee_type,
            grantee_id=str(grantee_id),
            scope_json=json.dumps(list(scope), ensure_ascii=False),
            granted_by=granted_by,
            expires_at=expires_at,
            status="active",
        )
        self.db.add(grant)
        self.db.commit()
        self.db.refresh(grant)
        return grant

    def revoke_grant(self, grant_id: str) -> CredentialGrant:
        grant = (
            self.db.query(CredentialGrant).filter(CredentialGrant.id == grant_id).first()
        )
        if not grant:
            raise GrantDeniedError(f"grant_not_found: {grant_id}")
        grant.status = "revoked"
        grant.revoked_at = _utcnow()
        self.db.commit()
        self.db.refresh(grant)
        return grant

    def list_credentials(
        self, *, tenant_id: str | None = None, status: str | None = None
    ) -> list[dict]:
        q = self.db.query(VaultCredential)
        if tenant_id is not None:
            q = q.filter(VaultCredential.tenant_id == tenant_id)
        if status:
            q = q.filter(VaultCredential.status == status)
        out = []
        for c in q.order_by(VaultCredential.created_at.desc()).all():
            out.append(
                {
                    "id": str(c.id),
                    "vault_ref": make_vault_ref(str(c.id)),
                    "tenant_id": str(c.tenant_id) if c.tenant_id else None,
                    "owner_type": c.owner_type,
                    "owner_id": c.owner_id,
                    "connection_type": c.connection_type,
                    "connection_id": c.connection_id,
                    "artifact_type": c.artifact_type,
                    "name": c.name,
                    "crypto_backend": c.crypto_backend,
                    "status": c.status,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                    "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )
        return out


def _aad_string_of(
    tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
) -> str:
    from app.services.vault.crypto import aad_string

    return aad_string(
        tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
    )
