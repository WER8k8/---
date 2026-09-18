# OpenCodeReview LLM 全量合并报告

> 多批次扫描合并 · 去重后意见 · 密钥未入库

- 工具：alibaba/open-code-review **v1.12.5**
- Provider/Model：['agnes'] / ['agnes-2.5-flash', 'agnes-3.0-flash']
- 批次数：7
- 意见：原始 251 → **去重 251**
- 级别：**critical 8** · high 60 · medium 87 · low 81 · unknown 15

## 各批次运行

| 文件 | 状态 | 评审文件数 | 意见数 | token | 超预算 |
|------|------|----------:|------:|------:|:------:|
| `ocr-scan-critical-full.json` | completed_with_errors | 76 | 86 | 835543 | True |
| `ocr-scan-batch2.json` | completed_with_errors | 17 | 66 | 565606 | True |
| `ocr-scan-batch3.json` | completed_with_errors | 13 | 17 | 700349 | True |
| `ocr-scan-batch4.json` | success | 2 | 12 | 38593 | None |
| `ocr-scan-batch5-payment.json` | success | 2 | 13 | 84731 | None |
| `ocr-scan-batch6-acq-rest.json` | success | 10 | 47 | 199919 | None |
| `ocr-scan-batch7-acq-route.json` | success | 1 | 10 | 170400 | None |

## 按文件（去重后 Top）

| 文件 | 意见数 |
|------|------:|
| `backend/app/services/acquisition/experience_feed.py` | 17 |
| `backend/app/api/v1/routes/acquisition.py` | 15 |
| `backend/app/services/oauth_login.py` | 12 |
| `backend/app/api/v1/routes/tenants.py` | 10 |
| `backend/app/services/acquisition/nps_rescue.py` | 10 |
| `backend/app/services/acquisition/ops_card_pg.py` | 10 |
| `backend/app/api/v1/routes/payment.py` | 9 |
| `backend/app/core/config.py` | 9 |
| `backend/app/api/v1/routes/auth.py` | 8 |
| `backend/app/core/login_bruteforce.py` | 8 |
| `backend/app/services/acquisition/__init__.py` | 8 |
| `backend/app/services/acquisition/suppression_list.py` | 8 |
| `backend/app/services/adapters/tradeai/__init__.py` | 8 |
| `backend/app/services/hermes/harness_gateway.py` | 8 |
| `backend/app/services/acquisition/dispatch_service.py` | 7 |
| `backend/app/services/hermes/task_control_supervisor.py` | 7 |
| `backend/app/services/payment_pkg/payment_service_impl.py` | 7 |
| `backend/app/core/admin_auth.py` | 6 |
| `backend/app/core/database.py` | 6 |
| `backend/app/services/payment_service.py` | 6 |
| `backend/app/services/acquisition/onboarding.py` | 6 |
| `backend/app/services/acquisition/tender_engine.py` | 6 |
| `backend/app/services/acquisition/baseline_bench.py` | 5 |
| `backend/app/services/acquisition/billing_explain.py` | 5 |
| `backend/app/services/acquisition/growth_ops.py` | 5 |
| `backend/app/services/acquisition/knowledge_queue.py` | 5 |
| `backend/app/services/acquisition/payment_risk.py` | 5 |
| `backend/app/services/goodjob/customer_pool_projection.py` | 5 |
| `backend/app/services/acquisition/intent_classifier.py` | 5 |
| `backend/app/services/acquisition/fulfillment_nodes.py` | 4 |

## 按类别

| 类别 | 数量 |
|------|-----:|
| bug | 89 |
| maintainability | 58 |
| security | 47 |
| other | 21 |
| performance | 17 |
| documentation | 9 |
| unknown | 6 |
| style | 3 |
| test | 1 |

## 仍未完整扫完（诚实）

- backend/app/services/acquisition/onboarding.py · token_budget_reached · stopped in batch #0: used 789196 tokens + next-file estimate exceeds budget 800000
- backend/app/services/acquisition/loss_report.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/services/acquisition/nps_rescue.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/api/v1/routes/acquisition.py · scan_subtask_error · LLM completion error: context deadline exceeded
- backend/app/services/payment_pkg/payment_service_impl.py · token_budget_reached · stopped in batch #0: used 480799 tokens + next-file estimate exceeds budget 500000
- backend/app/services/oauth_login.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/services/hermes/harness_gateway.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/services/acquisition/experience_feed.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/services/acquisition/payment_risk.py · token_budget_reached · stopped in batch #0: used 616193 tokens + next-file estimate exceeds budget 600000
- backend/app/services/acquisition/onboarding.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/services/acquisition/ops_card_pg.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- backend/app/api/v1/routes/acquisition.py · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing

## Critical 全文

### `backend/app/api/v1/routes/auth.py`:101-104 · security

Line 101: `except (ConnectionError, TimeoutError, Exception)` — catching bare `Exception` here is problematic. It will also catch `HTTPException` raised by the `raise HTTPException(429, ...)` on line 99 if Redis returns count > limit, causing the rate limit to silently fail open (allowing the request through). The rate limit check should happen BEFORE the except block, or the except clause should be narrowed to only the Redis operations. As written, if `incr()` returns a count > 3, the exception is caught and the code falls through to the unguarded in-memory path which then crashes on `count` being undefined.

```python
        except (ConnectionError, TimeoutError, Exception):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Redis 限流故障，降级到内存计数: %s", email)
```

### `backend/app/api/v1/routes/auth.py`:106-110 · bug

Undefined variable `count` in rate-limit fallback path causes UnboundLocalError on every non-Redis request. When Redis is unavailable or fails, the code falls through to lines 106-110 which reference `count` (defined only inside the `if _use_redis_rate_limit:` block at line 95). This makes the email code sending endpoint crash with a 500 error whenever Redis is not configured or fails. Fix: use a local variable like `email_count = len(_email_code_store[email])` for the in-memory check.

```python
    now = time.time()
    window = _email_code_store[email]
    _email_code_store[email] = [t for t in window if now - t < _EMAIL_CODE_WINDOW]
    if count > _EMAIL_CODE_LIMIT:
        raise HTTPException(429, "验证码发送过于频繁，请 1 小时后再试")
```

### `backend/app/api/v1/routes/auth.py`:106-111 · bug

In `_check_email_code_rate`, when Redis is unavailable and the fallback path executes, the `count` variable from line 95 is out of scope, causing an UnboundLocalError. Additionally, the in-memory path only checks the count after filtering the window but uses `count` (undefined) instead of the length of the filtered list. This means email code sending always fails with a 500 error in non-Redis environments.

```python
    now = time.time()
    window = _email_code_store[email]
    _email_code_store[email] = [t for t in window if now - t < _EMAIL_CODE_WINDOW]
    if count > _EMAIL_CODE_LIMIT:
        raise HTTPException(429, "验证码发送过于频繁，请 1 小时后再试")
    _email_code_store[email].append(now)
```

### `backend/app/api/v1/routes/payment.py`:537-548 · security

BUG-06 Stripe checkout.session.completed is accepted without verifying the session's actual payment status. The webhook handler trusts `event.get('data', {})` to contain a dict, but never inspects `session.get('payment_status')` or `session.get('status')`. A Stripe session can complete in states other than paid (e.g. `payment_pending`, `complete` with no charge captured). Processing such an event will call `_mark_paid_and_provision`, mark the order as paid, and provision credits even though payment was never collected. Fix: assert `session.get('payment_status') == 'paid'` (or equivalently `session.get('status') == 'complete'` with verified charge) before provisioning. Add an explicit comment that this guard matches Stripe's idempotency policy.

```python
        if event_type != 'checkout.session.completed':
            # 非支付完成事件（如 checkout.session.expired）确认收到即可
            return success_response(data={'ignored': True, 'event_type': event_type}, message='Webhook 处理成功')

        session = event.get('data') or {}
        if not isinstance(session, dict):
            return error_response(400, '事件数据格式异常')
        metadata = session.get('metadata') or {}
        order_no = (metadata.get('order_no') if isinstance(metadata, dict) else None) or ''
        if not order_no:
            log.error('[Payment] Stripe Webhook 缺少 metadata.order_no，无法对账 event=%s', event_id)
            return error_response(400, 'missing metadata.order_no')
```

### `backend/app/api/v1/routes/payment.py`:611-626 · security

The balance payment code calls `pay_order_with_balance` then `_mark_paid_and_provision` sequentially. If `_mark_paid_and_provision` raises (or the compensation path `_refund_balance_after_failed_pay` raises), the wallet may have already been debited without crediting the user. Wrap the compound sequence in a single database/workflow transaction where possible, or ensure the compensation function is idempotent and logged with sufficient context to allow manual recovery.

```python
        result = pay_order_with_balance(user_id=str(current_user.id), order_id=str(order.id), amount=amount, currency=getattr(order, 'currency', 'CNY'), tenant_id=str(order.tenant_id))
        if not result or not getattr(result, 'success', False):
            return error_response(400, (getattr(result, 'error', None) if result else None) or '余额支付失败')
        # 复用回调一致的发放链路：原子置 paid + 收入 + 权益
        try:
            from app.services.payment_pkg.payment_service_impl import PaymentService
            svc = PaymentService(db)
            paid = svc._mark_paid_and_provision(order.order_no)
            if not paid:
                # 并发下已被其它请求支付：补偿退回刚扣的余额
                _refund_balance_after_failed_pay(current_user, amount, order)
                return error_response(409, '订单已被支付，余额已退回')
        except Exception:
            log.exception('[Payment] 余额支付后发放权益失败，补偿退回余额: order=%s', order_no)
            _refund_balance_after_failed_pay(current_user, amount, order)
            return error_response(500, '权益发放失败，余额已退回，请稍后重试')
```

### `backend/app/core/admin_auth.py`:202-206 · security

Security: jwt.decode is called with verify_exp=False, which means revoked sessions using expired tokens will bypass the blacklist check. If a token is leaked and then the user logs out (revoking the session), an attacker can continue using the expired token indefinitely since the expiry check is disabled. The comment '防止 token 泄露后被吊销的会话仍可使用' contradicts this - it claims to prevent leaked tokens from being used, but verify_exp=False actually enables exactly that for expired tokens. Either remove verify_exp=False and handle expired token cases differently, or document why this is intentional and accept the security trade-off.

```python
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
```

### `backend/app/services/oauth_login.py`:0-0 · security

The comment references lines 393-402 but verify_wechat_signature is actually around line 387-396. The actual issue is correct - using FEISHU_VERIFICATION_TOKEN for WeChat signature verification. This is a critical bug that causes the function to always fail or verify with the wrong credential.

```python
def verify_wechat_signature(signature: str, timestamp: str, nonce: str) -> bool:
    token = settings.FEISHU_VERIFICATION_TOKEN.strip()
```

### `backend/app/services/oauth_login.py`:667-675 · security

verify_wechat_signature reads settings.FEISHU_VERIFICATION_TOKEN instead of a WeChat-specific signature token. This means the function will either always return False (wrong token) or use the wrong credential entirely. For Feishu events, a separate function should use FEISHU_VERIFICATION_TOKEN. For WeChat, the wechat signature uses a different algorithm (simple sort-and-sha1) but still requires a WeChat-configured token, not Feishu's.

```python
def verify_wechat_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """验证微信服务器推送的签名（用于事件回调）。"""
    token = settings.FEISHU_VERIFICATION_TOKEN.strip()
    if not token:
        return False

    parts = sorted([token, timestamp, nonce])
    expected = hashlib.sha1("".join(parts).encode("utf-8")).hexdigest()
    return signature == expected
```


## High 全文

### `backend/app/api/v1/routes/acquisition.py`:620-623 · bug

NONE SAFETY: `_ops_card_payload` is called after operations that might return None (e.g., `ops_card_store.update_sample`, `ops_card_store.record_touch`). If these return None, calling `.to_dict()`, `.summary_lines()`, etc. will raise AttributeError.

```python
card = ops_card_store.update_sample(inquiry_id, **kwargs)
    out = _ops_card_payload(card)
    out["sample"] = sample_view(card.sample)
    return out
```

### `backend/app/api/v1/routes/acquisition.py`:1218-1233 · bug

Unreachable logic due to duplicate route registration and silent error swallowing: `@router.get("/ops/reconcile")` is defined twice. The first definition (lines 1218-1233) includes a `get_read_session` fallback but is overridden by the second definition (line 1286), making the first one dead code. Furthermore, inside the code, the `except Exception: pass` silently swallows errors from the read-session attempt and falls through to calling `billing_reconcile` with `session=None`, causing opaque failures. Remove the duplicate or merge the fallback logic, and ensure errors are logged or handled explicitly.

```python
@router.get("/ops/reconcile")
def acquisition_billing_reconcile(
    tenant_id: str = "demo",
    window_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-5 meter vs ledger 对账（只读）。优先只读会话。"""
    session = _resolve_db(db)
    if session is None:
        try:
            with get_read_session() as rs:
                return billing_reconcile(rs, tenant_id=tenant_id, window_hours=window_hours)
        except Exception:
            pass
    return billing_reconcile(session, tenant_id=tenant_id, window_hours=window_hours)
```

### `backend/app/api/v1/routes/acquisition.py`:1218-1233 · bug

CRITICAL: Duplicate route definition for `/ops/reconcile`. Lines 1218-1233 and 1286-1294 both define the same GET endpoint. FastAPI will register the second one, making the first one unreachable. This creates inconsistent behavior: the first version uses read-session fallback logic, while the second directly calls billing_reconcile without fallback.

```python
@router.get("/ops/reconcile")
def acquisition_billing_reconcile(
    tenant_id: str = "demo",
    window_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-5 meter vs ledger 对账（只读）。优先只读会话。"""
    session = _resolve_db(db)
    if session is None:
        try:
            with get_read_session() as rs:
                return billing_reconcile(rs, tenant_id=tenant_id, window_hours=window_hours)
        except Exception:
            pass
    return billing_reconcile(session, tenant_id=tenant_id, window_hours=window_hours)
```

### `backend/app/api/v1/routes/acquisition.py`:1472-1479 · security

MISSING TENANT ISOLATION: Multiple endpoints accept `tenant_id` from request body or query params without validating it belongs to the current user. For example, `/reply-ingest`, `/dispatch`, `/buyers/upsert`, `/suppression/add` all trust user-supplied tenant_id. An authenticated user could potentially access or modify another tenant's data.

```python
@router.post("/reply-ingest")
def reply_ingest(
    body: ReplyIngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """客户回复进线（E-3：限流）。"""
    _rate_limit_or_raise(body.tenant_id or "demo", action="reply_ingest")
```

### `backend/app/api/v1/routes/auth.py`:351-366 · security

Race condition in email verification: the check-then-act pattern between querying for an unused verification code (with `.first()`) and then setting `verification.used = True` is not atomic across concurrent requests. Two simultaneous login attempts with the same valid code could both pass the query, and both would succeed in logging in. While `.with_for_update()` is present (line 304), this requires database-level row locking support (e.g., PostgreSQL with transaction isolation). With SQLite or misconfigured transactions, this race persists. Consider using an atomic UPDATE ... RETURNING or SELECT ... FOR UPDATE with proper transaction semantics.

