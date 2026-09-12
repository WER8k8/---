"""ACME Service - Let's Encrypt SSL certificate auto-issuance.

Implements real ACMEv2 protocol interaction with Let's Encrypt,
including account registration, domain validation (DNS-01 / HTTP-01),
certificate issuance and renewal.
"""
import asyncio
import base64
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Let's Encrypt endpoints
LE_STAGING = "https://acme-staging-v02.api.letsencrypt.org/directory"
LE_PRODUCTION = "https://acme-v02.api.letsencrypt.org/directory"

# Retry configuration
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # seconds
CHALLENGE_POLL_INTERVAL = 3  # seconds
CHALLENGE_POLL_TIMEOUT = 300  # seconds (5 min)


def _b64url(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(s: str) -> bytes:
    """Base64url decode with padding restoration."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


# ---------------------------------------------------------------------------
# Cryptography helpers (graceful fallback)
# ---------------------------------------------------------------------------
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.x509.oid import NameOID

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    x509 = None
    default_backend = None
    hashes = None
    serialization = None
    rsa = None
    padding = None
    NameOID = None


class ACMEClient:
    """ACMEv2 client for Let's Encrypt.

    Implements the full ACME protocol flow:
    directory fetch → account registration → order creation →
    challenge validation → CSR finalization → certificate download.
    """
    def __init__(self, staging: bool = True):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param staging: 参数 staging
        :return: 返回处理结果。
        """
        self.directory_url = LE_STAGING if staging else LE_PRODUCTION
        self.directory: Dict[str, Any] = {}
        self.account_key: Any = None  # rsa.RSAPrivateKey when cryptography available
        self.account_url: str = ""
        self._nonce: str = ""
        self._http = httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Directory & Nonce management
    # ------------------------------------------------------------------
    async def initialize(self) -> None:
        """Fetch ACME directory and generate account key."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError(
                "cryptography library is required for ACME. "
                "Install it with: pip install cryptography"
            )

        # Fetch directory
        response = await self._http.get(self.directory_url)
        response.raise_for_status()
        self.directory = response.json()
        logger.info("ACME directory fetched: %s", list(self.directory.keys()))
        # Cache initial nonce
        if "newNonce" in self.directory:
            nonce_resp = await self._http.head(self.directory["newNonce"])
            self._nonce = nonce_resp.headers.get("Replay-Nonce", "")

        # Generate account key (RSA 2048)
        self.account_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        logger.info("ACME account key generated")

    async def _get_nonce(self) -> str:
        """Get a fresh replay nonce."""
        if self._nonce:
            nonce = self._nonce
            self._nonce = ""
            return nonce
        nonce_resp = await self._http.head(self.directory["newNonce"])
        return nonce_resp.headers.get("Replay-Nonce", "")

    # ------------------------------------------------------------------
    # JWK & JWS helpers
    # ------------------------------------------------------------------
    def _jwk(self) -> Dict[str, Any]:
        """Build the JSON Web Key from the account public key."""
        pub = self.account_key.public_key()
        pub_numbers = pub.public_numbers()
        return {
            "e": _b64url(
                pub_numbers.e.to_bytes((pub_numbers.e.bit_length() + 7) // 8, "big")
            ),
            "kty": "RSA",
            "n": _b64url(
                pub_numbers.n.to_bytes((pub_numbers.n.bit_length() + 7) // 8, "big")
            ),
        }

    def _jwk_thumbprint(self) -> str:
        """Compute JWK thumbprint per RFC 7638."""
        jwk = self._jwk()
        # Canonical ordering is required: e, kty, n
        canonical = json.dumps(
            {"e": jwk["e"], "kty": jwk["kty"], "n": jwk["n"]},
            separators=(",", ":"),
            sort_keys=True,
        )
        return _b64url(hashlib.sha256(canonical.encode()).digest())

    def _sign_jws(self, payload: Dict[str, Any], url: str, kid: str = "") -> Dict[str, str]:
        """Create a JWS signed with the account key.

        Args:
            payload: The ACME request payload.
            url: The target URL.
            kid: Key ID (account URL) — used after registration; omit for newAccount.
        """
        protected: Dict[str, Any] = {
            "alg": "RS256",
            "nonce": self._nonce or "",
            "url": url,
        }
        if kid:
            protected["kid"] = kid
        else:
            protected["jwk"] = self._jwk()

        protected_b64 = _b64url(json.dumps(protected, separators=(",", ":")).encode())
        payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{protected_b64}.{payload_b64}".encode()
        signature = self.account_key.sign(
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return {
            "protected": protected_b64,
            "payload": payload_b64,
            "signature": _b64url(signature),
        }

    async def _acme_post(self, url: str, payload: Dict[str, Any], kid: str = "") -> httpx.Response:
        """Send a signed ACME POST request."""
        for attempt in range(MAX_RETRIES):
            jws = self._sign_jws(payload, url, kid=kid)
            resp = await self._http.post(url, json=jws)
            # Save nonce for next request
            new_nonce = resp.headers.get("Replay-Nonce")
            if new_nonce:
                self._nonce = new_nonce

            if resp.status_code == 400 and "urn:ietf:params:acme:error:badNonce" in resp.text:
                logger.warning("ACME badNonce, retrying (attempt %d)", attempt + 1)
                await asyncio.sleep(RETRY_BASE_DELAY * (attempt + 1))
                continue

            return resp

        raise RuntimeError("ACME request failed after retries: badNonce loop")

    # ------------------------------------------------------------------
    # Account registration
    # ------------------------------------------------------------------
    async def register_account(self) -> str:
        """Register a new ACME account.

        Returns:
            str: Account URL.
        """
        contact_email = os.getenv("ACME_CONTACT_EMAIL", "")
        payload: Dict[str, Any] = {"termsOfServiceAgreed": True}
        if contact_email:
            payload["contact"] = [f"mailto:{contact_email}"]

        resp = await self._acme_post(self.directory["newAccount"], payload)
        data = resp.json()
        if resp.status_code in (201, 200):
            self.account_url = resp.headers.get("Location", "")
            if not self.account_url:
                self.account_url = data.get("location", "")
        else:
            # Account may already exist — try existing-key lookup
            if resp.status_code == 400 and "urn:ietf:params:acme:error:accountExists" in str(data):
                logger.info("ACME account already exists, performing key-change lookup")
                # Re-post with only returning existing account
                resp2 = await self._acme_post(
                    self.directory["newAccount"],
                    {"onlyReturnExisting": True},
                )
                self.account_url = resp2.headers.get("Location", "")
            else:
                raise RuntimeError(
                    f"ACME account registration failed: {resp.status_code} {data}"
                )

        logger.info("ACME account registered: %s", self.account_url)
        return self.account_url

    # ------------------------------------------------------------------
    # Order creation
    # ------------------------------------------------------------------
    async def create_order(self, domains: list[str]) -> Tuple[str, list[dict]]:
        """Create ACME order for domains.

        Args:
            domains: List of domain names.

        Returns:
            tuple: (order_url, authorizations)
        """
        identifiers = [{"type": "dns", "value": d} for d in domains]
        payload = {"identifiers": identifiers}
        resp = await self._acme_post(
            self.directory["newOrder"], payload, kid=self.account_url
        )
        data = resp.json()
        if resp.status_code not in (201, 200):
            raise RuntimeError(f"ACME order creation failed: {resp.status_code} {data}")

        order_url = resp.headers.get("Location", "")
        authorizations = []
        for authz_url in data.get("authorizations", []):
            authz_resp = await self._http.get(authz_url)
            authz_data = authz_resp.json()
            new_nonce = authz_resp.headers.get("Replay-Nonce")
            if new_nonce:
                self._nonce = new_nonce
            authorizations.append(authz_data)

        logger.info("ACME order created for domains: %s", domains)
        return order_url, authorizations

    # ------------------------------------------------------------------
    # Challenge validation
    # ------------------------------------------------------------------
    def compute_dns01_record(self, token: str) -> str:
        """Compute the value for the DNS-01 TXT record.

        The value is base64url(sha256(keyAuthorization)), where
        keyAuthorization = token + '.' + thumbprint.
        """
        thumbprint = self._jwk_thumbprint()
        key_auth = f"{token}.{thumbprint}"
        digest = hashlib.sha256(key_auth.encode()).digest()
        return _b64url(digest)

    def compute_http01_content(self, token: str) -> str:
        """Compute the content for the HTTP-01 challenge file."""
        thumbprint = self._jwk_thumbprint()
        return f"{token}.{thumbprint}"

    async def validate_challenge(self, challenge_url: str) -> bool:
        """Respond to an ACME challenge and poll until validated.

        Args:
            challenge_url: The challenge URL from the authorization.

        Returns:
            bool: True if validation successful.
        """
        # Tell ACME server we're ready for validation
        resp = await self._acme_post(
            challenge_url, {}, kid=self.account_url
        )
        if resp.status_code not in (200, 201):
            logger.warning("Challenge response failed: %s %s", resp.status_code, resp.text)

        # Poll until the challenge is validated or times out
        start = time.time()
        while time.time() - start < CHALLENGE_POLL_TIMEOUT:
            await asyncio.sleep(CHALLENGE_POLL_INTERVAL)
            poll_resp = await self._http.get(challenge_url)
            poll_data = poll_resp.json()
            new_nonce = poll_resp.headers.get("Replay-Nonce")
            if new_nonce:
                self._nonce = new_nonce

            status = poll_data.get("status", "pending")
            if status == "valid":
                logger.info("ACME challenge validated: %s", challenge_url)
                return True
            elif status == "invalid":
                error = poll_data.get("error", {})
                logger.error(
                    "ACME challenge failed: status=%s error=%s", status, error
                )
                return False
            # status is 'pending' or 'processing' — keep polling

        logger.error("ACME challenge validation timed out: %s", challenge_url)
        return False

    async def wait_for_authorization(self, authz_url: str) -> bool:
        """Wait until an authorization becomes valid or fails."""
        start = time.time()
        while time.time() - start < CHALLENGE_POLL_TIMEOUT:
            await asyncio.sleep(CHALLENGE_POLL_INTERVAL)
            resp = await self._http.get(authz_url)
            data = resp.json()
            new_nonce = resp.headers.get("Replay-Nonce")
            if new_nonce:
                self._nonce = new_nonce

            status = data.get("status", "pending")
            if status == "valid":
                return True
            elif status == "invalid":
                logger.error("Authorization invalid: %s", data)
                return False

        return False

    # ------------------------------------------------------------------
    # CSR generation & order finalization
    # ------------------------------------------------------------------
    def generate_csr(self, domains: list[str]) -> bytes:
        """Generate a Certificate Signing Request (CSR) in DER format.

        Args:
            domains: List of domain names (first is the common name).

        Returns:
            bytes: DER-encoded CSR.
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography library required for CSR generation")

        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domains[0])])
        )
        # Add Subject Alternative Names for all domains
        san = x509.SubjectAlternativeName(
            [x509.DNSName(d) for d in domains]
        )
        builder = builder.add_extension(san, critical=False)
        csr = builder.sign(self.account_key, hashes.SHA256(), default_backend())
        return csr.public_bytes(serialization.Encoding.DER)

    async def finalize_order(self, finalize_url: str, csr: bytes) -> str:
        """Finalize ACME order with CSR.

        Args:
            finalize_url: Finalize URL from the order.
            csr: Certificate Signing Request (DER format).

        Returns:
            str: Certificate URL.
        """
        payload = {"csr": _b64url(csr)}
        resp = await self._acme_post(finalize_url, payload, kid=self.account_url)
        data = resp.json()
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"ACME order finalization failed: {resp.status_code} {data}")

        cert_url = data.get("certificate", "")
        if not cert_url:
            # Poll the order until certificate URL appears
            order_url = resp.headers.get("Location", "")
            if order_url:
                for _ in range(MAX_RETRIES):
                    await asyncio.sleep(RETRY_BASE_DELAY)
                    poll = await self._http.get(order_url)
                    poll_data = poll.json()
                    new_nonce = poll.headers.get("Replay-Nonce")
                    if new_nonce:
                        self._nonce = new_nonce
                    cert_url = poll_data.get("certificate", "")
                    if cert_url:
                        break

        if not cert_url:
            raise RuntimeError("Certificate URL not found after finalization")

        logger.info("ACME order finalized, cert URL: %s", cert_url)
        return cert_url

    # ------------------------------------------------------------------
    # Certificate download
    # ------------------------------------------------------------------
    async def download_certificate(self, cert_url: str) -> Tuple[str, str, str]:
        """Download issued certificate.

        Args:
            cert_url: Certificate URL from finalized order.

        Returns:
            tuple: (certificate_pem, chain_pem, fullchain_pem)
        """
        resp = await self._http.get(cert_url, headers={"Accept": "application/pem-certificate-chain"})
        new_nonce = resp.headers.get("Replay-Nonce")
        if new_nonce:
            self._nonce = new_nonce

        if resp.status_code != 200:
            raise RuntimeError(f"Certificate download failed: {resp.status_code}")

        fullchain_pem = resp.text.strip()
        # Split the full chain into leaf cert and chain
        parts = fullchain_pem.split("-----END CERTIFICATE-----")
        cert_pem = parts[0].strip() + "\n-----END CERTIFICATE-----\n"
        chain_parts = [p.strip() for p in parts[1:] if p.strip()]
        chain_pem = "".join(p + "\n-----END CERTIFICATE-----\n" for p in chain_parts)
        logger.info("ACME certificate downloaded successfully")
        return cert_pem, chain_pem, fullchain_pem


