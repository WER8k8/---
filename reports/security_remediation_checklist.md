# Security Remediation Checklist

## Status
- VS Code Copilot extension installed and verified.
- Strix system validated and scan results generated.
- Security audit reports saved under `reports/`.

## High-priority dependency fixes

### Backend Python (`backend/requirements.txt`)
- `starlette` is pinned to `>=1.0.1,<1.1` and is vulnerable.
  - Fix: upgrade to at least `1.3.1` (prefer `>=1.3.1,<2.0`).
- `cryptography 46.0.7` is vulnerable.
  - Fix: upgrade to `>=48.0.1`.
- `pytest 7.4.4` has a DoS issue in UNIX temporary directories.
  - Fix: upgrade to `>=9.0.3`.
- `protobuf 4.25.9` has a DoS vulnerability in `ParseDict()`.
  - Fix: upgrade to `>=5.29.6` or `>=6.33.5`.
- `ecdsa 0.19.2` has a timing attack vulnerability and currently has no planned fix.
  - Fix: replace or remove `python-ecdsa` usage if it is used for security-critical signing, or migrate to a maintained crypto implementation.

### Frontend / SEO Node workspaces

#### `frontend`
- `package.json` direct dependency:
  - `axios ^1.6.8` is currently resolving to `1.15.2` in `package-lock.json`.
    - Fix: upgrade to `^1.18.0` or later.
- Transitive vulnerabilities present in `package-lock.json`:
  - `@babel/plugin-transform-modules-systemjs 7.29.0` -> upgrade to `>=7.29.4`.
  - `brace-expansion 2.1.0`, `1.1.14`, `5.0.6`, `5.0.5` -> upgrade to `>=5.0.7`.
  - `form-data 4.0.5` -> upgrade to `>=4.0.6`.
  - `js-yaml 4.1.1` -> upgrade to `>=4.3.0`.
  - `shell-quote 1.8.3` -> upgrade to `>=1.8.5`.
  - `tar 7.5.13` -> upgrade to `>=7.5.19`.
  - `vite 7.3.2` -> upgrade to a safe version, e.g. `>=7.3.5` or `>=8.0.16` depending on compatibility.
  - `ws 8.20.0` -> upgrade to `>=8.21.0`.

#### `frontend/admin`
- `package.json` direct dependencies:
  - `axios ^1.6.8` -> upgrade to `^1.18.0` or later.
  - `vite ^5.2.8` -> upgrade to a safe version, e.g. `>=6.4.3` or `>=8.0.16`.
- Transitive vulnerabilities in `package-lock.json`:
  - `brace-expansion 2.1.0` and other nested versions -> upgrade via dependency updates.
  - `form-data 4.0.5` -> upgrade to `>=4.0.6`.
  - `js-yaml 4.1.1` -> upgrade to `>=4.3.0`.
  - `tar 7.5.15` -> upgrade to `>=7.5.19`.
  - `undici 7.25.0` -> upgrade to `>=7.28.0`.
  - `ws 8.20.1` -> upgrade to `>=8.21.0`.

#### `seo-admin`
- `package.json` direct dependencies:
  - `axios ^1.6.5` -> upgrade to `^1.18.0` or later.
  - `xlsx ^0.18.5` -> upgrade to `^0.20.2` or later.
  - `vite ^5.0.12` -> upgrade to a safe version, e.g. `>=6.4.3` or `>=8.0.16`.
- Transitive vulnerabilities in `package-lock.json`:
  - `form-data 4.0.5` -> `>=4.0.6`.
  - `js-yaml 4.1.1` -> `>=4.3.0`.
  - `tar 7.5.x` -> `>=7.5.19`.
  - `brace-expansion`, `shell-quote`, and `vite` are also flagged and should be updated via the dependency tree.

#### `seo-backend`
- `package.json` direct dependencies:
  - `axios ^1.6.2` -> upgrade to `^1.18.0` or later.
  - `xlsx ^0.18.5` -> upgrade to `^0.20.2` or later.
- Transitive vulnerabilities in `package-lock.json`:
  - `tar 7.5.13` -> `>=7.5.19`.
  - `tar-fs 3.0.4` -> `>=3.1.1`.
  - `tmp 0.0.33` -> `>=0.2.6`.
  - `undici 7.25.0` -> `>=7.28.0`.
  - `ws 8.16.0` -> `>=8.21.0`.
  - `form-data 4.0.5` -> `>=4.0.6`.
  - `js-yaml 4.1.1` -> `>=4.3.0`.

## Code-level security findings (Strix / Bandit / Ruff)

### Backend Python code
- `backend/app/services/site_audit.py`: `httpx` used with `verify=False` disables TLS certificate validation.
  - Fix: remove `verify=False` or replace with a trusted certificate bundle.
- Multiple files use weak hash algorithms (MD5, SHA1):
  - `backend/app/api/v1/routes/inquiries.py`
  - `backend/app/core/cache_decorator.py`
  - `backend/app/graduation/models.py`
  - `backend/app/services/cross_border/xfyun_lfasr_service.py`
  - `backend/app/services/logistics_provider.py`
  - `backend/app/services/media_cuplayer_service.py`
  - `backend/app/services/oauth_login.py`
  - `backend/app/services/payment_service.py`
  - `backend/app/services/platforms/baijiahao.py`
  - `backend/app/services/platforms/wechat.py`
  - `backend/app/services/talking_stick/file_lock.py`
  - `backend/app/services/ubrain/email_queue_service.py`
  - Fix: replace security-sensitive hashing with SHA-256/HMAC or use a secure key derivation function.
- Use of `shell=True` or shell-dependent subprocess execution is flagged in multiple backend adapters.
  - Fix: refactor to `subprocess.run([...], shell=False)` and sanitize arguments.
- `backend/alembic/versions/016_add_ai_config_tables.py`: `S608` / SQL injection risk from string-based query construction.
- `backend/app/api/v1/orders.py`: insecure random usage with non-cryptographic PRNG.
  - Fix: use the `secrets` module for security-sensitive tokens or nonces.
- Several hardcoded password-like values and token constants are flagged by Ruff.
  - Fix: move secrets into environment configuration and remove them from source control.
- Dozens of `try/except/pass` patterns were detected.
  - Fix: handle exceptions explicitly and log errors instead of silently swallowing them.

### Ruff summary
- Severe security lint counts: 297 total.
- Top codes:
  - `S110` (133) try/except/pass
  - `S101` (26) assert statements in production code
  - `S311` (25) insecure random generator usage
  - `S603` (25) unsafe subprocess use
  - `invalid-syntax` (22)
  - `S105` (12) likely hardcoded passwords
  - `S324` (12) insecure hashing
  - `S310` (11) insecure randomness
  - `S608` (8) SQL injection patterns
  - `S607` (4) insecure exception handling

## Recommended next steps
1. Update `backend/requirements.txt` to the patched Python package versions.
2. In each Node workspace (`frontend`, `frontend/admin`, `seo-admin`, `seo-backend`):
   - update direct dependencies shown above,
   - delete `package-lock.json` if necessary,
   - run `npm install`,
   - then run `npm audit` again.
3. Re-run Strix/Bandit/Ruff after dependency updates.
4. Review flagged backend files for hardcoded secrets, `verify=False`, weak hashes, shell execution, and exception swallowing.
5. Re-run `pip-audit` and `npm audit` after code and dependency fixes.

## Notes
- Reports are stored in `reports/`.
- The highest priority fixes are the backend Python package vulnerabilities and the critical npm transitive vulnerabilities for `tar`, `axios`, and `form-data`.
- `ecdsa 0.19.2` has no available fix; review its use carefully.
