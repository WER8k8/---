"""凭证库包（总纲 §8 迁移 087；轮20）。"""

from app.services.vault.credential_service import (
    AadMismatchError,
    CredentialNotFoundError,
    CredentialRevokedError,
    CredentialVaultService,
    GrantDeniedError,
    VaultError,
    make_vault_ref,
    parse_vault_ref,
)

__all__ = [
    "AadMismatchError",
    "CredentialNotFoundError",
    "CredentialRevokedError",
    "CredentialVaultService",
    "GrantDeniedError",
    "VaultError",
    "make_vault_ref",
    "parse_vault_ref",
]
