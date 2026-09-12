"""凭证库加密层（总纲 §3.1/§8 迁移 087；轮20）。

- 默认后端 aes_gcm：AES-256-GCM（复用 field_crypto 的 HKDF 派生模式），
  AAD 原生绑定四元上下文，密文与上下文错一位即解密失败（InvalidTag）。
- 国密后端 sm4：SM4-ECB+PKCS7（app/core/gm_crypto），AAD 经两层绑定：
  ① 服务层 aad_fingerprint 指纹比对快速拒绝；② AAD 串入密钥派生，
  上下文不符则密钥不符，解密必然失败。
- 需要国密合规时以 VAULT_CRYPTO_BACKEND=sm4 切换；gmssl 未安装时
  显式请求 sm4 会抛 VaultCryptoError，默认路径不受影响。
"""

from __future__ import annotations

import base64
import hashlib
import os

VAULT_KEY_CONTEXT = b"uj-saas-credential-vault-v1"
AAD_SEP = "\x1f"

CRYPTO_BACKENDS = ("aes_gcm", "sm4")


class VaultCryptoError(RuntimeError):
    """Vault 加解密失败（密钥/后端/参数问题）。"""


class AadMismatchError(VaultCryptoError):
    """AAD 四元绑定校验失败：凭证在错误的上下文中被使用。"""


def aad_string(
    tenant_id,
    owner_type: str,
    owner_id,
    connection_type: str,
    connection_id,
    artifact_type: str,
) -> str:
    """四元绑定（租户/属主/连接/工件）→ AAD 字符串。"""
    return AAD_SEP.join(
        (
            str(tenant_id or ""),
            str(owner_type or ""),
            str(owner_id or ""),
            str(connection_type or ""),
            str(connection_id or ""),
            str(artifact_type or ""),
        )
    )


def aad_fingerprint(
    tenant_id,
    owner_type: str,
    owner_id,
    connection_type: str,
    connection_id,
    artifact_type: str,
) -> str:
    """AAD 指纹（sha256 hex）：落库字段，解密前快速比对。"""
    return hashlib.sha256(
        aad_string(
            tenant_id, owner_type, owner_id, connection_type, connection_id, artifact_type
        ).encode("utf-8")
    ).hexdigest()


def _secret_key() -> str:
    from app.core.config import settings

    return str(settings.SECRET_KEY)


def _vault_key() -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=VAULT_KEY_CONTEXT,
    )
    return hkdf.derive(_secret_key().encode())


def encrypt_with_aad(plaintext: str, aad: str, backend: str = "aes_gcm") -> str:
    """按后端加密，AAD 参与认证（返回 base64 密文）。"""
    if not plaintext:
        raise VaultCryptoError("empty_plaintext")
    if backend == "aes_gcm":
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        aesgcm = AESGCM(_vault_key())
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad.encode("utf-8"))
        return base64.b64encode(nonce + ct).decode("ascii")
    if backend == "sm4":
        from app.core.gm_crypto import resolve_sm4_key, sm4_encrypt

        key_material = f"{resolve_sm4_key(fallback_secret=_secret_key())}|{aad}"
        return sm4_encrypt(plaintext, key_material)
    raise VaultCryptoError(f"unknown_backend: {backend}")


def decrypt_with_aad(ciphertext: str, aad: str, backend: str = "aes_gcm") -> str:
    """按后端解密；AAD 不符（aes_gcm）或密钥不符（sm4）时抛错。"""
    if not ciphertext:
        raise VaultCryptoError("empty_ciphertext")
    if backend == "aes_gcm":
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        try:
            raw = base64.b64decode(ciphertext.encode("ascii"))
        except Exception as exc:  # noqa: BLE001
            raise VaultCryptoError("invalid_ciphertext") from exc
        nonce, ct = raw[:12], raw[12:]
        aesgcm = AESGCM(_vault_key())
        try:
            return aesgcm.decrypt(nonce, ct, aad.encode("utf-8")).decode("utf-8")
        except InvalidTag as exc:
            raise AadMismatchError("aad_mismatch_or_corrupted") from exc
    if backend == "sm4":
        from app.core.gm_crypto import GMCryptoError, resolve_sm4_key, sm4_decrypt

        key_material = f"{resolve_sm4_key(fallback_secret=_secret_key())}|{aad}"
        try:
            return sm4_decrypt(ciphertext, key_material)
        except GMCryptoError as exc:
            raise AadMismatchError("aad_mismatch_or_corrupted") from exc
    raise VaultCryptoError(f"unknown_backend: {backend}")
