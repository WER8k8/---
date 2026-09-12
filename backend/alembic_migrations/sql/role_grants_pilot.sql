-- ============================================================
-- 生产角色映射 + ALTER DEFAULT PRIVILEGES（总纲 §8 / 轮 25-A 收口）
-- 幂等：可重复执行。PG 15 / uj_test。
--
-- 模型：
--   postgres      = 迁移/DDL 属主（alembic 用），保持现状
--   app_user      = 业务应用运行时角色（NOLOGIN，会话内 SET ROLE 进入），
--                   233 张表的 DML 精确授权，无 DDL，无 TRUNCATE
--   service_role  = 后台服务/对账角色（NOLOGIN），全量 DML + TRUNCATE
--
-- 收窄动作：
--   1. REVOKEPUBLIC.schema  ：public schema 的 CREATE 收回（防任意建表）
--   2. REVOKEPUBLIC.tables  ：PUBLIC 对全部表的隐式授权收回
--   3. GRANT 精确表级权限    ：app_user 去 TRUNCATE/REFERENCES，
--                              service_role 保留 TRUNCATE（对账重载用）
--   4. ALTER DEFAULT PRIVILEGES：未来 postgres 新建的表/序列/函数
--      自动带正确授权（新表无需手工 GRANT）
-- ============================================================

-- ---- 0. 角色存在性（幂等 DO 块） ----
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
END
$$;

-- ---- 1. public schema：收回 PUBLIC 的 CREATE（保留 USAGE） ----
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO app_user, service_role;

-- ---- 2. 存量表：收回 PUBLIC 隐式授权，再做精确授权 ----
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;

-- app_user：业务 DML（无 TRUNCATE / 无 REFERENCES / 无 DDL）
-- 先显式 REVOKE 残留权限（GRANT 是累加的，必须先收窄再授）
REVOKE TRUNCATE, REFERENCES ON ALL TABLES IN SCHEMA public FROM app_user;
GRANT SELECT, INSERT, UPDATE, DELETE, TRIGGER ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- service_role：全量 DML + TRUNCATE（对账重载）
GRANT SELECT, INSERT, UPDATE, DELETE, TRIGGER, TRUNCATE ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ---- 3. ALTER DEFAULT PRIVILEGES（postgres 属主新建对象自动授权） ----
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON SEQUENCES FROM PUBLIC;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE, TRIGGER ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE, TRIGGER, TRUNCATE ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO service_role;

-- ---- 4. 数据库连接权（NOLOGIN 角色仍需 CONNECT 供 SET ROLE 前置校验） ----
GRANT CONNECT ON DATABASE uj_test TO app_user, service_role;