```python
    verification = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == request.email,
            EmailVerification.code == input_code_hash,
            EmailVerification.used == False,
            EmailVerification.expires_at > datetime.now(timezone.utc),
        )
        .with_for_update()
        .first()
    )
    if not verification:
        return error_response(401, "验证码无效或已过期")

    verification.used = True
    db.commit()
```

### `backend/app/api/v1/routes/auth.py`:570-580 · security

Dev auto-bind bypasses authentication controls by allowing any `dev_`-prefixed OAuth identity to directly bind to the admin account without any password verification or 2FA. If `OAUTH_DEV_BYPASS=True` leaks into production (or if `is_production` incorrectly reports False), this creates an unrestricted privileged access path. The check at line 575 (`not settings.is_production`) is the only defense, but `is_production` is an application-level setting that can be misconfigured. Consider adding a separate, explicit feature flag that is harder to accidentally enable in production, and logging an alert when dev auto-bind is triggered.

```python
    admin_link = db.query(User).filter(User.username == "admin").first()
    if (
        admin_link
        and admin_link.is_active
        and provider_id.startswith("dev_")
        and not settings.is_production
        and (
            settings.OAUTH_DEV_BYPASS
            or settings.ENVIRONMENT == "development"
        )
    ):
```

### `backend/app/api/v1/routes/payment.py`:561-563 · security

The Stripe webhook handler wraps the entire request body, signature verification, dedup, dispatch, and provisioning in a single broad `try / except Exception as e` returning 500. Stripe will retry any 5xx response aggressively. Signature failures should return 403, missing metadata should return 400, and known-ignored events should return 200 — none of these currently do. This turns every malformed/stale webhook delivery into a retry storm that also inflates error monitoring alerts. Fix: narrow the catch to unexpected internal errors only, and return explicit 2xx/4xx codes for expected cases before entering the try block (or restructure with early returns). Log errors instead of swallowing them inside the generic handler.

```python
    except Exception as e:
        log.exception('[Payment] Stripe Webhook 处理失败: %s', e)
        return error_response(500, f'Webhook 处理失败: {e}')
```

### `backend/app/api/v1/routes/tenants.py`:33-37 · security

The module-level `_register_rate` dict is mutated without any lock or synchronization. In multi-worker (gunicorn) or threaded deployments, concurrent registration requests from the same IP will race on the read-modify-write sequence (lines 33-37), causing the rate limit to be ineffective — multiple registrations can slip through the check before either worker appends its timestamp. Fix: move rate-limit state into Redis or use a process-safe lock (e.g., `threading.Lock`) if single-process is guaranteed.

```python
now = time.time()
    _register_rate[ip] = [t for t in _register_rate[ip] if now - t < _REGISTER_WINDOW]
    if len(_register_rate[ip]) >= _REGISTER_LIMIT:
        raise HTTPException(429, "注册过于频繁，请 1 小时后再试")
    _register_rate[ip].append(now)
```

### `backend/app/api/v1/routes/tenants.py`:285-287 · security

The `update_current_tenant_settings` endpoint (line 285) accepts `body.settings` and merges it directly into the tenant's JSON settings blob via `existing.update(parsed)`. There is no schema validation on the contents of `parsed` — a malicious or erroneous client can write arbitrary keys into the settings dict, potentially overwriting critical fields like `brand`, `onboarding`, or `white_label`. The endpoint should validate that only known-permitted keys are merged, or at minimum deeply-validate the incoming structure before mutating the tenant record.

```python
parsed = json.loads(body.settings) if isinstance(body.settings, str) else body.settings
        existing = _safe_json_loads(tenant.settings)
        existing.update(parsed)
```

### `backend/app/api/v1/routes/tenants.py`:1065-1066 · security

In `get_tenant_domains` (line 1066) and `add_tenant_domain` (line 1090), when the current user has no active `UserTenant` link (`ut` is None), the code falls back to `db.query(Tenant).first()` — returning the first tenant in the database regardless of which user is logged in. This is an authorization bypass: any authenticated user without an active tenant association can read or modify the domain list of an arbitrary tenant (the first one in DB order). Fix: return 403 when `ut` is None rather than falling back to an arbitrary tenant.

```python
ut = db.query(UserTenant).filter(UserTenant.user_id == current_user.id, UserTenant.is_active.is_(True)).first()
    tenant = db.query(Tenant).filter(Tenant.id == ut.tenant_id).first() if ut else db.query(Tenant).first()
```

### `backend/app/api/v1/routes/tenants.py`:1346-1347 · bug

In `_create_register_entities` (lines 1346-1347), the tenant domain is generated using Python string `.replace()` with raw regex patterns instead of `re.sub()`:

    tenant_domain = body.company_name.lower().replace(r"\s+", "-").replace(r"[^a-z0-9-]", "")

The `.replace()` calls treat the pattern strings as literal text, so `r"\s+"` is replaced literally (not whitespace), and `r"[^a-z0-9-]"` is also a literal string. This means non-alphanumeric characters are never actually stripped — e.g., a company name like `My Company!` would produce `my-company!` instead of `my-company`. Fix: use `re.sub(r"\s+", "-", ...)` and `re.sub(r"[^a-z0-9-]", "", ...)`. Additionally, this means duplicate domain collisions are possible since two companies with similar names could produce identical slugs.

```python
tenant_domain = body.company_name.lower().replace(
        r"\s+", "-").replace(r"[^a-z0-9-]", "")[:50]
```

### `backend/app/api/v1/routes/tenants.py`:1528-1531 · bug

In `register_tenant` (lines 1528-1531), entities are created with `db.flush()` inside `_create_register_entities` but only committed after `_apply_register_extras` completes. If `_apply_register_extras` raises an exception (e.g., from `bind_guest_media_to_tenant`, `ReferralService.apply_referral`, or `provision_tenant_onboarding`), the partially-written rows (user, tenant, subscription, user_tenant) remain in the database as orphaned records because there is no rollback. Fix: wrap the entire creation sequence in a try/except with `db.rollback()` on failure, or use a transaction block.

```python
now = datetime.now(timezone.utc)
    user, tenant, trial_end = _create_register_entities(db, body, plan, now)
    guest_bound, onboarding = _apply_register_extras(db, body, tenant, user, plan, trial_end, verification)
    db.commit()
```

### `backend/app/core/admin_auth.py`:208-209 · security

Error handling: The bare except in _get_token_jti swallows ALL exceptions including JWTDecodeError, InvalidTokenError, and other authentication-related errors. This makes it impossible to distinguish between a valid token without JTI, a malformed token, a signature verification failure, or a Redis unavailability issue. During security incidents, this obscurity prevents effective investigation. At minimum, catch specific JWT exceptions and log them. Consider whether unauthorized tokens should be treated differently than tokens without JTI.

```python
    except Exception:
        return None
```

### `backend/app/core/database.py`:113-113 · security

Bare except clause swallows KeyboardInterrupt and SystemExit, preventing proper shutdown signals from reaching the application. This makes it impossible to stop the service cleanly. Should catch Exception at minimum and re-raise system exceptions.

```python
except Exception as e:
```

### `backend/app/core/database.py`:126-128 · bug

rebind_engine() recreates the main engine but leaves read_engine stale. After rebind, any sessions using RoutingSession will reference the old read_engine for read operations, breaking the read-write split. Should also update read_engine when rebind is called.

```python
def rebind_engine(database_url: str | None = None) -> None:
    """按新 URL 重建 engine/SessionLocal（预检、脚本切换 SQLite/Postgres 用）。"""
    global engine, SessionLocal, UUID_TYPE
```

### `backend/app/core/database.py`:184-185 · bug

Logger is used before it's defined in mount_rls_pilot_if_enabled(). The function references logger on line 189 but logger is only defined on line 191. This will cause NameError at runtime when the function is called.

```python
def mount_rls_pilot_if_enabled() -> None:
    """按配置门控挂载 RLS 试点表（默认关，生产零回归）。
```

### `backend/app/core/login_bruteforce.py`:0-0 · bug

`_redis_check` uses `time.time()` while `_memory_check` uses `_now_mono()` (which is `time.monotonic()`). This means Redis and in-memory stores have inconsistent lock semantics: a lock acquired in memory at monotonic time T+100 will expire at T+100+LOCK_SECONDS, but the same lock stored in Redis at wall-clock time W+100 expires at W+100+LOCK_SECONDS. If the system clock is adjusted (NTP sync, manual change), Redis locks can expire early or late relative to memory locks, defeating the anti-bruteforce guarantee during fallback transitions. Both paths should use the same time source. Since the Lua script already receives `ARGV[1]` as `now`, unify by passing `time.monotonic()` everywhere and using it consistently in Redis as well.

```python
def _redis_check(r: Any, client_ip: str,
                 username_or_email: str) -> Optional[Tuple[int, str]]:
    now = time.time()
    ik = _identity_key(client_ip, username_or_email)
```

### `backend/app/core/login_bruteforce.py`:120-127 · security

Bare `except Exception` in `_redis_client()` is far too broad. It catches `KeyboardInterrupt` via `Exception` is actually fine (KiB is not a subclass of Exception), but it still swallows import failures, config errors, and unexpected library bugs that should surface. More critically, the comment says '导入失败极少' but any exception here returns None, silently forcing the entire login brute-force protection into memory-only mode across all requests until the module is restarted or the issue is resolved. Use a narrower exception type or let it propagate so the service operator notices the Redis outage.

```python
    try:
        from app.core.refresh_token_blacklist import \
            get_refresh_blacklist_redis

        return get_refresh_blacklist_redis()
    except Exception as exc:  # pragma: no cover - 导入失败极少
        log.warning("login_bruteforce: 无法获取 Redis 客户端: %s", exc)
        return None
```

### `backend/app/core/login_bruteforce.py`:160-160 · bug

`_redis_record_failure` also mixes `time.time()` with the Lua script while `_memory_record_failure` uses `time.monotonic()`. This same inconsistency means identity locks recorded via Redis and via memory will expire at different real-world moments. Fix by using `_now_mono()` (i.e., `time.monotonic()`) in `_redis_record_failure` and `_redis_check`.

```python
-    now = time.time()
```

### `backend/app/core/login_bruteforce.py`:372-375 · security

`client_ip_from_request` returns the first IP from X-Forwarded-For without validating that it is a legitimate IP address. An attacker can send `X-Forwarded-For: 8.8.8.8, 127.0.0.1` and if the direct connection comes from a trusted proxy, the function returns `8.8.8.8` as the client IP. This bypasses IP-based rate limiting because the attacker's real IP is never stored. Add validation: parse the extracted IP with `ipaddress.ip_address()` and reject malformed entries, or at minimum verify the extracted IP is not a private/reserved address when claiming it came from a real client.

```python
    if _is_trusted_proxy(direct_ip):
        fwd = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
        if fwd:
            return fwd.split(",")[0].strip()
```

### `backend/app/services/acquisition/__init__.py`:912-916 · bug

The bare `except Exception: pass` on lines 912-916 silently swallows any import failure from the persistence patch. This means if `ops_card_pg` is missing, misconfigured, or raises any exception during initialization, the system will continue running without the Postgres backend — but the developer has no visibility into this. At minimum, log the exception. Also, this swallows exceptions during module import time, which could hide critical setup errors.

```python
try:
    from app.services.acquisition.ops_card_pg import patch_store_persistence
    patch_store_persistence(ops_card_store)
except Exception:
    pass
```

### `backend/app/services/acquisition/baseline_bench.py`:36-37 · bug

The bare `except Exception` at lines 32-34 and 42-44 silently swallows errors without logging or preserving the original traceback. This makes it impossible to diagnose why baseline operations failed. Consider using `except Exception as e:` and logging the exception, or re-raising with `raise ... from e` to preserve context.

```python
        except Exception:
            errors += 1
```

### `backend/app/services/acquisition/billing_explain.py`:119-125 · security

The acquisition events query filters by task_type pattern but does NOT filter by tenant_id/tid. This means it returns acquisition events from ALL tenants, not just the requested tenant. This is a security and correctness issue - users could see other tenants' acquisition activity. Fix: add `.filter(EvolutionTaskRecord.tenant_id == tid)` to the query on line 102.

```python
        acq = (
            session.query(EvolutionTaskRecord)
            .filter(EvolutionTaskRecord.task_type.like("acquisition.%"))
            .order_by(EvolutionTaskRecord.created_at.desc())
            .limit(limit)
            .all()
        )
```

### `backend/app/services/acquisition/dispatch_service.py`:41-47 · security

The except block on lines 36-41 silently swallows ALL exceptions from resolve_tenant_uuid without logging, making it impossible to diagnose tenant resolution failures. This could hide critical security issues like invalid tenant IDs being accepted. Consider logging the exception at least at DEBUG level, or re-raising with context if the failure is unrecoverable.

```python
        try:
            from app.services.acquisition.repo import resolve_tenant_uuid
            tid = resolve_tenant_uuid(session, tenant_id)
            if tid:
                resolved_tenant = tid
        except Exception:
            pass
```

### `backend/app/services/acquisition/dispatch_service.py`:95-96 · bug

Line 95: `node_tasks[0]` indexing will raise IndexError if `parse_graph_to_tasks` returns an empty list. The conditional only guards `getattr` but doesn't check if node_tasks is non-empty before indexing.

```python
        node_tasks = parse_graph_to_tasks(session, resolved_tenant, graph)
        plan_task_id = str(getattr(node_tasks[0], "parent_task_id", "")) if node_tasks else ""
```

### `backend/app/services/acquisition/experience_feed.py`:55-59 · bug

Lines 55 and 75: Both `except Exception` blocks use `# noqa: BLE001` to suppress the bare-except linting warning. While catching `Exception` (not bare `except:`) is better than swallowing `KeyboardInterrupt` and `SystemExit`, these are very broad catches. The first block (line 55) catches any exception from `EvolutionEngine` instantiation or `record_task_execution` call — including programming errors, import failures, etc. — and silently falls through to the fallback. If the fallback also fails, the original exception from the primary path is lost (only `exc2` is logged on line 76). Consider logging the primary exception at a higher level or including it in the returned reason for better observability.

```python
    except Exception as exc:  # noqa: BLE001
        logger.debug("EvolutionEngine 写入失败，尝试 terminal_hook: %s", exc)

    # 2) terminal_hook
    try:
```

### `backend/app/services/acquisition/experience_feed.py`:55-77 · bug

Lines 34-56 and 59-77: The fallback chain silently discards the primary exception. If `EvolutionEngine` raises an exception (e.g., database constraint violation, connection error), it is logged at DEBUG level and the code falls through to `terminal_hook`. If `terminal_hook` also fails, only `exc2` is captured in the returned reason — the original `Exc` is completely lost. This makes debugging production failures nearly impossible when both paths fail. At minimum, log both exceptions at WARNING or ERROR level, and include the primary exception in the returned reason dict so operators can see the full failure chain.

```python
    except Exception as exc:  # noqa: BLE001
        logger.debug("EvolutionEngine 写入失败，尝试 terminal_hook: %s", exc)

    # 2) terminal_hook
    try:
        from app.services.trace.terminal_hook import record_terminal_state
        out = record_terminal_state(
            db,
            task_type=task_type,
            executor_type="workflow",
            executor_id=executor_id,
            success=success,
            tenant_id=tenant_id or None,
            duration_ms=duration_ms,
            input_summary=inquiry_id,
            output_summary=detail[:500],
            metadata={"event": event},
        )
        return {"recorded": True, "engine": "terminal_hook", "id": out.get("record_id") if isinstance(out, dict) else None,
                "task_type": task_type}
    except Exception as exc2:  # noqa: BLE001
        logger.warning("经验写入全部失败 event=%s: %s", event, exc2)
        return {"recorded": False, "reason": str(exc2)[:200], "task_type": task_type}
```

