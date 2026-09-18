# OpenCodeReview LLM 扫描报告（关键路径）

- 工具：alibaba/open-code-review **v1.12.5**
- Provider：`{'provider': 'agnes', 'model': 'agnes-2.5-flash'}`
- 状态：`completed_with_errors`（部分子任务因 token 预算/超时未完成）
- 文件评审数：**76**
- 评论数：**48**（high 10 / medium 21 / low 17）
- Token：319723 · 耗时 7m24s · budget_exceeded=True
- Session：`b456c948-56a2-483c-afb8-52e390fccf02`

## 项目摘要（OCR 输出原文）

### Top Issues

1.  **Silent State Loss & Data Corruption in Acquisition Service (`backend/app/services/acquisition/__init__.py`)**
    *   **Race Condition:** `BuyerMasterStore.upsert()` performs a check-then-act on internal dicts without synchronization, leading to duplicate buyer records or lost updates in concurrent environments.
    *   **State Leaks:** Module-level mutable globals (`buyer_store`, `ops_card_store`) retain state across test runs and multi-process deployments with no isolation or cleanup.
    *   **Silent Failure:** A bare `except:` on line 575 swallows `KeyboardInterrupt`, `SystemExit`, and all exceptions. If persistence patches fail, the app continues silently without warning that order follow-up data is not surviving.

2.  **Database Routing & Session Integrity Failures (`backend/app/core/database.py`)**
    *   **Lost Read/Write Splitting:** `rebind_engine()` recreates `SessionLocal` without the `class_=RoutingSession` parameter, defeating the purpose of read replica routing after rebinding.
    *   **Generator Misuse:** `get_redis()` calls `_gr()` without yielding or using it as a context manager. If `_gr` is a generator (common in DI), this returns a generator object instead of the actual Redis client.
    *   **Swallowed Critical Errors:** Bare `pass` in the `_setup_rls_event_listener` exception block discards RLS tenant injection failures. While logged, the silent discard makes it easy to miss that tenant isolation is broken.

3.  **Async Event Loop Blocking (`backend/app/api/v1/routes/acquisition.py`)**
    *   Blocking synchronous code (`dispatch_acquisition`, `ps.decompose`) is called directly in async contexts without `run_in_executor()`. This stalls the asyncio event loop during blocking I/O operations.

4.  **Dev Secret Generation Race Condition & Weak Validation (`backend/app/core/config.py`)**
    *   **Race Condition:** Multiple worker processes starting concurrently can both read an empty dev secret file and generate different secrets, causing JWT inconsistency across the cluster.
    *   **False Positives:** The weak secret check uses substring matching (`if pat in val`), incorrectly flagging strong random secrets containing common words like 'password' or 'key'.
    *   **OS Incompatibility:** `os.chmod(0o600)` is ignored on Windows, leaving dev secrets world-readable.

5.  **Incorrect P95 Latency Calculation (`backend/app/services/acquisition/baseline_bench.py`)**
    *   The P95 index calculation (`int(n * 0.95) - 1`) systematically underestimates latency (e.g., for n=20, it calculates P45 instead of P95). This masks performance regressions in benchmarking.

6.  **Production URL Hardcoding (`backend/app/core/config.py`)**
    *   `HERMES_SITE_PATROL_HTTP_SELF_URL` is hardcoded to `http://127.0.0.1:8001`. This causes Hermes site patrol health checks and alerting to silently fail in any non-local production environment.

7.  **Duplicate Route Registration (`backend/app/api/v1/routes/acquisition.py`)**
    *   `/ops/reconcile` is registered twice. The second handler silently overrides the first, meaning the read-only session fallback logic in the first definition is never used.

8.  **Race Condition in Buyer Store (`backend/app/services/acquisition/__init__.py`)**
    *   `list_by_tenant()` is O(n) per call, iterating all records. Under concurrent load or scale, this degrades performance significantly. An inverted index `_by_tenant` is needed.

