-- =====================================================
-- 超级管理员后台: 数据库迁移 + 种子数据
-- 兼容 PostgreSQL / SQLite (SQLite 时需忽略 JSONB 等 PG 特有语法)
-- =====================================================

-- === 1. 管理员角色表 ===
CREATE TABLE IF NOT EXISTS admin_roles (
    id TEXT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === 2. 权限码表 ===
CREATE TABLE IF NOT EXISTS admin_permissions (
    id TEXT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    group_name VARCHAR(50),
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- === 3. 角色-权限关联表 ===
CREATE TABLE IF NOT EXISTS role_permissions (
    id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL REFERENCES admin_roles(id) ON DELETE CASCADE,
    permission_id TEXT NOT NULL REFERENCES admin_permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_perm ON role_permissions(permission_id);

-- === 4. 后台菜单表 ===
CREATE TABLE IF NOT EXISTS admin_menus (
    id TEXT PRIMARY KEY,
    parent_id TEXT REFERENCES admin_menus(id),
    title VARCHAR(50) NOT NULL,
    icon VARCHAR(50),
    path VARCHAR(200),
    permission_code VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    visible BOOLEAN DEFAULT TRUE NOT NULL,
    component_path VARCHAR(300),
    meta_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_menus_parent ON admin_menus(parent_id);
CREATE INDEX IF NOT EXISTS idx_admin_menus_perm ON admin_menus(permission_code);

-- === 5. CC Switch 中转配置表 ===
CREATE TABLE IF NOT EXISTS cc_switch_configs (
    id TEXT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(30) NOT NULL DEFAULT 'cc_switch',
    base_url VARCHAR(300) NOT NULL,
    api_key_encrypted TEXT,
    model_mapping TEXT DEFAULT '{}',
    rate_limit VARCHAR(10) DEFAULT '60',
    rate_window_seconds VARCHAR(10) DEFAULT '60',
    max_retries VARCHAR(10) DEFAULT '3',
    timeout_seconds VARCHAR(10) DEFAULT '30',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    health_check_url VARCHAR(300),
    last_health_status VARCHAR(20),
    last_health_check_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cc_switch_active ON cc_switch_configs(is_active);

-- === 6. 超管登录日志表 ===
CREATE TABLE IF NOT EXISTS super_admin_login_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    username VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    success BOOLEAN DEFAULT TRUE NOT NULL,
    fail_reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sa_login_logs_user ON super_admin_login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_sa_login_logs_time ON super_admin_login_logs(created_at);

-- === 7. users 表扩展 (如果列不存在则添加) ===
-- PostgreSQL:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id TEXT REFERENCES admin_roles(id);
-- SQLite: 需要应用层检查，此处跳过

-- =====================================================
-- 种子数据
-- =====================================================

-- 超级管理员角色
INSERT OR IGNORE INTO admin_roles (id, name, description, is_system, sort_order)
VALUES ('role-super-admin-001', 'super_admin', '超级管理员（系统内置）', TRUE, 0);

INSERT OR IGNORE INTO admin_roles (id, name, description, is_system, sort_order)
VALUES ('role-seo-admin-001', 'seo_admin', 'SEO管理员', TRUE, 1);

INSERT OR IGNORE INTO admin_roles (id, name, description, is_system, sort_order)
VALUES ('role-editor-001', 'editor', '内容编辑', TRUE, 2);

INSERT OR IGNORE INTO admin_roles (id, name, description, is_system, sort_order)
VALUES ('role-viewer-001', 'viewer', '只读访客', TRUE, 3);

-- 权限码
INSERT OR IGNORE INTO admin_permissions (id, code, name, group_name) VALUES
('perm-dashboard',    'dashboard:read',        '控制台大盘-查看',   'dashboard'),
('perm-dashboard-ai', 'dashboard:ai_stats',     'AI调用统计-查看',   'dashboard'),
('perm-users-read',   'users:read',             '用户管理-查看',     'users'),
('perm-users-write',  'users:write',            '用户管理-编辑',     'users'),
('perm-roles-read',   'roles:read',             '角色管理-查看',     'roles'),
('perm-roles-write',  'roles:write',            '角色管理-编辑',     'roles'),
('perm-menus-read',   'menus:read',             '菜单管理-查看',     'menus'),
('perm-menus-write',  'menus:write',            '菜单管理-编辑',     'menus'),
('perm-logs-read',    'logs:read',              '操作日志-查看',     'logs'),
('perm-config-read',  'config:read',            '系统配置-查看',     'config'),
('perm-config-write', 'config:write',           '系统配置-编辑',     'config'),
('perm-ai-read',      'ai:read',               'AI配置-查看',       'ai'),
('perm-ai-write',     'ai:write',              'AI配置-编辑',       'ai'),
('perm-ai-kb',        'ai:knowledge_base',     '知识库管理',        'ai'),
('perm-ai-langchain', 'ai:langchain',          'LangChain控制台',   'ai'),
('perm-ai-ccswitch',  'ai:cc_switch',          'CC Switch配置',     'ai'),
('perm-business',     'business:all',          '业务功能区-全部',    'business'),
('perm-monitor-read', 'monitor:read',          '系统监控-查看',     'monitor'),
('perm-monitor-write','monitor:write',         '系统监控-操作',     'monitor'),
('perm-cache-manage', 'cache:manage',          '缓存管理',          'tools'),
('perm-data-export',  'data:export',           '数据导入导出',      'tools'),
('perm-seo-all',      'seo:*',                 'SEO全部功能',       'seo'),
('perm-content-all',  'content:*',             '内容管理全部',      'content'),
('perm-products-all', 'products:*',            '产品管理全部',      'products');

-- 为 super_admin 角色分配所有权限
INSERT OR IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT
    'rp-sa-' || ap.id,
    'role-super-admin-001',
    ap.id
FROM admin_permissions ap
WHERE NOT EXISTS (
    SELECT 1 FROM role_permissions rp2
    WHERE rp2.role_id = 'role-super-admin-001' AND rp2.permission_id = ap.id
);

-- 为 seo_admin 分配 SEO 相关权限
INSERT OR IGNORE INTO role_permissions (id, role_id, permission_id)
SELECT
    'rp-seo-' || ap.id,
    'role-seo-admin-001',
    ap.id
FROM admin_permissions ap
WHERE ap.code IN (
    'dashboard:read', 'seo:*', 'content:*', 'ai:read', 'ai:knowledge_base',
    'ai:langchain', 'logs:read', 'config:read'
)
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp2
    WHERE rp2.role_id = 'role-seo-admin-001' AND rp2.permission_id = ap.id
);

-- 菜单种子数据
INSERT OR IGNORE INTO admin_menus (id, parent_id, title, icon, path, permission_code, sort_order, meta_json) VALUES
-- 控制台大盘
('menu-dashboard', NULL, '控制台大盘', 'dashboard', '/admin/dashboard', 'dashboard:read', 0, '{"badge":""}'),
('menu-dashboard-ai', 'menu-dashboard', 'AI调用看板', 'chart', '/admin/dashboard/ai-usage', 'dashboard:ai_stats', 1, '{}'),
('menu-dashboard-status', 'menu-dashboard', '系统运行状态', 'server', '/admin/dashboard/system-status', 'dashboard:read', 2, '{}'),

-- 权限管理
('menu-permissions', NULL, '权限管理', 'safety', '/admin/permissions', 'users:read', 10, '{}'),
('menu-users', 'menu-permissions', '管理员用户', 'user', '/admin/permissions/users', 'users:read', 0, '{}'),
('menu-roles', 'menu-permissions', '角色管理', 'team', '/admin/permissions/roles', 'roles:read', 1, '{}'),
('menu-login-logs', 'menu-permissions', '登录日志', 'file-text', '/admin/permissions/login-logs', 'logs:read', 2, '{}'),

-- 系统配置
('menu-config', NULL, '系统配置', 'setting', '/admin/config', 'config:read', 20, '{}'),
('menu-config-basic', 'menu-config', '基础参数', 'info-circle', '/admin/config/basic', 'config:read', 0, '{}'),
('menu-config-security', 'menu-config', '安全配置', 'lock', '/admin/config/security', 'config:write', 1, '{}'),

-- AI 管理
('menu-ai', NULL, 'AI 管理', 'robot', '/admin/ai', 'ai:read', 30, '{}'),
('menu-ai-knowledge', 'menu-ai', '知识库', 'book', '/admin/ai/knowledge', 'ai:knowledge_base', 0, '{}'),
('menu-ai-models', 'menu-ai', '模型池', 'cluster', '/admin/ai/models', 'ai:read', 1, '{}'),
('menu-ai-langchain', 'menu-ai', 'LangChain 控制台', 'code', '/admin/ai/langchain', 'ai:langchain', 2, '{}'),
('menu-ai-ccswitch', 'menu-ai', 'CC Switch 中转', 'swap', '/admin/ai/cc-switch', 'ai:cc_switch', 3, '{}'),

-- 业务功能区
('menu-business', NULL, '业务功能区', 'appstore', '/admin/business', 'business:all', 40, '{}'),
('menu-biz-seo', 'menu-business', 'SEO 优化', 'search', '/admin/business/seo', 'seo:*', 0, '{}'),
('menu-biz-content', 'menu-business', '内容管理', 'file', '/admin/business/content', 'content:*', 1, '{}'),
('menu-biz-products', 'menu-business', '产品管理', 'shop', '/admin/business/products', 'products:*', 2, '{}'),
('menu-biz-cases', 'menu-business', '案例中心', 'picture', '/admin/business/cases', 'business:all', 3, '{}'),
('menu-biz-news', 'menu-business', '新闻管理', 'read', '/admin/business/news', 'business:all', 4, '{}'),
('menu-biz-inquiries', 'menu-business', '询盘管理', 'mail', '/admin/business/inquiries', 'business:all', 5, '{}'),

-- 工具运维
('menu-tools', NULL, '工具运维', 'tool', '/admin/tools', 'monitor:read', 50, '{}'),
('menu-tools-cache', 'menu-tools', '缓存管理', 'database', '/admin/tools/cache', 'cache:manage', 0, '{}'),
('menu-tools-data', 'menu-tools', '数据导入导出', 'export', '/admin/tools/import-export', 'data:export', 1, '{}'),
('menu-tools-logs', 'menu-tools', '操作日志', 'audit', '/admin/tools/logs', 'logs:read', 2, '{}'),
('menu-tools-monitor', 'menu-tools', '系统监控', 'dashboard', '/admin/tools/monitor', 'monitor:read', 3, '{}');