### `backend/app/services/acquisition/fulfillment_nodes.py`:68-69 · bug

When deposit is paid, the code unconditionally overwrites status to "done", even if the deposit node was already marked "overdue". This loses overdue information and will suppress overdue reminders. Fix: skip the payment-led update when status is "overdue" or "skipped", e.g. `if status not in ("done", "skipped", "overdue"):`.

```python
            elif key == "deposit" and deposit_paid:
                status = "done" if not status or status in ("pending", "active") else status
```

### `backend/app/services/acquisition/growth_ops.py`:173-174 · other

Module-level mutable singletons (content_attr_store and ip_slot_catalog) have no thread safety. Concurrent requests from different tenants can interleave mutations on shared dicts/lists, causing data corruption or inconsistent reads. No locks are used around dict operations or list iterations.

```python
content_attr_store = ContentAttributionStore()
ip_slot_catalog = IpSlotCatalog()
```

### `backend/app/services/acquisition/knowledge_queue.py`:180-180 · security

The `tenant_id` parameter in `list()` and `report()` is unused. The method signatures imply multi-tenancy support, but there is no filtering or isolation by tenant. If this is intended to support multiple tenants, the implementation is incomplete and leaks state. If not, the parameter should be removed to avoid misleading API contracts.

```python
def list(self, *, tenant_id: str = "", category: str = "", only_pending: bool = False) -> list[dict[str, Any]]:
```

### `backend/app/services/acquisition/knowledge_queue.py`:211-212 · security

The `report()` method returns all items via `self.list(tenant_id=tenant_id)` which ignores the `tenant_id` parameter. If multi-tenancy is intended, this is a data leak. If not, the parameter should be removed.

```python
def report(self, *, tenant_id: str = "") -> dict[str, Any]:
        items = self.list(tenant_id=tenant_id)
```

### `backend/app/services/acquisition/knowledge_queue.py`:237-237 · other

The module-level singleton `knowledge_queue_store` holds mutable state (the `_items` dict). In a multi-tenant, multi-threaded environment (common for SaaS applications), concurrent calls to `mark_done`, `mark_pending`, or `list` can cause race conditions. The check-then-act pattern in `mark_done` (reading `it.done`, then setting it) is not atomic. Use a lock or thread-safe data structure to protect shared state.

```python
knowledge_queue_store = KnowledgeQueueStore()
```

### `backend/app/services/acquisition/loss_report.py`:26-27 · bug

Inquiry-level substring match in _normalize_reason is too broad. Any reason containing '无回复' (e.g. '客户说无回复意向', '暂无回复计划') is collapsed into the canonical '无回复' bucket, distorting both counts and hints. If the intent is to normalize only exact known values, use an exact equality check. If substring matching is intentional, document that behavior explicitly and consider whether it leads to misleading reports.

```python
    if "无回复" in r or r == "原因未知":
        return "无回复"
```

### `backend/app/services/acquisition/nps_rescue.py`:41-41 · bug

Bug: the `or` in `getattr(c, "stage", "") == "won" or getattr(c, "won_at", "")` is not parenthesized, so the whole `sum(1 for ...)` expression actually becomes:

    (sum(1 for c in cards if getattr(c, "stage", "") == "won")) or getattr(c, "won_at", "")

i.e. Python's generator is consumed first, then the result is `or`-ed with the *last* iteration's `won_at` attribute. This means `won_n` will hold the `won_at` string of the final card instead of the count when the count is 0. The intended semantics is almost certainly that a card counts as "won" if either field is truthy:

    won_n = sum(1 for c in cards if getattr(c, "stage", "") == "won" or bool(getattr(c, "won_at", "")))

```python
            won_n = sum(1 for c in cards if getattr(c, "stage", "") == "won" or getattr(c, "won_at", ""))
```

### `backend/app/services/acquisition/nps_rescue.py`:45-47 · bug

The won_n count logic uses `or` which means a card with both stage=='won' AND won_at truthy will still only be counted once (correct). However, the condition `getattr(c, 'stage', '') == 'won' or getattr(c, 'won_at', '')` could double-count if there's a bug in data where both are present but distinct. More importantly, the won_n value from ops_store can be overridden by win_loss_view data (line 46-47: `won_n = won_n or int(...)`), which means if ops_store has valid won_n > 0, the win_loss_view count is ignored entirely. This is potentially surprising behavior.

```python
    if win_loss_view:
        won_n = won_n or int(win_loss_view.get("won_count") or 0)
        lost_n = lost_n or int(win_loss_view.get("lost_count") or 0)
```

### `backend/app/services/acquisition/nps_rescue.py`:79-79 · security

Bug: when `nps_score` is a negative number (e.g. -3, which a caller could pass in despite the `Optional[int]` type hint), `s = max(0, min(10, int(nps_score)))` coerces it to 0, which is then misinterpreted as a collected NPS score of 0 (detractor bucket). The code's own docstring principle is "无数据不编 NPS 分数" — clamping negative input to 0 fabricates a score from invalid data. Consider returning the uncollected block when the value is outside [0, 10], or raising a `ValueError` to make the contract explicit.

```python
        s = max(0, min(10, int(nps_score)))
```

### `backend/app/services/acquisition/ops_card_pg.py`:111-114 · security

No tenant isolation: The table stores tenant_id but load_ops_card doesn't filter by tenant. If inquiry_id collides across tenants, the wrong card could be loaded.

```python
        row = session.execute(
            text("SELECT payload FROM acquisition_ops_cards WHERE inquiry_id = :iid"),
            {"iid": inquiry_id},
        ).scalar()
```

### `backend/app/services/acquisition/ops_card_pg.py`:174-174 · bug

When payment is an empty dict, the ternary creates a bare OpsCardPayment() instance, but when payment is a non-empty dict, the inner dict-comprehension {k: payment.get(k, getattr(OpsCardPayment(), k)) for k in payment} only iterates over the keys present in the serialized payment. Any OpsCardPayment field that was omitted (e.g., because it defaulted to None/empty and was stripped during serialization) will be set to its default via getattr, which is correct. However, the real defect is that getattr(OpsCardPayment(), k) creates a new throwaway OpsCardPayment instance for every key lookup — if OpsCardPayment is a dataclass with non-trivial __init__ defaults, this is expensive and, more importantly, if any default itself depends on other fields or raises (e.g., a field with a factory that returns a mutable object shared across instances), the default will be the shared factory result, not a fresh copy. Use a single reference instance for defaults.

```python
        card.payment = OpsCardPayment(**{k: payment.get(k, getattr(OpsCardPayment(), k)) for k in payment} if payment else OpsCardPayment())
```

### `backend/app/services/acquisition/payment_risk.py`:82-83 · other

Lines 82-83: The bare `except Exception: pass` silently swallows all errors from `ops_store` operations (AttributeError, TypeError, etc.). This makes debugging impossible when the ops_store API changes or fails. Consider logging the exception or re-raising with context.

```python
        except Exception:
            pass
```

### `backend/app/services/acquisition/quote_guard.py`:21-30 · bug

The `now` parameter accepts `Optional[datetime]` but is never asserted to be timezone-aware. When callers pass a naive datetime, `valid_until = start + timedelta(days=days)` produces a timezone-aware `valid_until` (since `start` comes from `_parse_ts`, presumably aware), and the comparison `now >= valid_until` will raise `TypeError: can't compare offset-naive and offset-aware datetimes`. Callers should ensure `now` is UTC-aware, or the function should validate/normalize it.

```python
def quote_validity_view(
    *,
    quote_at: str = "",
    valid_days: Optional[int] = None,
    fx_locked: bool = False,
    fx_note: str = "",
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """报价有效期视图（大白话）。"""
    now = now or datetime.now(timezone.utc)
```

### `backend/app/services/acquisition/sales_collision.py`:0-0 · bug

Race condition: The get/check/set sequence in claim_inquiry is not atomic. If two users call claim_inquiry concurrently for the same inquiry_id, both may see `card` as having no owner (or different owners) before either calls set_owner, leading to silent overwrites without proper collision handling. This is a data integrity issue for a collision-tracking system whose entire purpose is to detect and prevent exactly this scenario. Consider whether ops_store methods need to be called within a transaction or with distributed locking.

```python
    card = ops_store.get_by_inquiry(inquiry_id)
    if card is None:
        card = ops_store.materialize(
            tenant_id=tenant_id or "demo",
            inquiry_id=inquiry_id,
            owner_user_id=user_id,
        )
        return {
            "ok": True,
            "code": "claimed_new",
            ...
        }

    current = (card.owner_user_id or "").strip()
    if not current:
        card = ops_store.set_owner(inquiry_id, user_id, note=note or "认领无主询盘")
        return {
            "ok": True,
            "code": "claimed_empty",
            ...
        }
```

### `backend/app/services/acquisition/sample_flow.py`:94-100 · bug

The fee_status field is referenced in fee_hole logic but never defined in SAMPLE_STATUSES or _TRANSITIONS. The SAMPLE_STATUSES tuple only contains shipment statuses ('none' through 'rejected'), while fee_hole checks for 'unbilled' and 'billed' which are not valid sample statuses. This suggests the fee tracking state machine is incomplete or inconsistently modeled - the code assumes fee_status values exist but they're not part of the defined state transitions.

```python
    fee_hole = False
    if payload:
        if payload.get("status") in ("shipped", "delivered") and payload.get("fee_status") in (
            "unbilled",
            "billed",
        ) and (payload.get("fee_amount") or 0) > 0:
            fee_hole = True
```

### `backend/app/services/acquisition/suppression_list.py`:30-36 · security

Thread safety issue: The module-level `suppression_store` singleton is shared mutable state accessed by `add`, `remove`, and `check_outreach` without any locking. In multi-threaded or async deployments, concurrent calls can cause check-then-act races — e.g., two threads both calling `add` for the same email simultaneously could both pass the `if key in self._by_key` check and insert duplicate entries, or a `remove` could interleave with a `check_outreach` causing a suppressed contact to slip through. This directly violates the module's stated policy that suppression is additive and must prevent re-sending.

```python
class SuppressionStore:
    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], SuppressionEntry] = {}

    @staticmethod
    def _norm(email: str) -> str:
        return (email or "").strip().lower()
```

### `backend/app/services/acquisition/suppression_list.py`:165-166 · security

No persistence guarantee: The comment states '生产可换 DB 表' (production can swap to DB), but the current in-memory implementation loses ALL suppression data on process restart. This violates the stated policy that '抑制只增不减' (suppression is additive and never decreases). If this file is used in production without immediate DB replacement, any server restart will wipe all suppression entries, allowing previously unsubscribed/complained contacts to receive unsolicited emails. A persistence layer or at minimum a restart-safe storage mechanism should be added before production use.

```python
# 全局单例（生产可换 DB 表）
suppression_store = SuppressionStore()
```

### `backend/app/services/acquisition/template_weights.py`:154-154 · bug

Line 137: `max(loss_reason_counts.items(), key=lambda x: x[1])` will raise `ValueError: max() arg is an empty sequence` when there are zero loss records. The ternary conditional expression only provides a default for the result assignment but does not prevent the `max()` call from executing when `loss_reason_counts` is empty.

```python
    top_loss = max(loss_reason_counts.items(), key=lambda x: x[1])[0] if loss_reason_counts else ""
```

### `backend/app/services/acquisition/template_weights.py`:175-176 · other

Lines 153-154: The module-level `_approved` dict is shared mutable state mutated by `approve_weight()` without any synchronization. In multi-threaded or multi-worker deployments, concurrent calls can corrupt the approval records.

```python
# 内存中的「已批准权重」（生产应落 PG；当前先只读建议 + 可选批准记录）
_approved: dict[str, dict[str, Any]] = {}
```

### `backend/app/services/adapters/tradeai/__init__.py`:191-202 · other

The `_tenant_orchestrators` dictionary is a module-level mutable global that is accessed and mutated without any thread synchronization. In a multi-threaded web service (Hermes supervisor pattern), concurrent calls to `tenant_orchestrator()` could race on the check-then-act pattern at lines 178-182: one thread might check `tenant_id not in _tenant_orchestrators` while another is in the middle of creating the orchestrator, potentially causing duplicate creation or, worse, a KeyError if `sys.modules` manipulation in `_load_vendor_isolated` races with this path.

```python
_tenant_orchestrators: Dict[str, Any] = {}


def tenant_orchestrator(tenant_id: str) -> Any:
    """按租户返回隔离的 AgentOrchestrator 实例（其原生为全局单例，总纲 §5.2.3-④ 改造项）。"""
    if not tenant_id:
        raise ValueError("tenant_id 必填（冻结原则 §1.2-3 租户隔离优先）")
    if tenant_id not in _tenant_orchestrators:
        orch_cls = getattr(importlib.import_module(_EXPORTS["AgentOrchestrator"]), "AgentOrchestrator")
        _tenant_orchestrators[tenant_id] = orch_cls()
        logger.info("tradeai adapter: created orchestrator for tenant=%s", tenant_id)
    return _tenant_orchestrators[tenant_id]
```

### `backend/app/services/goodjob/customer_pool_projection.py`:69-78 · security

The projection payload contains raw PII fields (email, phone, name, message_excerpt) without any masking or sensitivity handling. These values will be stored in task queues, potentially logged by the worker infrastructure, and may violate data protection requirements. Consider masking sensitive fields (e.g., partial email masking, phone number truncation) or documenting the PII handling expectations with downstream consumers.

```python
        "customer": {
            "name": _attr_str(row, "name"),
            "email": _attr_str(row, "email"),
            "phone": _attr_str(row, "phone"),
            "product": _attr_str(row, "product"),
            "message_excerpt": _excerpt(getattr(row, "message", "")),
            "status": _attr_str(row, "status"),
            "source_channel": _attr_str(row, "source_channel"),
            "attribution_channel": _attr_str(row, "attribution_channel"),
        },
```

### `backend/app/services/goodjob/trade_document_bridge.py`:53-55 · bug

The idempotency key truncation at 128 chars can cause collisions. Two different payloads with different tenant_id, inquiry_id, doc_type, or content hashes could produce identical keys if the differing segments fall after position 128 in the concatenated string. Consider using a hash prefix (e.g., first 8-16 chars of sha256) instead of raw string truncation to minimize collision risk.

```python
    return (
        f"gj-doc:{tenant_id}:{inquiry_id}:{doc_type}:{_content_hash(items, options)}"
    )[:_KEY_MAX_LEN]
```

### `backend/app/services/hermes/task_control_supervisor.py`:51-62 · bug

The recursive `dfs` in `_validate_dag_topology` can hit Python's default recursion limit (typically 1000) on DAGs with deep chains approaching the MAX_DAG_NODES=100 boundary. A recursion error here would surface as an unhandled exception rather than a clean validation failure. Consider rewriting as an iterative DFS or increasing the recursion limit with a explicit guard.

```python
    def dfs(u: str) -> None:
        visited[u] = 1
        for v in graph_adj.get(u, []):
            if visited.get(v) == 1:
                raise ValueError(f"DAG Governor: 检测到拓扑死循环环路: '{u}' -> '{v}'")
            if visited.get(v) == 0:
                dfs(v)
        visited[u] = 2

    for n in nodes:
        if visited[n.id] == 0:
            dfs(n.id)
```

