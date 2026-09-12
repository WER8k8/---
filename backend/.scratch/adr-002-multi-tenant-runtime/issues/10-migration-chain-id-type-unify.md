# 10 — P0-B：迁移链 ID 类型统一（绿色 PG 部署）✅ 已完成（2026-09-05）

**结果**：空库真 PG `alembic upgrade heads` 001→105 **全绿**（229 表，FK 类型错配 0），
模型 Base.metadata 200 张表全覆盖；活库 youding_dev 已 stamp 到 head；
全量回归 21/21 套 rc=0（含 4 套真 PG 套件）。

## 根因链（比 ticket 初判更深）

不是"17 个迁移硬编码 String(36)"单点问题，实测发现 5 类叠加病灶：

1. **ID 类型三派分裂**：001 `users.id`=PG native uuid（方言感知）；4188869502e0
   `tenants.id`=硬编码 varchar(36)；069 曾为对齐后者把 `_uuid_type()` 硬编码 String(36)。
   模型 canonical = `UUID(as_uuid=False)`（app/core/database.py:get_uuid_column）。
2. **死迁移**：020_add_pgvector 目标表 `content` 不存在（实为 content_pages）、
   float[] 配 ivfflat vector_cosine_ops、`logging` 未 import——任何真 PG 上必炸，
   app 全仓 0 引用 → 改写为守卫式空操作（保留 CREATE EXTENSION vector）。
3. **活库 create_all 掩盖的缺表/缺列**：platforms（040 FK 引用，无迁移建）、
   content_masters（048/052 触碰，无迁移建）、036 add_column 被注释、
   022 建表缺 assigned_to/source_channel、057 复合索引引用 102 才补的列。
4. **迁移顺序错乱**：024 与 069 重复建 deerflow_jobs；100 的 RLS 策略引用
   102 才加的 tenant_id 列；088/089/100 的策略引用绿色库不存在的角色 app_user/service_role。
5. **模型层同病**：Base.metadata 8 处 FK 类型错配（ab_test 5 处 Integer/String(36)
   →uuid、globalization task_id、international site_id/source_site_id）——
   **create_all 在真 PG 空库上同样必炸**（活库是历史侥幸），与迁移链互为镜像。

## 修复清单

- **sweep**：41 个迁移文件 String(36) id 主键/FK 列 → `_uuid_col()`（方言感知，
  PG=native uuid(as_uuid=False)/SQLite=String(36)，与模型 UUID_TYPE 一致），
  含 4 处跨行声明漏网补刀（040/042/043）。
- **foundational**：4188869502e0 的 tenants 全家 24 列 → uuid_col()；
  069 `_uuid_type()` 恢复方言感知。
- **守卫化**：022（补列）、027/036（幂等 index/add）、048（升级为 content_masters
  建表点）、052（幂等 deleted_at）、055（boolean server_default sa.false()）、
  057（列存在守卫）、069（deerflow_jobs if_absent + 拆 `_upgrade_evolution_only`）、
  088/089/100（角色 DO 块幂等预建 + 缺表/缺列跳过）、040（platforms 兜底建表）。
- **模型**：ab_test.py/globalization.py/international.py 8 处 FK → UUID_TYPE。
- **新增 105_reconcile_model_backfill**（down_revision=104）：链尾 Base.metadata.
  create_all 幂等兜底——绿色链 141 表→229 表，模型 200 张全覆盖（仅模型有=0），
  存量库零改动；这是迁移链与 create_all 两条建库路径的合流收口。
- **工具**：scripts/greenchain_p0b_verify.py（可重跑绿色链测量：建临时库→upgrade
  heads→id 类型分布+FK 错配 dump）；tests/idor_tenant_isolation_verify.py 补
  sys.path（cwd 陷阱修复）。
- **活库**：youding_dev alembic_version 080（已删的归档 revision，alembic 无法
  stamp）→ SQL 直改 = `105_reconcile_model_backfill (head)`，零 DDL 触碰。

## 已知挂账（不属本票）

- 共同表 113 列型差异（迁移版 vs 模型版历史漂移：timestamp 时区、json/jsonb、
  varchar/text 等）——存量表 create_all 不改，归 101_align_model_schema 持续工作。
- 29 张仅迁移有的表（模型已删）——留存无害，治理去留另立票。
- idor 套件 D1/D2 DB 纵深 WARN（superuser 绕 RLS）= T05 既有挂账，非本票回归。

## 验证证据（2026-09-05 本轮实测）

- `python scripts/greenchain_p0b_verify.py` → `[PASS] 绿色链 001→heads 全绿`
  + `uuid 表 134 张（+backfill 后 229 表）` + `FK 类型错配：0 处`
- 21/21 verify 套件 rc=0（idor 应用层 A1-A5 全 PASS）
- 备份：`backend/_archive/versions-backup-20260905-P0B/`（80 文件改前快照）

**Status:** done（2026-09-05）

- [x] canonical id 类型 = 原生 UUID（对齐模型 UUID_TYPE，as_uuid=False）
- [x] sweep String(36)→uuid_col()（41 文件 + 跨行漏网 4 处）
- [x] 空库 `alembic upgrade heads` 001→105 全绿（真 PG youding-dev-postgres:5433）
- [x] 模型 8 处 FK 错配清零（create_all 真 PG 从必炸变可用）
- [x] youding_dev stamp → head，alembic current 对齐