### Module Hotspots

*   **`backend/app/api/v1/routes/acquisition.py`**: High density of issues including async blocking, duplicate routes, missing rate limits on sensitive endpoints (`/claim`, `/sanctions/screen`), potential None dereferences (`card.sample.status`), and inconsistent error handling (400 vs 422).
*   **`backend/app/services/acquisition/__init__.py`**: Critical concurrency and state management issues (race conditions, global state leaks, silent exception swallowing).
*   **`backend/app/core/config.py`**: Configuration validation weaknesses and race conditions in dev secret generation.
*   **`backend/app/services/acquisition/billing_explain.py`**: Contradicts its own "honest empty" ethos by silently defaulting missing `success` columns to `True` and swallowing exceptions in meter events.
*   **`backend/app/services/acquisition/dispatch_service.py`**: Bare except clauses masking DB failures, truncated error messages losing debugging context, and unvalidated input parameters.

### Cross-Cutting Concerns

*   **Bare `except:` / `except Exception` with `pass`**: Repeated across `config.py`, `database.py`, `acquisition/__init__.py`, `baseline_bench.py`, `billing_explain.py`, and `dispatch_service.py`. This pattern swallows critical errors (permissions, DB failures, keyboard interrupts) and makes debugging nearly impossible.
    *   *Examples:* `backend/app/services/acquisition/__init__.py:575`, `backend/app/services/acquisition/billing_explain.py` (multiple), `backend/app/services/acquisition/dispatch_service.py:27`.
*   **Missing Input Validation**: Parameters like `intent` and `channel` in `dispatch_service.py` are used without validation, risking downstream errors or malicious events.
*   **Inconsistent Error Handling**: Mixed use of HTTP 400 and 422 for similar failures (`intent_preview` vs `acquisition_dispatch`) confuses API consumers.
*   **Potential None Dereferences**: Multiple paths access attributes on objects that may be None without guards (e.g., `card.buyer_grade`, `card.sample.status`, `_resolve_db(db)` returning None in tests).
    *   *Examples:* `backend/app/api/v1/routes/acquisition.py` (lines 524, sample status), `backend/app/api/v1/routes/acquisition.py` (`reply_ingest`).

### Quick Wins

1.  **Fix P95 Calculation:** Update `baseline_bench.py` to use `min(int(len(lat_ms) * 0.95), len(lat_ms) - 1)` or `math.ceil` for correct percentile indexing.
2.  **Add Rate Limits:** Apply `_rate_limit_or_raise()` to sensitive endpoints `/ops-card/{inquiry_id}/claim`, `/sanctions/screen`, and `/risk-rescan/mark` in `acquisition.py`.
3.  **Validate `intent`/`channel`:** Add basic non-empty and type checks for `IntentEvent` parameters in `dispatch_service.py`.
4.  **Remove Duplicate Route:** Delete the redundant `/ops/reconcile` registration in `acquisition.py` to ensure the correct handler (with read-only session fallback) is used.
5.  **Guard `card` and `sample` Access:** Add `None` checks for `card` and `card.sample` in `acquisition.py` before accessing `buyer_grade`, `stage`, or `status`.
6.  **Make `HERMES_SITE_PATROL_HTTP_SELF_URL` Configurable:** Replace the hardcoded `127.0.0.1:8001` with an environment variable in `config.py`.
7.  **Fix `rebind_engine()`:** Ensure `SessionLocal` is recreated with `class_=RoutingSession` in `database.py` to preserve read/write routing.
8.  **Use `except Exception:` and Log:** Replace bare `except:` clauses in `acquisition/__init__.py`, `billing_explain.py`, and `dispatch_service.py` with `except Exception as e:` and add logging to preserve error context.

## 警告 / 未完成文件