### `backend/app/services/hermes/task_control_supervisor.py`:282-285 · bug

If any child task has a non-numeric `budget_used` value, the `float()` conversion raises `ValueError` which is caught by the broad `except Exception`, silently resetting `budget_used` to 0.0. This disables the budget gate for the entire plan and could allow unbounded spending. Additionally, the error is not logged, making diagnosis impossible.

```python
    try:
        budget_used = sum(float(t.budget_used or 0) for t in child_tasks)
    except Exception:  # noqa: BLE001
        budget_used = 0.0
```

### `backend/app/services/hermes/task_control_supervisor.py`:428-429 · bug

When `on_fail=abort` triggers `compensate_plan`, only nodes with `compensation_action` in their input get status set to `cancelled`. Nodes that completed successfully *after* a skipped node (i.e., dependents of the skipped node) are left as `done` without their `compensation_action` being executed or status reset. This violates Saga rollback semantics — the plan is marked failed but downstream completed work is not compensated.

```python
        # 2. If node was 'done' or 'executing', and has a compensation action, execute it.
        if task.status in ["done", "executing"] and comp_action:
```

### `backend/app/services/oauth_login.py`:400-410 · security

The QQ OAuth token exchange uses a GET request with client_secret as a query parameter. Per OAuth 2.0 best practices and the QQ OpenAPI documentation, the token endpoint should receive credentials via POST with the body, not GET with query params. GET leaks the client_secret in server access logs, browser history, and Referer headers. Consider changing to client.post() with form data.

```python
        tr = client.get(
            "https://graph.qq.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": app_id,
                "client_secret": key,
                "code": code,
                "redirect_uri": _redirect_uri(),
                "fmt": "json",
            },
        )
```

### `backend/app/services/oauth_login.py`:667-669 · bug

Bug: `verify_wechat_signature` reads `settings.FEISHU_VERIFICATION_TOKEN` instead of a WeChat-specific token setting (e.g. `WECHAT_OPEN_VERIFICATION_TOKEN` or similar). This is almost certainly a copy-paste from the Feishu signature verification pattern. If no Feishu verification token is configured, WeChat event callback signature verification will always fail, breaking WeChat webhook processing. Either add a dedicated WeChat verification token config and reference it here, or remove this function if WeChat server events are not supported.

```python
def verify_wechat_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """验证微信服务器推送的签名（用于事件回调）。"""
    token = settings.FEISHU_VERIFICATION_TOKEN.strip()
```

### `backend/app/services/payment_pkg/payment_service_impl.py`:145-146 · security

Secret exposure risk: `PAYMENT_WEBHOOK_SECRET` is used to compute an HMAC digest. Ensure this value is never logged, returned in responses, or included in stack traces. Confirm that `verify_notify` is only called from trusted webhook endpoints and that the signature comparison path does not inadvertently log `sig` or `secret`. Consider rotating the secret on a regular schedule and storing it in a secrets manager rather than a plain env var.

```python
        secret = (os.getenv("PAYMENT_WEBHOOK_SECRET") or "").strip()
        sig = (signature or "").strip()
```

### `backend/app/services/payment_pkg/payment_service_impl.py`:368-372 · bug

Silent failure in `_record_revenue`: while the method re-raises after rollback, the broad `except Exception` may mask transaction state issues (e.g., `PendingRollbackError`). If the revenue entry is partially written before the exception, the rollback leaves the session in a dirty state. Consider using a separate transaction or explicit savepoint to isolate revenue ledgering from the main payment flow, ensuring idempotency checks are not bypassed by a failed rollback.

```python
        except Exception:
            # BUG-09 修复：财务台账写入失败时回滚并重新抛出，不静默吞异常
            self.db.rollback()
            logger.exception("FinanceLedgerEntry 写入失败 order=%s", order.order_no)
            raise
```

### `backend/app/services/payment_pkg/payment_service_impl.py`:431-441 · bug

TOCTOU race: `_mark_paid_and_provision` uses `SELECT-UPDATE` then proceeds to async provisioning. Under concurrent webhook delivery (channel retries), two requests can both read `status=pending`, pass the `updated == 0` guard, and proceed to provision — causing duplicate benefit issuance. The rollback-to-pending path only protects the sender of the second request, but the first request may have already provisioned. Recommend using a DB-level atomic update with a returning/affected-row check plus a distributed lock or idempotency key, and rejecting the second webhook with a definitive "already processed" status rather than retryable failure.

```python
        updated = (
            self.db.query(PaymentOrder)
            .filter(PaymentOrder.order_no == order_no, PaymentOrder.status == "pending")
            .update({PaymentOrder.status: "paid", PaymentOrder.paid_at: datetime.now(timezone.utc)})
        )
        self.db.commit()
        if updated == 0:
            return None
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
```

### `backend/app/services/payment_service.py`:0-0 · bug

Bug: `_schedule_compensation` references an undefined variable `data` at line 360, which will raise a `NameError` whenever compensation scheduling is attempted, causing the exception handler to fail. Additionally, `sync_b2b_from_payment_notify(self.db, data or {})` at the end of the method is dead/unreachable code because the method either returns after the try/except block or raises an exception before reaching it. The call should either be moved inside the `try` block alongside provisioning calls (if intended) or removed entirely.

```python
        except Exception as exc:
            logger.error(
                "WeChat provision failed, scheduled compensation | order_no=%s err=%s",
                order_no,
                exc_info=True,
            )
            self._schedule_compensation(order, source="wechat_notify")
        return order

    # ------------------------------------------------------------------
    # 处理支付宝回调
    # ------------------------------------------------------------------
    def process_alipay_notify(self, data: dict) -> Optional[PaymentOrder]:
```

### `backend/app/services/payment_service.py`:154-159 · security

Security: Weak webhook signature verification. The HMAC-SHA256 payload format `f"{order_no}:{amount}"` uses a colon separator that could be ambiguous if field values contain colons (e.g., order_no = 'A:B' vs 'A:B:100'). This could allow signature confusion attacks. Additionally, there's no timestamp or nonce to prevent replay attacks. The `PAYMENT_WEBHOOK_SECRET` fallback for non-strict mode also allows unverified callbacks in non-production environments without clear security boundaries.

```python
        payload = f"{order_no}:{amount}"
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
```

### `backend/app/services/payment_service.py`:587-593 · other

Race condition: `process_wechat_notify` and `process_alipay_notify` perform check-then-act without database locking. Concurrent webhook deliveries (common with payment gateways retrying failed notifications) could cause duplicate provisioning, revenue recording, and subscription updates. Consider using SELECT FOR UPDATE or a unique constraint on order_no with idempotency checks at the database level.

```python
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        if not order or order.status != "pending":
            return None

        order.status = "paid"
```


## Medium / Low 索引

### medium

