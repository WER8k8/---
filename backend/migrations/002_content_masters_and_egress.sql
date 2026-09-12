-- =====================================================
-- 统一发布母版 + 静态IP槽位 + 浏览器指纹: 数据库迁移
-- 兼容 PostgreSQL / SQLite
-- =====================================================

-- === 1. 内容母版表 ===
CREATE TABLE IF NOT EXISTS content_masters (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    body TEXT,
    media_urls TEXT DEFAULT '[]',  -- JSON array
    content_type VARCHAR(30) DEFAULT 'article',  -- article | video_script
    tenant_canonical_url VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'draft',  -- draft | ready | published
    hub_slug VARCHAR(200),
    hub_summary TEXT,
    show_on_hub BOOLEAN DEFAULT TRUE,
    hub_published_at TIMESTAMP WITH TIME ZONE,
    created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_content_masters_tenant_id ON content_masters(tenant_id);
CREATE INDEX IF NOT EXISTS idx_content_masters_status ON content_masters(status);
CREATE INDEX IF NOT EXISTS idx_content_masters_hub_slug ON content_masters(hub_slug);

-- === 2. 静态IP槽位表 ===
CREATE TABLE IF NOT EXISTS egress_endpoints (
    id TEXT PRIMARY KEY,
    region VARCHAR(20) NOT NULL,  -- cn | global
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 0,
    provider VARCHAR(100),
    slot_status VARCHAR(20) DEFAULT 'available',  -- available | assigned | disabled
    tenant_id TEXT REFERENCES tenants(id) ON DELETE SET NULL,
    label VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_egress_endpoints_region ON egress_endpoints(region);
CREATE INDEX IF NOT EXISTS idx_egress_endpoints_tenant_id ON egress_endpoints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_egress_endpoints_status ON egress_endpoints(slot_status);

-- === 3. 浏览器指纹配置表 ===
CREATE TABLE IF NOT EXISTS browser_profiles (
    id TEXT PRIMARY KEY,
    tenant_id TEXT REFERENCES tenants(id) ON DELETE SET NULL,
    egress_endpoint_id TEXT REFERENCES egress_endpoints(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    fingerprint TEXT DEFAULT '{}',  -- JSON object
    platform_account_id TEXT,  -- 可选关联平台账号
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_browser_profiles_tenant_id ON browser_profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_browser_profiles_egress ON browser_profiles(egress_endpoint_id);

-- === 4. 确保 publish_tasks 表有 content_master_id 字段 ===
-- (如果已存在则跳过，兼容现有数据)
-- PostgreSQL:
-- ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS content_master_id TEXT REFERENCES content_masters(id) ON DELETE SET NULL;
-- ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS primary_url VARCHAR(1000);
-- ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS secondary_url VARCHAR(1000);

-- SQLite (手动执行，SQLite不支持IF NOT EXISTS for columns):
-- ALTER TABLE publish_tasks ADD COLUMN content_master_id TEXT;
-- ALTER TABLE publish_tasks ADD COLUMN primary_url TEXT;
-- ALTER TABLE publish_tasks ADD COLUMN secondary_url TEXT;