- `backend/app/api/v1/routes/acquisition.py` · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- `backend/app/services/acquisition/experience_feed.py` · token_budget_reached · stopped in batch #0: used 281482 tokens + next-file estimate exceeds budget 250000
- `backend/app/services/acquisition/dispatch_service.py` · scan_subtask_error · main_task did not complete before stopping: reached the aggregate token budget before finishing
- `backend/app/core/login_bruteforce.py` · scan_subtask_error · LLM completion error: context deadline exceeded
- `backend/app/services/acquisition/billing_explain.py` · scan_subtask_error · LLM completion error: context deadline exceeded

## 按文件统计

| 文件 | 评论数 |
|------|------:|
| `backend/app/api/v1/routes/acquisition.py` | 17 |
| `backend/app/services/acquisition/billing_explain.py` | 7 |
| `backend/app/core/config.py` | 5 |
| `backend/app/services/acquisition/__init__.py` | 5 |
| `backend/app/services/acquisition/baseline_bench.py` | 5 |
| `backend/app/services/acquisition/dispatch_service.py` | 5 |
| `backend/app/core/database.py` | 4 |

## 按类别统计

| 类别 | 数量 |
|------|-----:|
| bug | 17 |
| security | 11 |
| maintainability | 9 |
| performance | 6 |
| other | 2 |
| style | 2 |
| documentation | 1 |

## High 级评论（全文）

### `backend/app/api/v1/routes/acquisition.py`:1218-1233 · bug

Duplicate route registration: the endpoint `/ops/reconcile` is registered twice. The first definition (lines 584-590) uses a read-only session fallback, while the second (lines 635-641) directly passes `_resolve_db(db)`. The second handler silently overrides the first, making the first decorator unreachable. The earlier implementation had better read-replica handling.

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
    if sessio
```

### `backend/app/core/config.py`:971-972 · security

Weak secret literal check uses substring matching (`if pat in val`) which causes false positives. For example, a strong random secret containing 'password' (e.g., 'my-password-123-secure-key') or 'key' would incorrectly trigger the production validation failure. Similarly, 'notchangeme' would match 'changeme'. Consider using exact equality checks or a more robust pattern matching approach.

```python
for pat in weak_patterns:
                    if pat in val:
```

### `backend/app/core/database.py`:120-123 · security

The bare `pass` in this except block silently swallows exceptions from `_setup_rls_event_listener()`, which means if RLS tenant injection fails to initialize, the error is logged but the exception is discarded. While there is a warning log, this makes it easier to miss that critical security functionality (RLS tenant isolation) never got registered. Consider re-raising the exception or at minimum using a more explicit handling pattern that doesn't use bare `pass`.

```python
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning("RLS事件监听器初始化失败，继续启动: %s", e)
    pass  # RLS事件监听器初始化失败不应阻塞数据库引擎创建
```

### `backend/app/core/database.py`:145-145 · bug

The `rebind_engine()` function updates `engine`, `SessionLocal`, and `UUID_TYPE`, but it recreates `SessionLocal` without the `class_=RoutingSession` parameter. This means after rebinding, the session no longer supports read/write routing to the read replica, defeating the purpose of the routing session.

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### `backend/app/services/acquisition/__init__.py`:103-141 · other

`BuyerMasterStore.upsert()` performs a check-then-act race on `self._by_email` and `self._by_id` with no synchronization. In a multi-threaded or async context, two concurrent upserts for the same email can both pass the conflict check, resulting in duplicate buyer records or one overwriting the other despite `persona_locked=True`. This breaks the identity lock guarantee the module claims to enforce.

```python
    def upsert(self, buyer: BuyerMaster) -> tuple[BuyerMaster, bool, list[str]]:
        """返回 (buyer, is_new, alerts)。"""
        alerts: list[str] = []
        key = (buyer.tenant_id, (buyer.email or "").lower())
        if key[1]:
            existing_id = self._by_email.get(key)
            if e