- `backend/app/api/v1/routes/acquisition.py`:339 · **bug** · INCONSISTENT ERROR HANDLING: `intent_preview` catches exceptions and raises HTTPException with 400, but other endpoints like `ops_card_touch`, `ops_ca
- `backend/app/api/v1/routes/acquisition.py`:573 · **bug** · Missing `tenant_id` when creating a new OpsCard: when the card does not exist, a bare `OpsCard(inquiry_id=inquiry_id)` is constructed without a `tenan
- `backend/app/api/v1/routes/acquisition.py`:600 · **bug** · NULL POINTER RISK: In `ops_card_sample`, `card.sample` is accessed at line 600 without null check. If `card` exists but `card.sample` is None, this wi
- `backend/app/api/v1/routes/acquisition.py`:1181 · **bug** · DEAD CODE: Lines 1182-1184 contain a condition check that does nothing (just `pass`). The comment says '同步跟单卡备注' but no code follows. This is unreacha
- `backend/app/api/v1/routes/acquisition.py`:1183 · **bug** · Broken ternary expression and reference to a non-existent attribute. `TenderAdvanceRequest` does not have an `inquiry_id` field, so `hasattr(body, "in
- `backend/app/api/v1/routes/acquisition.py`:1252 · **bug** · Data loss: `card.risk_flags = list(body.risk_flags or [])` overwrites all previously accumulated risk flags on the card with only the flags from the c
- `backend/app/api/v1/routes/auth.py`:65 · **other** · The module-level mutable globals `_email_code_store` (dict[str, list[float]]) and `_email_code_ttl_store` (dict[str, float]) retain state across reque
- `backend/app/api/v1/routes/auth.py`:279 · **maintainability** · Broad exception handling catches `Exception` alongside `jwt.InvalidTokenError`, which swallows system exceptions like `KeyboardInterrupt` and `SystemE
- `backend/app/api/v1/routes/payment.py`:0 · **security** · Several ops endpoints use `dependencies=[]` on the decorator, which explicitly disables any default dependencies (such as security/auth dependencies d
- `backend/app/api/v1/routes/payment.py`:498 · **performance** · Stripe session creation constructs success_url and cancel_url via f-string interpolation of `settings.SITE_URL`. If `SITE_URL` is unset or malformed, 
- `backend/app/api/v1/routes/tenants.py`:389 · **performance** · The async route `generate_tenant_site_content` (line 342) awaits `run_ai_site_builder_v1` which likely performs synchronous HTTP calls to AI services 
- `backend/app/api/v1/routes/tenants.py`:1078 · **bug** · The `/domains` GET endpoint (line 1078) and `/domains` POST endpoint (lines 1103-1106) mark all custom domains with hardcoded `verifyStatus: "verified
- `backend/app/api/v1/routes/tenants.py`:1439 · **bug** · In `_run_register_autopilot` (lines 1439-1448), a bare `except Exception: pass` silently swallows any failure from `build_and_persist_product_profile`
- `backend/app/core/admin_auth.py`:50 · **performance** · Concurrency/Atomicity: get_user_permission_codes performs a non-atomic check-then-set pattern on Redis cache. Between the redis_client.get() and set_c
- `backend/app/core/admin_auth.py`:221 · **performance** · Performance: build_menu_tree calls _load_permission_codes for every recursive call, causing repeated database queries. For a menu tree with N nodes, t
- `backend/app/core/database.py`:41 · **bug** · RoutingSession.get_bind() checks self._flushing which is an internal SQLAlchemy attribute that may not be reliable across versions. Also, if a query i
- `backend/app/core/database.py`:55 · **bug** · Mutable list created with setdefault() on connection.info is stored as shared state. If before_cursor_execute is called before after_cursor_execute co
- `backend/app/core/login_bruteforce.py`:0 · **performance** · `_cleanup_stale_entries` only runs every 300 seconds and uses a cutoff of 1 hour. Entries with `lock_until=0` and `fails=0` (successfully logged-in id
- `backend/app/core/login_bruteforce.py`:198 · **bug** · The Lua script uses `cjson.encode` and `cjson.decode` which are Redis-lua builtins provided by the `redis.server.exec` environment in standard Redis. 
- `backend/app/core/login_bruteforce.py`:242 · **other** · In `_memory_check`, the IP check runs before the identity check, but if the IP is locked, the function returns immediately without checking whether th
- `backend/app/services/acquisition/__init__.py`:106 · **bug** · When buyer.email is empty, key becomes (tenant_id, '') which has truthy second element '', causing `if key[1]:` to be True and enter the conflict bran
- `backend/app/services/acquisition/__init__.py`:515 · **bug** · The `add_note` method silently creates a new OpsCard when inquiry_id doesn't exist (lines 516-518). This masks data integrity issues — callers expecti
- `backend/app/services/acquisition/__init__.py`:628 · **bug** · The sample status auto-transition on line 629 only checks for 'shipped', 'delivered', 'confirmed', 'preparing' but not 'requested'. If a sample goes t
- `backend/app/services/acquisition/__init__.py`:907 · **security** · The module-level singleton stores (`buyer_store`, `ops_card_store`, `playbook_store`) are mutable shared state with no synchronization. In a multi-thr
- `backend/app/services/acquisition/baseline_bench.py`:44 · **bug** · The bare `except Exception` at lines 42-44 silently swallows errors during idempotency checks without logging. This hides failures that should be repo
- `backend/app/services/acquisition/baseline_bench.py`:49 · **bug** · Lines 52-53: The P95 index calculation `int(len(lat_ms) * 0.95) - 1` can produce negative indices for small lists. For example, with len=1, this gives
- `backend/app/services/acquisition/billing_explain.py`:114 · **maintainability** · The `except Exception:` on line 88-89 silently swallows all exceptions from the meter query block without logging. If MeterEvent model doesn't exist o
- `backend/app/services/acquisition/billing_explain.py`:114 · **maintainability** · The `except Exception:` on lines 107-108 silently swallows all exceptions from the acquisition query block without logging. If EvolutionTaskRecord mod
- `backend/app/services/acquisition/billing_explain.py`:134 · **bug** · The `success` attribute access on line 109 uses `getattr(r, 'success', True)` which defaults to True when the attribute doesn't exist. This means if t
- `backend/app/services/acquisition/dispatch_service.py`:110 · **maintainability** · The broad except on lines 105-112 catches all exceptions from parse_graph_to_tasks but only records a truncated message. The original traceback is los
- `backend/app/services/acquisition/experience_feed.py`:93 · **bug** · The variable `currency` is passed into the function but only used inside `record_ops_win`. However, in line 103-104, when `amount` is truthy and `curr
- `backend/app/services/acquisition/experience_feed.py`:105 · **bug** · Lines 105-106: When `amount` is truthy but `currency` is an empty string `''`, the expression `currency or 'USD'` correctly falls back to `'USD'`. How
- `backend/app/services/acquisition/experience_feed.py`:125 · **security** · Line 125: `from app.services.acquisition.loss_report import REASON_HINTS` is imported inside the function body on every call. While this avoids circul
- `backend/app/services/acquisition/experience_feed.py`:129 · **bug** · The `lost` filter includes any card with a truthy `loss_reasons` attribute regardless of its `stage`. If a card reaches `stage == "won"` but still car
- `backend/app/services/acquisition/fulfillment_nodes.py`:108 · **bug** · The balance_status guard uses `not in ("paid",)` which silently allows None (missing balance_status attribute) into the reminder path as non-paid. Bec
- `backend/app/services/acquisition/fulfillment_nodes.py`:109 · **bug** · Missing `stage` in reminder key check: the earlier loop considers `stage` for quote done, but the reminder logic checks `key in ("pi", "deposit")` and
- `backend/app/services/acquisition/growth_ops.py`:0 · **security** · Id generation uses hex[:10] from uuid4, producing only 40 bits of entropy. If these IDs are exposed in URLs or APIs, an attacker could enumerate all c
- `backend/app/services/acquisition/growth_ops.py`:60 · **bug** · link_inquiry calls upsert_content before any validation of the inquiry_id, which means a phantom ContentTouch entry is created even when linking fails
- `backend/app/services/acquisition/intent_classifier.py`:19 · **bug** · The 'competitor' keyword in reject_competitor can cause false positives in neutral or positive contexts where the word appears without rejection inten
- `backend/app/services/acquisition/intent_classifier.py`:96 · **bug** · When multiple intents have the same keyword hit count, only the first matched intent (in rule order) is selected. This means rule ordering silently de
- `backend/app/services/acquisition/knowledge_queue.py`:193 · **maintainability** · Error response shapes are inconsistent: `not_found` returns `{ok: False, ...}` while `already_done` returns `{ok: True, ...}` with the item. This forc
- `backend/app/services/acquisition/loss_report.py`:54 · **bug** · When total_lost is 0 (empty cards or no lost-stage items), counter is empty so sum(counter.values()) is 0, but `or 1` forces total_marks to 1. As a re
- `backend/app/services/acquisition/nps_rescue.py`:0 · **bug** · The should_notify logic uses `bucket == 'detractor'` which depends on the potentially truncated score. If nps_score is float (e.g., 6.9), truncation t
- `backend/app/services/acquisition/nps_rescue.py`:34 · **maintainability** · The broad `except Exception: pass` at lines 33-42 silently swallows all errors from ops_store processing (e.g., AttributeError, TypeError, configurati
- `backend/app/services/acquisition/nps_rescue.py`:37 · **bug** · Ambiguous tenant filtering when `tenant_id` is empty or specific: the condition `if not tenant_id or getattr(c, "tenant_id", "") in ("", tenant_id)` i
- `backend/app/services/acquisition/nps_rescue.py`:43 · **maintainability** · Silent `except Exception: pass` swallows every error from reading `_by_inquiry` and card enumeration, leaving counters and onboarding state at default
- `backend/app/services/acquisition/nps_rescue.py`:79 · **bug** · The NPS score normalization uses `int()` which truncates rather than rounds non-integer scores. A score of 8.9 would become 8 instead of 9, potentiall
- `backend/app/services/acquisition/onboarding.py`:77 · **bug** · The bare `except Exception:` with `pass` on line 56-64 silently swallows all errors during ops_store inspection — including KeyError, AttributeError, 
- `backend/app/services/acquisition/ops_card_pg.py`:0 · **performance** · Re-running DDL on every write: save_ops_card executes CREATE TABLE IF NOT EXISTS DDL before each upsert. This adds unnecessary database round-trips an
- `backend/app/services/acquisition/ops_card_pg.py`:45 · **maintainability** · Generic exception handling: The bare except Exception blocks catch all exceptions but only log warnings, making it difficult to diagnose serialization
- `backend/app/services/acquisition/ops_card_pg.py`:176 · **bug** · Fragile dataclass construction from serialized dicts: passing raw keys from JSON/PG rows directly into `OpsCardLogistics`, `OpsCardSkuLine`, etc., via
- `backend/app/services/acquisition/ops_card_pg.py`:209 · **other** · restore_ops_card silently discards newer in-memory state: If a card is evicted from cache and restored from PG, there's no version check to ensure we'
- `backend/app/services/acquisition/ops_card_pg.py`:224 · **other** · The patch_store_persistence function wraps orig_update and tries to save the returned value, but orig_update might return None or a different object t
- `backend/app/services/acquisition/ops_card_pg.py`:226 · **maintainability** · The update wrapper silently swallows all exceptions from save_ops_card with a bare 'pass', contradicting the module's stated principle of 'failing hon
- `backend/app/services/acquisition/payment_risk.py`:71 · **bug** · Line 71: String matching is case-sensitive for 'payment' (`r.lower()`) but case-insensitive for '付款' (uses `in` operator). If loss_reasons contains mi
- `backend/app/services/acquisition/sales_collision.py`:0 · **bug** · Inconsistent audit record shape: claimed_new returns a dict with keys {type, from, to, at, note}, while claimed_empty and handed_off return entries fr
- `backend/app/services/acquisition/sales_collision.py`:109 · **maintainability** · collision_report reads ops_store._by_inquiry (private attribute) directly instead of using a public API method. This couples the function to internal 
- `backend/app/services/acquisition/sample_flow.py`:64 · **maintainability** · can_transition returns True for self-loops (from_status == to_status), which bypasses the _TRANSITIONS validation. This may allow unintended state cha
- `backend/app/services/acquisition/suppression_list.py`:38 · **security** · Permissive email validation: The check `not email_n or '@' not in email_n` only verifies the presence of an '@' character. This accepts malformed inpu
- `backend/app/services/acquisition/suppression_list.py`:165 · **maintainability** · Global mutable singleton limits testability: The module-level `suppression_store` is a global mutable object. Tests cannot isolate state between test 
- `backend/app/services/acquisition/template_weights.py`:71 · **other** · Lines 49-58: The broad `except Exception` on ops_store iteration silently swallows all errors including potential data corruption or interface contrac
- `backend/app/services/acquisition/template_weights.py`:78 · **security** · Lines 64-65: The `from sqlalchemy import or_` import is inside the try block but `or_` is never used in the query. More critically, if SQLAlchemy is n
- `backend/app/services/adapters/tradeai/__init__.py`:65 · **security** · The SECRET_KEY fallback logic at lines 61-70 has a subtle issue: when TRADEAI_SECRET_KEY is set but SECRET_KEY is already in os.environ (from a parent
- `backend/app/services/adapters/tradeai/__init__.py`:138 · **other** · The `finally` block in `_load_vendor_isolated` (lines 130-136) restores saved modules and removes the vendor path from sys.path. However, if an except
- `backend/app/services/adapters/tradeai/__init__.py`:149 · **other** · The module-level execution at line 139 (`_loaded = _load_vendor_isolated()`) runs during import time. If this adapter module is imported in a multi-th
- `backend/app/services/goodjob/customer_pool_projection.py`:57 · **bug** · Tenant ID validation only rejects empty strings, but whitespace-only values (e.g., '   ') pass through. This can break downstream tenant isolation ass
- `backend/app/services/goodjob/customer_pool_projection.py`:83 · **bug** · The idempotency key is truncated to 128 characters using simple slicing, which can cause collisions between different (inquiry_id, status, updated_at)
- `backend/app/services/goodjob/customer_pool_projection.py`:92 · **performance** · The function docstring claims fail-safe behavior, but there's no try/except around `build_projection()` or `executor.submit()`. If either raises an ex
- `backend/app/services/goodjob/trade_document_bridge.py`:128 · **bug** · The step_number parameter is cast to int but not validated for non-positive values. A step_number of 0 or negative could represent an invalid lifecycl
- `backend/app/services/goodjob/trade_document_bridge.py`:132 · **bug** · int(step_number) can raise ValueError or TypeError if step_number is a non-numeric string. This exception is not caught and will propagate unhelpfully
- `backend/app/services/hermes/harness_gateway.py`:55 · **security** · Logging raw_input without sanitization: Line 61 stores `raw_text` in the event's payload dict under "raw_input". If this IntentEvent is logged (e.g., 
- `backend/app/services/hermes/harness_gateway.py`:57 · **security** · Lines 46-47: `event_id=f"evt_{uuid.uuid4().hex[:12]}"` truncates the UUID to 12 hex characters (48 bits). In a multi-worker deployment with high throu
- `backend/app/services/hermes/harness_gateway.py`:61 · **security** · Lines 56-60: While raw_text is not directly logged, the `payload` dict passed to IntentEvent includes `raw_input` which contains the user's raw text. 
- `backend/app/services/hermes/harness_gateway.py`:114 · **security** · Line 95: `intent=str(intent) if intent else None` - if `intent` is a non-string truthy value (e.g., int, bool), it's silently coerced to string. This 
- `backend/app/services/hermes/task_control_supervisor.py`:266 · **bug** · Multiple locations use bare `except Exception` with only logging, which can hide real configuration or data errors. Specifically: line 138-144 (polici
- `backend/app/services/hermes/task_control_supervisor.py`:281 · **bug** · The `advance_plan` function has a check-check-act race condition: it reads `running_now` and then dispatches tasks, but between these operations anoth
- `backend/app/services/hermes/task_control_supervisor.py`:382 · **bug** · After committing to release row locks, the function re-queries child tasks. Newly dispatched tasks from the current cycle may still be in `running` st
- `backend/app/services/oauth_login.py`:0 · **security** · Dev mode authorize URL encodes provider and code directly in query parameters without any signature or encryption. While low-risk in development, this
- `backend/app/services/oauth_login.py`:113 · **security** · Security: Dev mode bypass exposes `code` in the redirect URL query string via `_dev_authorize_url`. Although this only applies in non-production envir
- `backend/app/services/oauth_login.py`:426 · **security** · Security/Logging: PII (openid prefixes) leaked into logs. Lines 297, 327, 368, and ~413 all log `openid[:8]` which leaks the first 8 characters of a u
- `backend/app/services/oauth_login.py`:465 · **bug** · Bug: The QQ response parser regex `^\s*\w+\s*\(\s*(.+)\s*\)\s*;?\s*$` with `re.DOTALL` uses a greedy `.+` that can over-match when the JSON body itsel
- `backend/app/services/oauth_login.py`:578 · **bug** · WeChat provider ID generation prioritizes unionid over openid, but if unionid is unavailable in subsequent logins (e.g., due to scope changes), the sa
- `backend/app/services/payment_pkg/payment_service_impl.py`:134 · **other** · Amount parsing edge case in `_verify_notify_amount_guard`: when `paid_raw` is a dict (e.g. nested amount object), it falls back to `order.amount`. How
- `backend/app/services/payment_pkg/payment_service_impl.py`:313 · **performance** · Inconsistent error handling across native payment flows: each factory (`create_native_payment`, `create_egress_addon_native`, `create_token_pack_nativ
- `backend/app/services/payment_pkg/payment_service_impl.py`:448 · **maintainability** · Missing `raise` after `self.db.commit()` in `_mark_paid_and_provision`'s exception handler can mask errors if a subsequent call implicitly depends on 
- `backend/app/services/payment_service.py`:0 · **bug** · Potential inconsistency in subscription handling: `create_native_payment` creates or updates a subscription record before creating the payment order. 
- `backend/app/services/payment_service.py`:636 · **bug** · Inconsistent error handling: The Alipay notify handler logs an amount mismatch but returns None (line ~508), silently dropping the notification. This 

### low

- `backend/app/api/v1/routes/acquisition.py`:51 · **bug** · DUPLICATE IMPORT: `get_read_session` is imported twice (lines 51 and 61). Also `claim_inquiry` is imported twice (lines 46 and 60 as `_claim_fn`). Thi
- `backend/app/api/v1/routes/acquisition.py`:499 · **performance** · INEFFICIENT LIST CONVERSION: Multiple places convert to list unnecessarily, e.g., `list(body.reasons or [])` when `body.reasons` is already a List[str
- `backend/app/api/v1/routes/acquisition.py`:607 · **bug** · LOGIC ERROR: In the sample endpoint, `body.qty` and `body.fee_amount` are already added to kwargs in the loop (lines 608-615), then redundantly checke
- `backend/app/api/v1/routes/acquisition.py`:1274 · **bug** · UNUSED VARIABLE: `last` is assigned in the loop but the loop result overwrites it each iteration. The variable serves no purpose since only the final 
- `backend/app/api/v1/routes/acquisition.py`:1530 · **bug** · `card.sample` may be `None` after `ops_card_store.materialize` if the card was just created and no sample object was attached. Accessing `card.sample.
- `backend/app/api/v1/routes/auth.py`:66 · **other** · Variable `_email_code_ttl_store` is declared but never read or written anywhere in this file. It appears to be dead code left over from an earlier imp
- `backend/app/api/v1/routes/payment.py`:127 · **documentation** · The module imports `APIResponse` from `app.core.response` but uses it inconsistently — some endpoints declare `response_model=APIResponse` while other
- `backend/app/api/v1/routes/payment.py`:315 · **maintainability** · The generic `/notify` endpoint logs a warning advising migration to channel-specific routes, but still processes the request through the same `_emit_p
- `backend/app/api/v1/routes/payment.py`:485 · **maintainability** · `create_stripe_session` imports `PaymentService` from the internal package path `app.services.payment_pkg.payment_service_impl` on line 341, while the
- `backend/app/api/v1/routes/payment.py`:550 · **maintainability** · Same issue in the Stripe webhook handler: `PaymentService` is imported again from the internal path on line 408, diverging from the module-level impor
- `backend/app/api/v1/routes/tenants.py`:708 · **performance** · The `generate_tenant_site_content` route (line 388) and `onboarding_autopilot_run` route (line 725) perform CPU-intensive or long-running AI service c
- `backend/app/api/v1/routes/tenants.py`:1323 · **security** · In `_resolve_register_client_ip` (lines 1322-1325), the `x-forwarded-for` header is trusting the first entry without validation. While this is common 
- `backend/app/core/admin_auth.py`:35 · **maintainability** · Correctness: The admin_session_revoked key format uses f"admin_session_revoked:{user.id}:{jti}" but there's no corresponding cleanup mechanism shown. 
- `backend/app/core/admin_auth.py`:120 · **style** · Style: Multiple functions have verbose docstrings with generic ':param request: 参数 request' style documentation that adds no value. The checker functi
- `backend/app/core/database.py`:230 · **bug** · get_pool_status() accesses engine.pool without checking if engine is initialized. During startup or after rebind failures, engine may not have a pool 
- `backend/app/core/login_bruteforce.py`:0 · **bug** · `_identity_key` strips and lowercases `username_or_email` but does not validate that the result is non-empty. If an attacker sends an empty or whitesp
- `backend/app/services/acquisition/__init__.py`:37 · **maintainability** · The `_now_iso()` function uses `datetime.now(timezone.utc)` but should use `datetime.utcnow()` or `datetime.now(timezone.utc)` consistently. The curre
- `backend/app/services/acquisition/__init__.py`:140 · **maintainability** · The duplicate `if key[1]:` check on line 140 is redundant — it's already inside the `if key[1]:` block opened on line 107. This dead branch will never
- `backend/app/services/acquisition/__init__.py`:374 · **maintainability** · The `score_display` method mutates `self.buyer_grade_reason` when computing on-the-fly — this is a side effect that persists back to the in-memory car
- `backend/app/services/acquisition/baseline_bench.py`:3 · **documentation** · The docstring mentions '并发诚实率' (concurrency honesty rate) but both benchmark functions run sequentially. This is misleading documentation. Either impl
- `backend/app/services/acquisition/baseline_bench.py`:73 · **style** · Line 58 uses `is False` for identity comparison. While this works for bool singletons, it is semantically incorrect for checking return values. Use `=
- `backend/app/services/acquisition/billing_explain.py`:32 · **bug** · The `_reason_plain` function uses substring matching with `in` operator on lowercase strings (lines 28-34). The check `if "dispatch" in r` will match 
- `backend/app/services/acquisition/dispatch_service.py`:49 · **maintainability** · Late imports on lines 46-47 and 54-57 reduce code readability and make it harder to track dependencies. While this is a common pattern in FastAPI apps
- `backend/app/services/acquisition/dispatch_service.py`:60 · **performance** · Line 75: The list comprehension builds the full `nodes` list eagerly even when auto_dispatch=False and the function returns early on line 78. For larg
- `backend/app/services/acquisition/dispatch_service.py`:86 · **maintainability** · The session check on line 88-93 returns early with dispatch_error='db_unavailable', but this is inconsistent with the behavior when auto_dispatch=Fals
- `backend/app/services/acquisition/dispatch_service.py`:96 · **maintainability** · Line 92: `getattr(node_tasks[0], "parent_task_id", "")` returns an empty string if the attribute doesn't exist, then line 93 checks `if plan_task_id:`
- `backend/app/services/acquisition/experience_feed.py`:30 · **bug** · Line 30-31: `if db is None` returns early with `{recorded: False, reason: 'db_unavailable'}`. However, `db` could be a falsy value other than `None` (
- `backend/app/services/acquisition/experience_feed.py`:35 · **performance** · Performance - Lazy imports on every call: `EvolutionEngine` is imported inside the function on line 31, and `record_terminal_state` on line 54. These 
- `backend/app/services/acquisition/experience_feed.py`:47 · **maintainability** · Lines 46-47 and 70: Both `error_message` and `output_summary` truncate `detail` to 500 characters (`detail[:500]`). While this prevents excessively lo
- `backend/app/services/acquisition/experience_feed.py`:47 · **maintainability** · String truncation masking errors: Error messages are truncated to 500 characters via `detail[:500]` on lines 42 and 60. For multi-line stack traces or
- `backend/app/services/acquisition/experience_feed.py`:55 · **maintainability** · Bare except with noqa suppression: The `except Exception` blocks here (lines 48-50 and 58-62) are intentionally broad with noqa: BLE001, but this is w
- `backend/app/services/acquisition/experience_feed.py`:80 · **documentation** · The `reasons: list[str]` parameter in `record_ops_loss` has no default value, making it a required positional-or-keyword argument. Callers must always
- `backend/app/services/acquisition/experience_feed.py`:80 · **maintainability** · Line 80: `reasons: list[str]` is a required parameter with no default. If this signature is later changed to have a default (e.g., `reasons: list[str]
- `backend/app/services/acquisition/experience_feed.py`:80 · **maintainability** · Mutable default argument: The parameter `reasons: list[str]` in `record_ops_loss` (line 72) has no default value, requiring callers to always provide 
- `backend/app/services/acquisition/experience_feed.py`:123 · **maintainability** · The `db` parameter is never used in the function body. Callers already pass `None` (see `acquisition/__init__.py` line 612: `win_loss_summary(None, ..
- `backend/app/services/acquisition/experience_feed.py`:125 · **other** · Potential infinite recursion in win_loss_summary: The function imports `REASON_HINTS` from `app.services.acquisition.loss_report` on line 98. If that 
- `backend/app/services/acquisition/experience_feed.py`:138 · **documentation** · Lines 123-124: `max(loss_reasons.items(), ...)` and `max(win_reasons.items(), ...)` will raise `ValueError: max() arg is an empty sequence` when there
- `backend/app/services/acquisition/fulfillment_nodes.py`:97 · **maintainability** · The outer reminder condition tests `pi_no is not None` but since pi_no is always a str (defaulting to `""`), this is always true. The inner elif then 
- `backend/app/services/acquisition/growth_ops.py`:56 · **maintainability** · upsert_content uses a silent fallback pattern: tenant_id parameter is optional with empty string default, but the code does `tenant_id or item.tenant_
- `backend/app/services/acquisition/growth_ops.py`:91 · **performance** · list_contents iterates all items and builds a new list, then sorts by inquiry_count. For large catalogs this is O(n log n) and creates unnecessary dic
- `backend/app/services/acquisition/intent_classifier.py`:26 · **maintainability** · The 't/t' keyword in payment_discuss has no trailing space, while 'tt ' and 'lc ' use trailing-space padding to avoid substring matches. Since the inp
- `backend/app/services/acquisition/intent_classifier.py`:73 · **maintainability** · The `country` parameter in `classify_reply(text: str, country: str = "")` is never referenced in the function body. This suggests either incomplete im
- `backend/app/services/acquisition/intent_classifier.py`:111 · **maintainability** · The confidence score uses a linear formula: min(0.95, 0.45 + 0.15 * best_hits). There is no documentation of downstream thresholds (e.g., is 0.2 vs 0.
- `backend/app/services/acquisition/knowledge_queue.py`:33 · **maintainability** · The pre-scan correctly identified a critical shared mutable seed issue. `_SEED` is a module-level list of dicts, and the `KnowledgeQueueStore.__init__
- `backend/app/services/acquisition/loss_report.py`:35 · **maintainability** · A bare `continue` inside a loop without an outer try/except leaves no traceback information. If getattr(card, 'loss_reasons', None) raises (e.g. on a 
- `backend/app/services/acquisition/loss_report.py`:35 · **maintainability** · The function silently accepts any iterable of objects without validating their shape. If `cards` contains items missing expected fields, AttributeErro
- `backend/app/services/acquisition/nps_rescue.py`:51 · **other** · `int(onboarding_view.get("done_count") or 0)` and `int(onboarding_view.get("total") or 5)` will raise `ValueError` / `TypeError` if the view holds a n
- `backend/app/services/acquisition/nps_rescue.py`:65 · **maintainability** · The billing_view check only appends a rescue action when balance is None, but doesn't validate that the billing integration is actually configured. If
- `backend/app/services/acquisition/onboarding.py`:11 · **maintainability** · **Module-level mutable list of mutable dicts**: `STEPS` is a module-level `list[dict]`. Although the current code only reads from it, any code that im
- `backend/app/services/acquisition/onboarding.py`:11 · **maintainability** · Module-level mutable `STEPS` list is never mutated in this file, but it's exported as part of the module API. Any caller (including tests or other ser
- `backend/app/services/acquisition/onboarding.py`:66 · **maintainability** · Mutable default argument `ops_store: Any = None` is fine, but `tenant_id: str = "demo"` silently falls back to a hardcoded demo tenant when called wit
- `backend/app/services/acquisition/onboarding.py`:81 · **maintainability** · The condition `if not tenant_id` on line 59 combined with `getattr(c, "tenant_id", "") in ("", tenant_id)` means that when `tenant_id` is the empty st
- `backend/app/services/acquisition/onboarding.py`:85 · **bug** · The truthiness check `getattr(c, 'last_touch_at', '')` on line 63 treats both `None` and empty string `''` as falsy (correct), but also treats any tim
- `backend/app/services/acquisition/ops_card_pg.py`:68 · **performance** · Every call to save_ops_card re-executes the CREATE TABLE IF NOT EXISTS statement within the same transaction as the INSERT. Since patch_store_persiste
- `backend/app/services/acquisition/ops_card_pg.py`:174 · **other** · In restore_ops_card, the payment assignment uses a conditional expression that might not work correctly if payment dict is empty.
- `backend/app/services/acquisition/payment_risk.py`:33 · **maintainability** · Line 34: `tenant_id` is declared as a parameter but never used anywhere in the function body. This is dead code that should be removed or documented i
- `backend/app/services/acquisition/payment_risk.py`:88 · **maintainability** · Lines 88-97: The deposit_ratio reduction logic can create inconsistent behavior. When `r >= 0.3`, score decreases by 1, but the threshold checks are o
- `backend/app/services/acquisition/payment_risk.py`:108 · **maintainability** · Line 109: `auto_pi_allowed = False if auto_pi else True` is logically equivalent to `auto_pi_allowed = not auto_pi`, but the conditional expression is
- `backend/app/services/acquisition/quote_guard.py`:61 · **maintainability** · When `expired=True`, the FX branch appends `" 注意汇率可能已变。"` regardless of `fx_note`. If `fx_note` contains useful context (e.g., lock expiry details), i
- `backend/app/services/acquisition/sample_flow.py`:77 · **style** · The fallback status='none' when getattr returns None silently masks potential data issues. If a sample exists but has no status attribute or None stat
- `backend/app/services/acquisition/suppression_list.py`:69 · **maintainability** · Missing input validation for `tenant_id`: Unlike `email` which has validation, `tenant_id` has no length limits or format checks. A tenant_id of None 
- `backend/app/services/acquisition/suppression_list.py`:96 · **maintainability** · Inconsistent email validation in check_outreach(): The `check_outreach` method calls `self.is_suppressed(email_n, tenant_id)` with `email_n` (already 
- `backend/app/services/acquisition/suppression_list.py`:136 · **performance** · Missing bounds check in list_all(): The method returns all entries without pagination. In a multi-tenant production scenario with thousands of suppres
- `backend/app/services/acquisition/suppression_list.py`:145 · **performance** · Inefficient string building in report(): The `plain` summary uses string concatenation with `+` operator and creates an unmaterialized generator expre
- `backend/app/services/adapters/__init__.py`:1 · **documentation** · No issues found. The `__init__.py` is a package marker with only a docstring — it has no executable code, imports, or definitions to review.
- `backend/app/services/adapters/tradeai/__init__.py`:85 · **maintainability** · Lines 76-92: The `_normalize_cors_origins` function mutates the `env` dict parameter directly. While this works because `os.environ` is passed, the fu
- `backend/app/services/adapters/tradeai/__init__.py`:138 · **other** · Line 124: The bare `except Exception` in `_load_vendor_isolated` catches all exceptions including those during module restore in the `finally` block. 
- `backend/app/services/adapters/tradeai/__init__.py`:175 · **other** · Lines 150-156: The `__getattr__` implementation uses `getattr(importlib.import_module(_EXPORTS[name]), name)` which can raise AttributeError in two wa
- `backend/app/services/adapters/tradeai/__init__.py`:219 · **other** · Line 190-206: The `make_context` function creates UUIDs without any collision guarantee beyond hex length. In a high-throughput scenario with many con
- `backend/app/services/goodjob/__init__.py`:1 · **documentation** · The file is currently just a module stub with a copyright header and docstring. It appears incomplete for a service module named `goodjob/__init__.py`
- `backend/app/services/goodjob/customer_pool_projection.py`:83 · **maintainability** · The idempotency key falls back to `created_at` when `updated_at` is None, but the module's design assumes `updated_at` is the authoritative change tim
- `backend/app/services/hermes/harness_gateway.py`:19 · **maintainability** · Line 33: The import `from typing import Any, Dict, Optional` uses the older typing module style. In Python 3.9+, these can be imported from builtins o
- `backend/app/services/hermes/harness_gateway.py`:94 · **documentation** · The docstring describes `process_inbound_webhook` as a 'synchronous entry-point wrapper', but it's defined as an async function. If called from a sync
- `backend/app/services/hermes/harness_gateway.py`:113 · **maintainability** · Double payload.get('context') call: Lines 113 and 115 call payload.get() twice for the same key, which is inefficient. While minor, this pattern reduc
- `backend/app/services/hermes/harness_gateway.py`:113 · **test** · Lines 92-94: The webhook handler validates that context and payload are dicts via isinstance checks, but doesn't validate nested values. Downstream `d
- `backend/app/services/hermes/task_control_supervisor.py`:135 · **maintainability** · In `_resolve_input_from`, when `src_data` is found via `node_tasks` but `json.loads` fails, an empty dict `{}` is used. This silently suppresses data 
- `backend/app/services/oauth_login.py`:78 · **maintainability** · Dead code: The `_SENSITIVE_BODY_KEYS` constant includes `"token"` as a sensitive key. However, `_mask_body` is only called in error/log paths for QQ a
- `backend/app/services/oauth_login.py`:92 · **documentation** · Style/Documentation: Several functions have empty or useless docstrings with the pattern `"""_function_name。"""` followed by `参数说明：:param ... :return:
- `backend/app/services/oauth_login.py`:473 · **bug** · _parse_qq_response's fallback for non-JSON responses blindly splits on '&' and assumes all '=' containing text is query-style. If the response is a ma
- `backend/app/services/payment_pkg/payment_service_impl.py`:101 · **maintainability** · Inconsistent channel validation: some methods check `pay_channel not in ("wechat", "alipay")` while others default to `"wechat"` without validation. E
- `backend/app/services/payment_service.py`:5 · **maintainability** · Unnecessary re-imports: `hashlib`, `hmac`, and `os` are imported at the module level but also imported again inside methods (e.g., `verify_notify`). T


## OCR 项目级摘要（各批原文）

## 来自 ocr-scan-critical-full.json

### Top Issues

1.  **Silent Error Swallowing Across Acquisition Services**
    Broad `except Exception: pass` or silent `except Exception:` blocks appear in `dispatch_service.py`, `nps_rescue.py`, `__init__.py`, `billing_explain.py`, and `baseline_bench.py`. These hide configuration failures, missing dependencies (e.g., `ops_card_pg`), and data integrity errors, making production diagnosis nearly impossible.

2.  **Inconsistent Time Semantics in Bruteforce Protection**
    `login_bruteforce.py` mixes `time.time()` (wall-clock) and `time.monotonic()` (clock-speed). This causes Redis-backed and memory-backed locks to expire at different real-world moments, leading to unpredictable lock durations and potential race conditions during failover.

3.  **IP Extraction Vulnerability via X-Forwarded-For**
    `client_ip_from_request` trusts the first IP in `X-Forwarded-For` without validating proxy chain legitimacy. Attackers can spoof client IPs (e.g., `8.8.8.8`), bypassing IP-based bruteforce locks and identity restrictions.

4.  **Cross-Tenant Data Leak in Billing/Acquisition Queries**
    `billing_explain.py` queries acquisition events without filtering by `tenant_id`/`tid`. This exposes all tenants' activity to any user, constituting a critical security and compliance violation in multi-tenancy contexts.

5.  **Broken Read-Write Split After Engine Rebind**
    `database.py`'s `rebind_engine()` recreates the main engine but leaves `read_engine` stale. Subsequent read operations will hit the old, potentially disconnected or outdated database instance, breaking data consistency.

6.  **Shared Mutable State in Multi-Threaded Acquisition Modules**
    `growth_ops.py`, `knowledge_queue.py`, and `__init__.py` rely on module-level singletons (`content_attr_store`, `knowledge_queue_store`, `buyer_store`) without synchronization. In ASGI environments with multiple workers/threads, this leads to data corruption, race conditions, and lost updates.

7.  **Missing Tenant Isolation in Knowledge Queue**
    `knowledge_queue.py` accepts `tenant_id` parameters in `list()` and `report()` but ignores them, returning all items. This is a latent data leak if multi-tenancy is ever enabled.

8.  **Incomplete Production Key Validation**
    `config.py`'s `_init_production_key_validation()` checks only a subset of secrets (JWT, Redis, DB) while missing AI provider keys (OpenAI, Anthropic). Compromised env vars for these missing keys go undetected.

### Module Hotspots

*   **`backend/app/services/acquisition/`**: High density of issues across 8+ files. Dominated by silent error handling, missing tenant filters, race conditions on shared state, and business logic gaps (e.g., `loss_report.py`, `dispatch_service.py`, `nps_rescue.py`).
*   **`backend/app/core/database.py`**: Critical concurrency and lifecycle bugs (stale engines, unsafe stack assumptions, logger usage before definition).
*   **`backend/app/core/login_bruteforce.py`**: Security-relevant time inconsistency and IP spoofing vulnerabilities.
*   **`backend/app/core/config.py`**: Structural maintainability issues and incomplete security validation.

### Cross-Cutting Concerns

*   **Bare/ Silent Exception Handling**: Found in `database.py`, `login_bruteforce.py` (Lua fallbacks), `baseline_bench.py`, `billing_explain.py`, `dispatch_service.py`, `nps_rescue.py`, and `__init__.py`. The pattern is consistent: broad catches with no logging or re-raising, obscuring root causes.
*   **Missing Tenant Context Propagation**: `billing_explain.py` and `knowledge_queue.py` fail to enforce tenant boundaries in queries or method signatures, risking data leakage.
*   **Inconsistent Input Validation**: `intent_classifier.py` has inconsistent keyword padding ('t/t' vs 'tt '), `experience_feed.py` has inconsistent currency fallbacks, and `login_bruteforce.py` doesn't validate empty usernames in key generation.
*   **Mutable Default Arguments / Side Effects**: `experience_feed.py` warns about potential mutable default list risks; `__init__.py` mutates `buyer_grade_reason` during read operations (`score_display`), causing persistent side effects.

### Quick Wins

1.  **Add Logging to Silent Catches**: In `billing_explain.py` (lines 88, 107) and `dispatch_service.py` (lines 36, 105), replace silent `except` blocks with `logger.warning` or `logger.exception` to surface failures.
2.  **Standardize Time Sources**: Refactor `login_bruteforce.py` to use `_now_mono()` (`time.monotonic()`) exclusively for all lock expiration calculations to ensure consistent semantics across Redis and memory stores.
3.  **Validate X-Forwarded-For Chain**: Update `client_ip_from_request` in `login_bruteforce.py` to validate that forwarded IPs belong to trusted proxy ranges before trusting them.
4.  **Fix Tenant Filter in Billing**: Add `WHERE tid = :tenant_id` to the acquisition events query in `billing_explain.py`.
5.  **Update Read Engine on Rebind**: In `database.py`, ensure `rebind_engine()` also updates `read_engine` to prevent stale database connections.
6.  **Remove Dead Code**: Delete the redundant `if key[1]:` check in `acquisition/__init__.py` (line 140) which is unreachable.
7.  **Validate Config File Existence**: In `config.py`, add a check to ensure files in `_env_file` actually exist before passing them to pydantic-settings, preventing silent ignore of misconfigured paths.
## 来自 ocr-scan-batch2.json

### Top Issues

1.  **Payment Webhook Security & Integrity Failures** (`backend/app/api/v1/routes/payment.py`)
    *   The Stripe webhook handler accepts `checkout.session.completed` events without verifying the actual `payment_status`, allowing potential spoofing.
    *   A broad `try/except Exception` swallows signature verification failures and metadata errors, returning 500s that trigger aggressive Stripe retries instead of appropriate 403/400 responses.
    *   Balance payment logic lacks compensation guarantees: if provisioning fails after wallet debit, the refund path itself may fail, leaving the wallet debited without service provisioned.

2.  **Authentication Bypass & Token Revocation Failure** (`backend/app/core/admin_auth.py`, `backend/app/api/v1/routes/auth.py`)
    *   `jwt.decode` is called with `verify_exp=False`, meaning revoked/expired tokens bypass blacklist checks indefinitely if leaked.
    *   Dev auto-bind logic allows any `dev_`-prefixed OAuth identity to bind to admin accounts without password/2FA; leakage of this flag into production is a critical risk.
    *   Bare `except` blocks in `_get_token_jti` and auth routes swallow `JWTDecodeError` and other authentication errors, making it impossible to distinguish between valid tokens without JTI and malformed tokens.

3.  **Tenant Data Integrity & Validation Gaps** (`backend/app/api/v1/routes/tenants.py`)
    *   Domain verification is faked: GET/POST endpoints hardcode `verifyStatus: "verified"` and `sslStatus: "active"` without actual DNS/SSL checks, misleading the frontend.
    *   Tenant settings updates accept arbitrary JSON without schema validation, allowing clients to inject malicious or corrupt configuration blobs.
    *   IP resolution trusts the first entry in `X-Forwarded-For` without validation, vulnerable to header injection in non-trusted proxy environments.
    *   Fallback query when no active `UserTenant` link exists returns the first tenant in the DB (`db.query(Tenant).first()`), breaking multi-tenant isolation.

4.  **Hermes Task Supervisor Concurrency & State Bugs** (`backend/app/services/hermes/task_control_supervisor.py`)
    *   Recursive DAG validation (`dfs`) can hit Python’s recursion limit on deep graphs, causing unhandled crashes instead of clean validation failures.
    *   Compensation logic leaves dependent nodes (completed after a skipped node) in `done` status without triggering their `compensation_action`, resulting in inconsistent system state.
    *   Broad `except Exception` blocks silently reset `budget_used` to 0.0 on parse errors, disabling budget gates and allowing unbounded spending.
    *   Race condition in `advance_plan`: between reading `running_now` and dispatching tasks, another process may dispatch additional tasks, violating batch isolation.

5.  **TradeAI Adapter Global State & Isolation Risks** (`backend/app/services/adapters/tradeai/__init__.py`)
    *   Module-level mutable global `_tenant_orchestrators` is accessed without thread synchronization, causing race conditions in multi-threaded worker environments.
    *   Import-time execution (`_loaded = _load_vendor_isolated()`) creates a race condition if the module is imported concurrently by multiple workers.
    *   `SECRET_KEY` fallback logic is broken: if `SECRET_KEY` is already set in the parent environment, the dedicated `TRADEAI_SECRET_KEY` is ignored, potentially weakening isolation.
    *   Bare `except Exception` in `_load_vendor_isolated` masks errors during module restore in the `finally` block, potentially leaving the application in a partially corrupted state.

6.  **Auth Route Race Conditions & Undefined Variables** (`backend/app/api/v1/routes/auth.py`)
    *   Undefined variable `count` in the rate-limit fallback path causes an `UnboundLocalError` whenever Redis is unavailable, breaking authentication entirely during outages.
    *   In-memory email code storage (`_email_code_store`, `_email_code_ttl_store`) uses mutable globals without thread safety, leading to data corruption under concurrent requests.
    *   Check-then-act race condition in email verification: concurrent requests with the same valid code can bypass the `used=True` check, allowing multiple logins.

7.  **PII Leakage in Job Projections** (`backend/app/services/goodjob/customer_pool_projection.py`)
    *   Projection payloads contain raw PII (email, phone, name) without masking, which will be stored in task queues and potentially logged by worker infrastructure, violating data protection requirements.

8.  **OAuth Implementation Flaws** (`backend/app/services/oauth_login.py`)
    *   `verify_wechat_signature` incorrectly reads `FEISHU_VERIFICATION_TOKEN` instead of a WeChat-specific token, causing signature verification to always fail or use wrong credentials.
    *   QQ OAuth token exchange uses GET with `client_secret` in query parameters, leaking secrets in server logs and browser history; should use POST with body credentials.
    *   WeChat provider ID generation prioritizes `unionid` over `openid`; if `unionid` becomes unavailable, the same user gets a different provider ID, causing duplicate accounts.

---

### Module Hotspots

*   **`backend/app/api/v1/routes/payment.py`**: High severity issues集中在 webhook security, idempotency, and error handling. 9 distinct comments covering security, concurrency, and correctness.
*   **`backend/app/core/admin_auth.py`**: Critical security flaws in JWT verification and token revocation. 6 comments highlighting authentication bypass risks.
*   **`backend/app/services/adapters/tradeai/__init__.py`**: Concurrency and isolation vulnerabilities in a core adapter module. 7 comments focusing on thread safety and error handling.
*   **`backend/app/api/v1/routes/auth.py`**: Race conditions and undefined variables in authentication flows. 6 comments highlighting availability and correctness issues.
*   **`backend/app/api/v1/routes/tenants.py`**: Data integrity and validation gaps in tenant management. 7 comments covering security, validation, and multi-tenant isolation.
*   **`backend/app/services/hermes/task_control_supervisor.py`**: Concurrency bugs and state management issues in task orchestration. 7 comments focusing on race conditions and error swallowing.

---

### Cross-Cutting Concerns

*   **Bare `except Exception` Swallowing Critical Errors**
    *   Patterns found in: `payment.py`, `admin_auth.py`, `tradeai/__init__.py`, `auth.py`, `tenants.py`, `task_control_supervisor.py`
    *   Consistently masks configuration errors, data integrity issues, and security failures, making debugging difficult and hiding real problems.

*   **Missing Thread Synchronization for Shared State**
    *   Affected: `tradeai/__init__.py` (_tenant_orchestrators), `auth.py` (_email_code_store), `tenants.py` (_register_rate), `admin_auth.py` (Redis cache)
    *   Multiple modules use mutable globals or check-then-act patterns without locks, leading to race conditions in multi-worker deployments.

*   **Inconsistent Error Handling & Response Codes**
    *   Affected: `payment.py`, `auth.py`, `task_control_supervisor.py`
    *   Signature failures return 500 instead of 403; validation errors are swallowed; API response models are inconsistently declared, breaking OpenAPI schemas.

*   **Insufficient Input Validation**
    *   Affected: `tenants.py` (tenant settings, XFF headers), `customer_pool_projection.py` (tenant_id whitespace), `trade_document_bridge.py` (step_number)
    *   Missing schema validation, trust of proxied headers without verification, and lack of boundary checks on numeric inputs.

*   **Idempotency Key Collisions**
    *   Affected: `customer_pool_projection.py`, `trade_document_bridge.py`
    *   Both modules truncate idempotency keys to 128 characters using simple slicing, risking collisions between distinct payloads.

---

### Quick Wins

1.  **Fix `verify_wechat_signature` token mismatch** (`backend/app/services/oauth_login.py`): Change to use WeChat-specific verification token instead of `FEISHU_VERIFICATION_TOKEN`.
2.  **Define `count` in auth rate-limit fallback** (`backend/app/api/v1/routes/auth.py`): Ensure `count` is initialized before the fallback path to prevent `UnboundLocalError` when Redis is unavailable.
3.  **Add thread lock to `_register_rate`** (`backend/app/api/v1/routes/tenants.py`): Wrap the read-modify-write sequence in a lock to prevent race conditions during concurrent registrations.
4.  **Validate `step_number` in trade document bridge** (`backend/app/services/goodjob/trade_document_bridge.py`): Add check for `step_number < 1` and raise `ValueError` with clear message.
5.  **Sanitize raw input in harness gateway** (`backend/app/services/hermes/harness_gateway.py`): Replace `raw_text` in event payload with sanitized/redacted version to prevent PII leakage in logs.
6.  **Standardize Stripe webhook error handling** (`backend/app/api/v1/routes/payment.py`): Return 403 for signature failures, 400 for missing metadata, and only 500 for unexpected internal errors to stop aggressive retry loops.
7.  **Add tenant_id whitespace stripping** (`backend/app/services/goodjob/customer_pool_projection.py`): Apply `.strip()` to tenant_id and reject if empty after stripping to prevent isolation bypasses.
8.  **Fix OAuth token exchange method** (`backend/app/services/oauth_login.py`): Change QQ token exchange from GET with query params to POST with credentials in request body.
## 来自 ocr-scan-batch3.json

### Top Issues

1. **Silent Error Swallowing & Data Loss in `nps_rescue.py`**
   - Critical bugs in `backend/app/services/acquisition/nps_rescue.py`:
     - Negative NPS scores are coerced to `0` (detractor) instead of being handled gracefully or rejected.
     - A missing parenthesis in a conditional expression (`sum(...) or getattr(...)`) breaks the logic flow, likely causing incorrect card enumeration or state updates.
     - `except Exception: pass` blocks silently discard errors when loading `_by_inquiry` and card data, making it indistinguishable between "no data" and "failed to load."
   - **Impact:** High. Leads to incorrect rescue state, silent failures, and inability to debug production issues.

2. **Broken Ternary Logic & Data Overwrite in `routes/acquisition.py`**
   - `backend/app/api/v1/routes/acquisition.py`:
     - The expression `if (out.get("ok") and body.inquiry_id)` is parsed incorrectly due to operator precedence, and `body.inquiry_id` does not exist on `TenderAdvanceRequest`, rendering the logic broken.
     - `card.risk_flags = list(body.risk_flags or [])` overwrites existing risk flags instead of merging, causing data loss (e.g., losing sanctions watch flags).
     - Duplicate route registration for `@router.get("/ops/reconcile")` means the first definition is unreachable.
   - **Impact:** High. API endpoints behave incorrectly, potential security/compliance data loss, and maintenance confusion due to dead code.

3. **Schema Drift & Fragile Dataclass Construction in `ops_card_pg.py`**
   - `backend/app/services/acquisition/ops_card_pg.py`:
     - Using `**` unpacking from JSON/DB rows into dataclasses (`OpsCardLogistics`, etc.) will raise `TypeError` if the schema drifts (old rows have new fields).
     - Redundant `CREATE TABLE IF NOT EXISTS` on every save adds unnecessary DB round-trips.
     - The update wrapper silently swallows exceptions from `save_ops_card`, contradicting the module's "fail honestly" principle.
   - **Impact:** Medium-High. System fragility against schema changes, performance degradation, and silent persistence failures.

4. **Ambiguous Tenant Filtering in `nps_rescue.py`**
   - `backend/app/services/acquisition/nps_rescue.py`:
     - The condition `getattr(c, "tenant_id", "") in ("", tenant_id)` treats unassigned cards (empty tenant) as valid matches for *any* specific tenant ID.
   - **Impact:** High. Potential cross-tenant data leakage or incorrect aggregation in multi-tenant environments.

5. **Mutable Global State in `onboarding.py`**
   - `backend/app/services/acquisition/onboarding.py`:
     - `STEPS` is a module-level mutable list of mutable dicts. Importing this allows external code to mutate shared state, affecting all other consumers.
   - **Impact:** Medium. Subtle bugs and side effects across the application if any module modifies `STEPS`.

### Module Hotspots

*   **`backend/app/services/acquisition/`**: This module has the highest density of critical issues, including silent error handling, broken logic in `nps_rescue.py`, fragile persistence in `ops_card_pg.py`, and mutable global state in `onboarding.py`.
*   **`backend/app/api/v1/routes/acquisition.py`**: Contains critical API logic errors, including unreachable routes, broken ternaries, and data loss due to overwriting collections.

### Cross-Cutting Concerns

*   **Silent Error Handling (`except: pass`)**: Appears in `nps_rescue.py` and `ops_card_pg.py`. This anti-pattern hides failures, making production debugging extremely difficult and leading to silent data corruption or missing state.
*   **Unvalidated/Dangerous Data Coercion**: 
    - `nps_rescue.py`: Coerces negative NPS to 0; crashes on non-numeric onboarding view strings.
    - `ops_card_pg.py`: Blindly unpacks DB/JSON data into dataclasses without schema validation.
*   **Inconsistent State Mutation**: `routes/acquisition.py` overwrites `risk_flags` instead of merging; `experience_feed.py` includes cards in both "won" and "lost" categories if `loss_reasons` is not cleared on win.

### Quick Wins

1.  **Remove `except: pass` blocks**: In `nps_rescue.py` and `ops_card_pg.py`, replace with specific exception logging or re-raising to preserve diagnostic information.
2.  **Fix Tenant Filtering**: In `nps_rescue.py`, exclude empty tenant IDs from the match tuple for specific tenants (e.g., `if tenant_id and getattr(c, "tenant_id", "") == tenant_id`).
3.  **Correct API Logic**: In `routes/acquisition.py`, remove the duplicate `/ops/reconcile` route and fix the broken ternary for `inquiry_id` (which should likely be `body.get("inquiry_id")` or similar, depending on the model).
4.  **Prevent Data Loss**: In `routes/acquisition.py`, change `card.risk_flags = ...` to a merge operation (e.g., `card.risk_flags = list(set(card.risk_flags or []) | set(body.risk_flags or []))`).
5.  **Immutability**: In `onboarding.py`, convert `STEPS` to a frozen dataclass structure or a tuple of tuples to prevent accidental mutation.
## 来自 ocr-scan-batch4.json

### Top Issues

1.  **WeChat Signature Verification Uses Feishu Token** (`backend/app/services/oauth_login.py`)
    `verify_wechat_signature` references `settings.FEISHU_VERIFICATION_TOKEN` instead of a WeChat-specific setting. This is likely a copy-paste error that would cause WeChat signature verification to fail or accept invalid signatures if tokens overlap.

2.  **QQ Response Parser Regex Greedy Over-match** (`backend/app/services/oauth_login.py`)
    The regex `^\s*\w+\s*\(\s*(.+)\s*\)\s*;?\s*$` with `re.DOTALL` uses a greedy `.+` that can over-match when JSON bodies contain balanced parentheses (e.g., nested values like `"(val)"`). This could corrupt response parsing.

3.  **Short UUID Generation Risking Event ID Collisions** (`backend/app/services/hermes/harness_gateway.py`, lines 46-47)
    `event_id` is generated by truncating a UUID to 12 hex characters (48 bits). In high-throughput, multi-worker deployments, collision probability becomes non-negligible (~0.03% at 1M events), potentially causing event deduplication failures or data corruption.

4.  **PII Leakage via OpenID Prefix Logging** (`backend/app/services/oauth_login.py`, lines 297, 327, 368, ~413)
    Logs emit `openid[:8]`, leaking the first 8 characters of users' persistent, globally unique OpenIDs (QQ and WeChat). While not a full secret, this constitutes PII exposure and violates privacy best practices.

5.  **Dev Mode OAuth Code Exposure in URLs** (`backend/app/services/oauth_login.py`)
    The `_dev_authorize_url` function exposes the OAuth `code` in the redirect URL query string. This code may be logged in server access logs or browser history, creating a security risk even in non-production environments.

6.  **Async Docstring Misleading Sync Callers** (`backend/app/services/hermes/harness_gateway.py`)
    `process_inbound_webhook` is documented as a "synchronous entry-point wrapper" but is defined as an async function. Calling it without `await` or `asyncio.run()` from a sync context will raise a `TypeError`.

### Module Hotspots

-   **`backend/app/services/oauth_login.py`**: Contains 6 comments covering critical bugs (signature verification, regex parsing), security issues (PII logging, dev mode exposure), dead code, and style problems. This is the highest-density hotspot.
-   **`backend/app/services/hermes/harness_gateway.py`**: Contains 6 comments focusing on type safety, PII exposure risks, event ID generation quality, and documentation accuracy.

### Cross-Cutting Concerns

-   **PII/Privacy Exposure**: Both files exhibit patterns where sensitive user data (OpenID prefixes, raw user input in `IntentEvent`) is logged or exposed without adequate masking. Representative paths: `oauth_login.py` (lines 297, 327, 368, ~413) and `harness_gateway.py` (lines 56-60).
-   **Inconsistent/Error-Prone OAuth Implementation**: The OAuth login service has multiple implementation flaws: incorrect token reference for WeChat, fragile regex parsing for QQ, and insecure dev-mode URL handling. Path: `backend/app/services/oauth_login.py`.
-   **Type and Validation Gaps**: `harness_gateway.py` shows insufficient validation of nested payload types and silent coercion of non-string intent values to strings, risking downstream failures. Paths: `harness_gateway.py` (lines 46-47, 56-60, 92-94, 95).

### Quick Wins

-   **Fix WeChat Token Reference** (`oauth_login.py`): Replace `settings.FEISHU_VERIFICATION_TOKEN` with the correct WeChat verification token setting.
-   **Fix QQ Regex Greediness** (`oauth_login.py`): Change the regex to use a non-greedy quantifier (`.+?`) or a more precise pattern that avoids over-matching on nested parentheses.
-   **Remove/Mask OpenID Prefixes in Logs** (`oauth_login.py`): Stop logging `openid[:8]` or replace with a non-identifying hash/token.
-   **Generate Full UUIDs for Event IDs** (`harness_gateway.py`, line 46-47): Use the full UUID hex string instead of truncating to 12 characters to eliminate collision risk.
-   **Correct Async Docstring** (`harness_gateway.py`): Update the docstring for `process_inbound_webhook` to accurately reflect its async nature.
-   **Add Nested Payload Validation** (`harness_gateway.py`, lines 92-94): Extend `isinstance` checks to validate nested dictionary values or add schema validation to catch type mismatches earlier.
## 来自 ocr-scan-batch5-payment.json

### Top Issues

1.  **Duplicate Subscriptions and Revenue via TOCTOU Races**
    *Root Cause*: Both `process_wechat_notify`/`process_alipay_notify` and `_mark_paid_and_provision` perform check-then-act operations without database locks.
    *Impact*: Concurrent webhook retries from payment gateways can pass the `status=pending` guard multiple times, leading to duplicate benefit provisioning, double revenue recording, and corrupted subscription states.
    *Paths*: `backend/app/services/payment_service.py`, `backend/app/services/payment_pkg/payment_service_impl.py`

2.  **Webhook Signature Confusion Attack**
    *Root Cause*: HMAC-SHA256 payload format uses a colon separator (`f"{order_no}:{amount}"`).
    *Impact*: If `order_no` contains a colon (e.g., `A:B`), an attacker could craft a payload where the intended amount shifts into the order_no field, potentially bypassing signature verification or altering the interpreted amount.
    *Path*: `backend/app/services/payment_service.py`

3.  **Indefinite Order Pending State (Silent Failure)**
    *Root Cause*: The Alipay notify handler logs an amount mismatch but returns `None` instead of success or an explicit error code.
    *Impact*: The payment gateway interprets the lack of success response as a failure and may not retry appropriately, or the order remains stuck in a `pending` state indefinitely because the system neither acknowledges nor explicitly rejects the notification.
    *Path*: `backend/app/services/payment_service.py`

4.  **Cascading Failure in Compensation Scheduling**
    *Root Cause*: `_schedule_compensation` references an undefined variable `data`.
    *Impact*: Any attempt to schedule compensation raises a `NameError`, which is caught by an exception handler that likely fails due to the same missing context, resulting in silent loss of compensation logic and potential data inconsistency.
    *Path*: `backend/app/services/payment_service.py`

5.  **Subscription-Order Transactional Inconsistency**
    *Root Cause*: `create_native_payment` creates/updates a subscription record *before* creating the payment order.
    *Impact*: If the payment order creation fails (e.g., DB error), the subscription is left in an inconsistent state (created but no payment order exists), requiring complex manual rollback logic that may not cover all edge cases.
    *Path*: `backend/app/services/payment_service.py`

### Module Hotspots

*   **`backend/app/services/payment_pkg/payment_service_impl.py`**: High density of critical issues including race conditions, manual transaction management errors, and input validation gaps.
*   **`backend/app/services/payment_service.py`**: Central hub for security vulnerabilities (webhook verification) and critical bugs (undefined variables, silent failures).

### Cross-Cutting Concerns

*   **Inconsistent Error Handling in Payment Flows**:
    Multiple methods (`create_native_payment`, `create_egress_addon_native`, `create_token_pack_native`) manually call `self.db.rollback()` in error branches. If the caller’s outer transaction expects to commit, this creates conflicting transaction states. Additionally, broad `except Exception` blocks (e.g., in `_record_revenue`) may mask `PendingRollbackError` or other session-level issues.
    *Paths*: `backend/app/services/payment_pkg/payment_service_impl.py`

*   **Lack of Atomicity in Critical Operations**:
    Both the old (`payment_service.py`) and new (`payment_pkg/payment_service_impl.py`) implementations fail to use database-level locking or atomic updates for state transitions (pending -> paid), making them vulnerable to race conditions under concurrent webhook delivery.
    *Paths*: `backend/app/services/payment_service.py`, `backend/app/services/payment_pkg/payment_service_impl.py`

*   **Inconsistent Input/Channel Validation**:
    Some methods enforce a whitelist for `pay_channel` (`wechat`, `alipay`), while others default silently to `"wechat"` without validation, creating injection vectors or unexpected behavior.
    *Paths*: `backend/app/services/payment_pkg/payment_service_impl.py`

*   **Secret Exposure Risk**:
    The `PAYMENT_WEBHOOK_SECRET` is used in HMAC computation. There are concerns about it being logged or included in stack traces, especially given the inconsistent error handling that might expose internal state.
    *Path*: `backend/app/services/payment_pkg/payment_service_impl.py`

### Quick Wins

1.  **Remove Redundant Imports**: Eliminate inline imports of `hashlib`, `hmac`, and `os` in `verify_notify` and other methods, as they are already imported at the module level. This improves code clarity.
    *Path*: `backend/app/services/payment_service.py`

2.  **Fix Alipay Handler Return Value**: Change the Alipay notify handler to return a success response (as per Alipay docs) even on amount mismatch, or explicitly return an error code that triggers gateway retry, rather than returning `None` which leaves orders pending.
    *Path*: `backend/app/services/payment_service.py`

3.  **Repair Undefined Variable**: Define or pass the `data` variable correctly in `_schedule_compensation` to prevent `NameError`.
    *Path*: `backend/app/services/payment_service.py`

4.  **Standardize Channel Validation**: Enforce a consistent whitelist check for `pay_channel` at all entry points, removing silent defaults.
    *Path*: `backend/app/services/payment_pkg/payment_service_impl.py`

5.  **Secure Webhook Signature Format**: Replace the colon-separated HMAC payload with a more robust format (e.g., JSON serialization or length-prefixed fields) to prevent signature confusion attacks.
    *Path*: `backend/app/services/payment_service.py`
## 来自 ocr-scan-batch6-acq-rest.json

### Top Issues

1.  **Data Integrity & Concurrency Races**
    Critical race conditions in `tender_engine.py` (check-then-act on stage transitions) and `sales_collision.py` (non-atomic claim/handoff). In `ops_card_pg.py`, concurrent cache restores risk overwriting newer in-memory state with stale persistence data due to missing version checks.
    *   *Paths:* `backend/app/services/acquisition/tender_engine.py`, `backend/app/services/acquisition/sales_collision.py`, `backend/app/services/acquisition/ops_card_pg.py`

2.  **Tenant Isolation Violations**
    `ops_card_pg.py` loads cards without filtering by `tenant_id`, risking cross-tenant data leakage if `inquiry_id` collides. `onboarding.py` silently falls back to a hardcoded `"demo"` tenant when arguments are missing, potentially filtering cards against the wrong tenant context in production.
    *   *Paths:* `backend/app/services/acquisition/ops_card_pg.py`, `backend/app/services/acquisition/onboarding.py`

3.  **Silent Error Swallowing (Debugging Black Holes)**
    Widespread use of bare `except Exception: pass` blocks prevents debugging of store failures, key errors, and type mismatches. This appears in `onboarding.py`, `payment_risk.py`, `template_weights.py`, and `ops_card_pg.py`. `experience_feed.py` also truncates stack traces to 500 chars, losing critical diagnostic context.
    *   *Paths:* `backend/app/services/acquisition/onboarding.py`, `backend/app/services/acquisition/payment_risk.py`, `backend/app/services/acquisition/template_weights.py`

4.  **State Corruption via Mutable Globals**
    Several modules expose or mutate module-level singletons without synchronization: `STEPS` list in `onboarding.py`, `_approved` dict in `template_weights.py`, and `suppression_store` in `suppression_list.py`. These are vulnerable to concurrent corruption and make unit testing difficult due to lack of isolation/cleanup.
    *   *Paths:* `backend/app/services/acquisition/onboarding.py`, `backend/app/services/acquisition/template_weights.py`, `backend/app/services/acquisition/suppression_list.py`

5.  **Logic Errors in Core State Machines**
    `sample_flow.py` contains invalid transition paths (self-loops bypassing validation) and references undefined status values (`unbilled`, `billed`) not present in `SAMPLE_STATUSES`. `tender_engine.py` allows arbitrary stage jumps to `won`/`lost` from initial stages, bypassing qualification gates.
    *   *Paths:* `backend/app/services/acquisition/sample_flow.py`, `backend/app/services/acquisition/tender_engine.py`

6.  **Incomplete Data Validation**
    `quote_guard.py` fails to enforce timezone awareness on naive datetime inputs, leading to runtime errors. `tender_engine.py` accepts negative or unvalidated amounts. `suppression_list.py` uses permissive email validation (`'@'` check only) and lacks input bounds for `tenant_id`.
    *   *Paths:* `backend/app/services/acquisition/quote_guard.py`, `backend/app/services/acquisition/tender_engine.py`, `backend/app/services/acquisition/suppression_list.py`

7.  **Crash Risks on Empty Data**
    `template_weights.py` calls `max()` on an empty sequence when there are zero loss records, causing an unhandled `ValueError`. The ternary default only affects the assignment, not the `max()` call itself.
    *   *Paths:* `backend/app/services/acquisition/template_weights.py`

### Module Hotspots

*   **`backend/app/services/acquisition/`**
    This directory contains all reviewed files and exhibits high density of concurrency issues, silent error handling, and state management flaws. Specific concentration in:
    *   `onboarding.py`: Tenant fallback and mutable global risks.
    *   `tender_engine.py`: Race conditions and logic bypasses.
    *   `template_weights.py`: Empty sequence crashes and unprotected globals.
    *   `suppression_list.py`: Thread-safety and persistence gaps.

### Cross-Cutting Concerns

*   **Unsafe Exception Handling**: Consistent pattern of `except Exception: pass` or overly broad catches in `onboarding.py`, `payment_risk.py`, `template_weights.py`, and `ops_card_pg.py`.
*   **Thread-Safety Neglect**: Multiple modules (`tender_engine.py`, `suppression_list.py`, `template_weights.py`, `sales_collision.py`) operate on shared mutable state without locks, posing significant risks in async or multi-worker deployments.
*   **Missing Tenant Context Enforcement**: Aside from the explicit bug in `ops_card_pg.py`, `onboarding.py` has implicit fallbacks that compromise tenant isolation.
*   **Inconsistent Audit/History Schemas**: `sales_collision.py` returns inconsistently shaped audit records (`claimed_new` vs. `handoff_history`), making downstream consumption fragile.

### Quick Wins

1.  **Fix `template_weights.py` Empty Sequence Crash**: Add a guard clause before `max(loss_reason_counts.items(), ...)` to return a default or empty dict when the list is empty.
2.  **Replace Bare `except` Blocks**: Add logging or re-raise specific exceptions in `onboarding.py` (line 56-64), `payment_risk.py` (lines 82-83), and `template_weights.py` (lines 49-58).
3.  **Add Tenant Filter to `ops_card_pg.py`**: Ensure `load_ops_card` includes `WHERE tenant_id = :tenant_id` to prevent cross-tenant data exposure.
4.  **Simplify `payment_risk.py` Logic**: Replace the complex conditional `auto_pi_allowed = False if auto_pi else True` with `not auto_pi`.
5.  **Validate `tender_engine.py` Stage Transitions**: Restrict `won`/`lost` assignments to only come from valid preceding stages (e.g., `negotiation`) rather than allowing arbitrary jumps.
6.  **Add Locking or Atomic Operations**: Implement simple locking in `suppression_list.py` and `sales_collision.py` for check-then-act sequences.

## 机读

- 合并：`docs/ocr-scan-merged.json`
- 各批：`docs/ocr-scan-critical-full.json` 等