class SSLCertificateService:
    """Service to manage SSL certificates via ACME."""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        use_staging = os.getenv("ACME_USE_STAGING", "true").lower() in ("true", "1", "yes")
        self.acme_client = ACMEClient(staging=use_staging)
        self._cert_storage_path = Path(os.getenv("SSL_CERT_STORAGE_PATH", "/tmp/ssl_certs"))

    async def _ensure_client(self) -> None:
        """Ensure ACME client is initialized and registered."""
        if not self.acme_client.directory:
            await self.acme_client.initialize()
        if not self.acme_client.account_url:
            await self.acme_client.register_account()

    async def issue_certificate(
        self, tenant_id: str, domain: str, challenge_type: str = "dns-01"
    ) -> Dict[str, Any]:
        """Issue SSL certificate for domain.

        Args:
            tenant_id: Tenant ID.
            domain: Domain name.
            challenge_type: Challenge type (dns-01 or http-01).

        Returns:
            dict: Certificate info including pem data and metadata.
        """
        logger.info("Issuing SSL certificate for %s (challenge: %s)", domain, challenge_type)
        await self._ensure_client()
        # Create order
        order_url, authorizations = await self.acme_client.create_order([domain])
        challenge_type = await self._validate_challenges(authorizations, domain, challenge_type)
        await self._wait_for_authorizations(authorizations, domain)
        cert_url = await self._finalize_order(order_url, domain)
        cert_pem, chain_pem, fullchain_pem, private_key_pem = await self._download_and_store_certificate(
            cert_url, tenant_id, domain
        )
        expires_at, issued_at = self._parse_certificate_expiry(cert_pem)
        result = {
            "domain": domain,
            "certificate": cert_pem,
            "chain": chain_pem,
            "fullchain": fullchain_pem,
            "private_key": private_key_pem,
            "expires_at": expires_at,
            "issued_at": issued_at,
        }
        logger.info("SSL certificate issued for %s (expires: %s)", domain, expires_at)
        return result

    async def _validate_challenges(
        self, authorizations: list, domain: str, challenge_type: str
    ) -> str:
        """Validate ACME challenges for each authorization."""
        for authz in authorizations:
            challenges = authz.get("challenges", [])
            target_challenge = None
            for ch in challenges:
                if ch.get("type") == challenge_type:
                    target_challenge = ch
                    break

            if not target_challenge:
                # Fallback to first available challenge
                target_challenge = challenges[0] if challenges else None
                if target_challenge:
                    challenge_type = target_challenge.get("type", challenge_type)
                    logger.warning(
                        "Requested challenge type not available, using %s",
                        challenge_type,
                    )

            if not target_challenge:
                raise RuntimeError(f"No challenges available for domain {domain}")

            token = target_challenge.get("token", "")
            # Output challenge details for the caller to set up DNS/HTTP
            if challenge_type == "dns-01":
                dns_value = self.acme_client.compute_dns01_record(token)
                logger.info(
                    "DNS-01 challenge: set TXT record _acme-challenge.%s = %s",
                    domain, dns_value,
                )
            elif challenge_type == "http-01":
                http_content = self.acme_client.compute_http01_content(token)
                logger.info(
                    "HTTP-01 challenge: serve at /.well-known/acme-challenge/%s",
                    token,
                )

            # Validate the challenge (caller should have set up DNS/HTTP before this)
            success = await self.acme_client.validate_challenge(
                target_challenge["url"]
            )
            if not success:
                raise RuntimeError(
                    f"Challenge validation failed for domain {domain}. "
                    f"Ensure DNS/HTTP challenge is properly configured."
                )
        return challenge_type

    async def _wait_for_authorizations(self, authorizations: list, domain: str) -> None:
        """Wait for all authorizations to complete."""
        for authz in authorizations:
            authz_url = authz.get("url", "")
            if authz_url:
                authz_valid = await self.acme_client.wait_for_authorization(authz_url)
                if not authz_valid:
                    raise RuntimeError(f"Authorization failed for domain {domain}")

    async def _finalize_order(self, order_url: str, domain: str) -> str:
        """Generate CSR and finalize the ACME order, returning the cert URL."""
        csr = self.acme_client.generate_csr([domain])
        finalize_url = order_url  # ACME provides finalize URL in order; construct from order
        # Fetch order to get finalize URL
        order_resp = await self.acme_client._http.get(order_url)
        order_data = order_resp.json()
        new_nonce = order_resp.headers.get("Replay-Nonce")
        if new_nonce:
            self.acme_client._nonce = new_nonce
        finalize_url = order_data.get("finalize", order_url + "/finalize")
        cert_url = await self.acme_client.finalize_order(finalize_url, csr)
        return cert_url

    async def _download_and_store_certificate(
        self, cert_url: str, tenant_id: str, domain: str
    ) -> tuple:
        """Download the issued certificate and persist it to disk."""
        cert_pem, chain_pem, fullchain_pem = await self.acme_client.download_certificate(cert_url)
        # Get private key PEM for renewal
        private_key_pem = self.acme_client.account_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode() if HAS_CRYPTOGRAPHY else ""
        self._save_certificate_files(tenant_id, domain, cert_pem, chain_pem, fullchain_pem, private_key_pem)
        return cert_pem, chain_pem, fullchain_pem, private_key_pem

    def _parse_certificate_expiry(self, cert_pem: str) -> tuple:
        """Parse certificate validity dates from the PEM."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=90)
        issued_at = datetime.now(timezone.utc)
        if HAS_CRYPTOGRAPHY:
            try:
                cert_obj = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                expires_at = cert_obj.not_valid_after_utc.replace(tzinfo=timezone.utc) if hasattr(cert_obj, 'not_valid_after_utc') else cert_obj.not_valid_after.replace(tzinfo=timezone.utc)
                issued_at = cert_obj.not_valid_before_utc.replace(tzinfo=timezone.utc) if hasattr(cert_obj, 'not_valid_before_utc') else cert_obj.not_valid_before.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning("Could not parse certificate expiry: %s", e)
        return expires_at, issued_at

    def _save_certificate_files(
        self,
        tenant_id: str,
        domain: str,
        cert_pem: str,
        chain_pem: str,
        fullchain_pem: str,
        private_key_pem: str,
    ) -> Path:
        """Save certificate files to disk for web server consumption."""
        cert_dir = self._cert_storage_path / tenant_id / domain
        cert_dir.mkdir(parents=True, exist_ok=True)
        (cert_dir / "cert.pem").write_text(cert_pem)
        (cert_dir / "chain.pem").write_text(chain_pem)
        (cert_dir / "fullchain.pem").write_text(fullchain_pem)
        if private_key_pem:
            (cert_dir / "privkey.pem").write_text(private_key_pem)

        logger.info("Certificate files saved to %s", cert_dir)
        return cert_dir

    async def renew_certificate(
        self, domain: str, certificate: str, private_key: str
    ) -> Dict[str, Any]:
        """Renew SSL certificate.

        Args:
            domain: Domain name.
            certificate: Current certificate PEM.
            private_key: Current private key PEM.

        Returns:
            dict: New certificate info.
        """
        logger.info("Renewing SSL certificate for %s", domain)
        # Renewal is essentially a new issuance with the same domain
        return await self.issue_certificate("renewal", domain)

    async def check_expiry(self, expires_at: datetime) -> Tuple[bool, int]:
        """Check if certificate is expiring soon.

        Args:
            expires_at: Certificate expiry datetime.

        Returns:
            tuple: (is_expiring, days_remaining)
        """
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        days_remaining = (expires_at - now).days
        is_expiring = days_remaining <= 30
        return is_expiring, days_remaining

    async def close(self) -> None:
        """Clean up resources."""
        await self.acme_client.close()


async def auto_renew_certificates():
    """Auto-renew certificates that are expiring soon.

    This function should be called by a cron job (e.g., daily).

    保持 async 签名以兼容调用方 await；DB 访问走同步 SessionLocal
    （项目未引入 asyncpg/aiosqlite，不存在可用的异步引擎）。
    """
    from sqlalchemy import update

    from app.db.session import SessionLocal
    from app.models.ssl_certificate import SSLCertificate
    logger.info("Starting auto-renewal check...")
    service = SSLCertificateService()
    db = SessionLocal()
    try:
        # Find certificates expiring within 30 days
        threshold = datetime.now(timezone.utc) + timedelta(days=30)
        certs = (
            db.query(SSLCertificate)
            .filter(
                SSLCertificate.auto_renew == "true",
                SSLCertificate.expires_at <= threshold,
            )
            .all()
        )
        for cert in certs:
            logger.info("Renewing certificate for %s...", cert.domain)
            try:
                new_cert = await service.renew_certificate(
                    cert.domain, cert.certificate, cert.private_key
                )
                # Save new cert files
                service._save_certificate_files(
                    str(cert.tenant_id),
                    cert.domain,
                    new_cert["certificate"],
                    new_cert["chain"],
                    new_cert["fullchain"],
                    new_cert.get("private_key", ""),
                )
                # Update certificate in DB
                db.execute(
                    update(SSLCertificate)
                    .where(SSLCertificate.id == cert.id)
                    .values(
                        certificate=new_cert["certificate"],
                        chain=new_cert["chain"],
                        expires_at=new_cert["expires_at"],
                        issued_at=new_cert["issued_at"],
                        last_renewal_attempt=datetime.now(timezone.utc),
                        renewal_error=None,
                    )
                )
                db.commit()
                logger.info("Certificate renewed for %s", cert.domain)

            except Exception as e:
                logger.error("Failed to renew certificate for %s: %s", cert.domain, e)
                db.execute(
                    update(SSLCertificate)
                    .where(SSLCertificate.id == cert.id)
                    .values(
                        last_renewal_attempt=datetime.now(timezone.utc),
                        renewal_error=str(e),
                    )
                )
                db.commit()
    finally:
        db.close()
        await service.close()

    logger.info("Auto-renewal check completed")