```

### `backend/app/services/acquisition/__init__.py`:912-916 · security

Bare `except:` on line 575 swallows KeyboardInterrupt, SystemExit, and all exceptions silently. If the persistence patch import fails (e.g., file missing, syntax error), the error is entirely hidden and the app continues without any warning that order follow-up data will not survive restarts. This violates the explicit hard lock: no fake success. Use `except Exception:` at minimum and log the failure so operators know persistence is degraded.

```python
try:
    from app.services.acquisition.ops_card_pg import patch_store_persistence
    patch_store_persistence(ops_card_store)
except Exception:
    pass
```

### `backend/app/services/acquisition/baseline_bench.py`:49-49 · bug

P95 percentile index calculation is incorrect. For n=20: int(20*0.95)-1 = 8, which gives p45 (index 8 of 20), not p95. The correct ceiling-based index should be `min(int(len(lat_ms) * 0.95), len(lat_ms) - 1)` or use `math.ceil`. This systematically underestimates p95 latency for small sample sizes.

```python
    p95 = lat_ms[int(len(lat_ms) * 0.95) - 1] if len(lat_ms) >= 2 else (lat_ms[0] if lat_ms else 0)
```

### `backend/app/services/acquisition/billing_explain.py`:114-115 · security

Bare `except:` (no exception type) swallows `KeyboardInterrupt` and `SystemExit` in addition to all exceptions. This blocks any ability to diagnose why meter events are missing from the output. Should at minimum use `except Exception:` and log the error.

```python
    except Exception:
        pass
```

### `backend/app/services/acquisition/dispatch_service.py`:41-47 · security

Line 27: Bare except with `pass` silently swallows all exceptions from `resolve_tenant_uuid`, including DB failures, invalid tenant IDs, or connection errors. This masks critical failures and makes debugging impossible. Should at minimum log the exception: `logger.warning(f"Failed to resolve tenant UUID: {exc}", exc_info=True)` and/or re-raise if resolution is essential.

```python
        try:
            from app.services.acquisition.repo import resolve_tenant_uuid
            tid = resolve_tenant_uuid(session, tenant_id)
            if tid:
                resolved_tenant = tid
        except Exception:
            pass
```

### `backend/app/services/acquisition/dispatch_service.py`:90-113 · bug

Lines 75-108: The outer try/except wraps `parse_graph_to_tasks` AND `advance_plan` together, but the inner try only catches `advance_plan` errors. If `parse_graph_to_tasks` fails, it bubbles up to the outer handler and overwrites any partial state. This makes it unclear whether tasks were persisted when an error occurs. Consider separating concerns or documenting the transaction boundary.

```python
    try:
        from app.services.hermes.task_control_supervisor import (
            advance_plan,
            parse_graph_to_tasks,
        )
        node_tasks = parse_graph_to_tasks(session, resolved_tenant, graph)
        plan_task_id = str(getattr(node_tasks[0], "parent_task_id", "")) if node
```


## Medium 级评论（标题级）

- `backend/app/api/v1/routes/acquisition.py`:339 · **performance** · Async function calling blocking synchronous code: `ps.decompose()` is called directly in an async context without `run_in_executor()`. If this function performs
- `backend/app/api/v1/routes/acquisition.py`:600 · **bug** · Potential None dereference: card.sample.status is accessed without null-check on card.sample. If card.sample is None, this will raise AttributeError.
- `backend/app/api/v1/routes/acquisition.py`:790 · **security** · Missing rate limit check on sensitive endpoints: `/ops-card/{inquiry_id}/claim`, `/sanctions/screen`, and `/risk-rescan/mark` modify critical business state but
- `backend/app/api/v1/routes/acquisition.py`:1181 · **bug** · Tender advance conditional logic has operator precedence bug. The expression `out.get('ok') and body.inquiry_id if hasattr(body, 'inquiry_id') else False` evalu
- `backend/app/api/v1/routes/acquisition.py`:1231 · **bug** · Silent exception swallowing in `except Exception` with bare `pass` in the read-session probe. If `get_read_session()` fails, the exception is caught but only th
- `backend/app/api/v1/routes/acquisition.py`:1554 · **bug** · The `reply_ingest` endpoint calls `_resolve_db(db)` which returns None in tests, then passes None to `persist_inquiry` and `persist_prospect_lead`. If these fun
- `backend/app/api/v1/routes/acquisition.py`:1704 · **performance** · Async function calling blocking synchronous code: `dispatch_acquisition()` is called directly in an async context without `run_in_executor()`. If this function 
- `backend/app/core/config.py`:417 · **bug** · HERMES_SITE_PATROL_HTTP_SELF_URL is hardcoded to http://127.0.0.1:8001 which will likely be unreachable or incorrect in production environments. This causes Her
- `backend/app/core/config.py`:1066 · **maintainability** · Bare except clauses in _load_persisted_dev_secret and _persist_dev_secret swallow all exceptions including KeyboardInterrupt and SystemExit. This makes it impos
- `backend/app/core/config.py`:1070 · **security** · The dev secret file persistence has a race condition: multiple worker processes starting concurrently could both read the file, see it empty, and generate diffe
- `backend/app/core/database.py`:60 · **bug** · Inside the `before_cursor_execute` event listener, `logger` is referenced at line 51 but is only defined locally within the `if total_time >= 0.2:` block at lin
- `backend/app/core/database.py`:249 · **bug** · The `get_redis()` function calls `_gr()` but doesn't yield or handle it as a context manager. If `app.core.cache.get_redis()` is a generator function (common fo
- `backend/app/services/acquisition/__init__.py`:154 · **performance** · `list_by_tenant()` iterates all buyer records to filter by tenant_id, making it O(n) per call. Under concurrent load or as the store grows, repeated calls will 
- `backend/app/services/acquisition/__init__.py`:906 · **maintainability** · Module-level mutable globals `buyer_store`, `ops_card_store`, `playbook_store` are created once at import time. Across test runs or in multi-process deployments
- `backend/app/services/acquisition/baseline_bench.py`:36 · **bug** · Bare `except Exception` silently swallows errors without logging. The error counter increments but no traceback or context is preserved, making it impossible to
- `backend/app/services/acquisition/baseline_bench.py`:71 · **bug** · claim_fn return value is assumed to be a dict but no validation exists. If claim_fn returns None or a non-dict type, `.get()` calls will raise AttributeError, c
- `backend/app/services/acquisition/billing_explain.py`:0 · **bug** · The fallback `success=True` silently treats a missing `success` column as a successful acquisition event. This contradicts the module's 'honest empty / no fake 
- `backend/app/services/acquisition/billing_explain.py`:90 · **maintainability** · The token_ledger try block catches all exceptions with only a warning log, which can conceal schema mismatches, `TypeError` from `_reason_plain`, or `ValueError
- `backend/app/services/acquisition/billing_explain.py`:114 · **maintainability** · The module docstring declares a red-line '无账本/无明细诚实 empty，不编流水', yet the meter-events path silently swallows all exceptions and the acquisition path defaults mi
- `backend/app/services/acquisition/dispatch_service.py`:52 · **security** · Lines 28-36: No validation on `intent` or `channel` parameters before constructing `IntentEvent`. Invalid or malformed inputs could produce downstream errors or
- `backend/app/services/acquisition/dispatch_service.py`:105 · **maintainability** · Lines 89, 102: Exception messages are truncated to 200 chars in the result dict, which may lose critical debugging context. While not a security issue, this ham

## Low 级评论（标题级）

- `backend/app/api/v1/routes/acquisition.py`:51 · **maintainability** · Unused import: `from app.core.db_sessions import get_read_session` appears twice (lines 49 and 60), causing a redundant import. Remove the duplicate.
- `backend/app/api/v1/routes/acquisition.py`:60 · **maintainability** · Unused import: `_claim_fn` is imported as alias for `claim_inquiry` but only used in baseline test setup (line ~690). While technically used, importing with an 
- `backend/app/api/v1/routes/acquisition.py`:71 · **other** · Unused variable: `ROUTE_PREFIX = ""` is defined but never referenced anywhere in the file. Remove it to avoid confusion.
- `backend/app/api/v1/routes/acquisition.py`:341 · **documentation** · Type ignore comment suggests known type mismatch: `ps.decompose(ev, db=None)` passes None where a Session might be expected. The type annotation `# type: ignore
- `backend/app/api/v1/routes/acquisition.py`:342 · **style** · Inconsistent error handling: `intent_preview` raises HTTPException(400) for decomposition failures, while `acquisition_dispatch` raises HTTPException(422) for s
- `backend/app/api/v1/routes/acquisition.py`:508 · **performance** · The `loss_stats` and `win_loss_stats` methods are called multiple times with `tenant_id=card.tenant_id` in different endpoints. If these methods perform expensi
- `backend/app/api/v1/routes/acquisition.py`:996 · **bug** · Potential None access: `card.buyer_grade` and `card.stage` are accessed without checking if `card` is None. The `if card is None:` check on line 524 should guar
- `backend/app/api/v1/routes/acquisition.py`:1512 · **performance** · Potential unbounded list accumulation: `tips` list is extended in multiple places without size limits. If playbook tips and intent analysis produce many entries
- `backend/app/api/v1/routes/acquisition.py`:1714 · **security** · String concatenation in exception messages with f-strings could expose sensitive data in logs. Consider sanitizing the exception message before including it.
- `backend/app/core/config.py`:104 · **security** · CORS_ORIGINS property accepts arbitrary JSON arrays from environment variables without validation. While currently safe, untrusted env input could contain compl
- `backend/app/services/acquisition/__init__.py`:0 · **maintainability** · Deferred imports in methods like `fulfillment_view`, `research_gate_view`, `quote_validity_view`, `payment_risk_view`, `win_loss_stats`, `loss_stats`, and `list
- `backend/app/services/acquisition/baseline_bench.py`:16 · **maintainability** · The `make_card` callable parameter has no type validation or documentation about expected signature. If passed incorrectly, it will fail deep in the loop with u
- `backend/app/services/acquisition/baseline_bench.py`:73 · **style** · Using `is False` for comparison with dict values is fragile. If the API returns `ok=False` (boolean False), this works, but if it returns `ok=0` or `ok=None`, t
- `backend/app/services/acquisition/billing_explain.py`:40 · **security** · `_reason_plain` has an early return when `reason` is falsy (`reason or "未知原因"`), but the function also returns raw un-mapped strings unfiltered. If an attacker-
- `backend/app/services/acquisition/billing_explain.py`:73 · **performance** · Each of the three source queries applies `.limit(limit)` independently, then the merged list is again truncated to `items[:limit]`. This means at most 3×limit r
- `backend/app/services/acquisition/billing_explain.py`:147 · **bug** · The `tenant_uuid` variable `tid` is computed but only returned in the dict under key `tenant_uuid`; the callers (e.g., billing endpoints) may expect a `tenant_i
- `backend/app/services/acquisition/dispatch_service.py`:95 · **bug** · Line 44: The comprehension `[str(getattr(t, "id", "")) for t in node_tasks]` will fail with IndexError if `node_tasks` is empty but `plan_task_id` was somehow s

## 与静态检测交叉

- OCR LLM **独立确认**：`/ops/reconcile` 重复路由、大量 except 吞异常、acquisition 异步阻塞、billing_explain 诚实性问题。
- OCR 新发现（静态规则难覆盖）：BuyerMasterStore 竞态与全局状态、`rebind_engine` 丢 RoutingSession、P95 计算错误、`HERMES_SITE_PATROL_HTTP_SELF_URL` 硬编码、敏感端点缺限流、`card.sample` 空引用风险。

## 机读

- 原始：`docs/ocr-scan-critical.json`
- 解析：`docs/ocr-scan-critical-parsed.json`
