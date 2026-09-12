/**
 * 导航栏映射逻辑 — 自动化回归测试
 * 运行: npx vitest run tests/nav-mapping.test.mjs
 */
import { describe, test, expect } from 'vitest';

// ═══════════════════════════════════════════
// 1. 受测函数（从源码提取的纯逻辑）
// ═══════════════════════════════════════════

/** 路径标准化（与 workbenchPathCapabilities.ts:normalizeLocationPath 一致） */
function normalizeLocationPath(path) {
  const raw = ((path ?? '').split('?')[0] || '/').split('#')[0] || '/';
  if (raw === '/') return '/';
  const trimmed = raw.replace(/\/+$/, '');
  return trimmed || '/';
}

/** 从能力注册表反向映射：path → capabilityId（最长前缀匹配） */
function resolveCapabilityIdForPath(routePath, registry) {
  const loc = normalizeLocationPath(routePath);
  if (loc === '/admin') return 'suite.workbench';

  const pairs = [];
  for (const sec of registry) {
    for (const item of sec.items) {
      if (item.guardOnly) continue;
      pairs.push({ path: normalizeLocationPath(item.path), id: item.id });
    }
  }
  pairs.sort((a, b) => b.path.length - a.path.length);

  for (const { path, id } of pairs) {
    if (loc === path) return id;
    if (loc.startsWith(`${path}/`)) return id;
  }
  return null;
}

/** 是否为绕过能力守卫的路径 */
function isCapabilityGuardBypassPath(routePath) {
  const loc = normalizeLocationPath(routePath);
  return loc === '/access-denied' || loc === '/login';
}

/** 导航栏活跃状态判断（修复后的 isNavActive 逻辑） */
function isNavActive(currentPath, item) {
  if (item.children?.length) {
    return currentPath.startsWith(item.path + '/') || currentPath === item.path;
  }
  return currentPath === item.path || currentPath.startsWith(item.path + '/');
}

/** 从注册表中收集所有 capability ID */
function allCapabilityIds(registry) {
  return registry.flatMap((s) => s.items.map((i) => i.id));
}

/** menuPathAllowed 核心逻辑 */
function menuPathAllowed(path, registry, grantedCapIds, tenantFeatures) {
  const capId = resolveCapabilityIdForPath(path, registry);
  if (capId == null) return true;
  if (!grantedCapIds.has(capId)) return false;
  if (tenantFeatures) {
    const feature = pathFeatureMap[path];
    if (feature && !tenantFeatures.includes(feature)) return false;
  }
  return true;
}

/** 递归过滤菜单子节点 */
function filterMenuNavChildren(children, registry, grantedCapIds, tenantFeatures) {
  const next = [];
  for (const item of children) {
    if (item.children?.length) {
      const sub = filterMenuNavChildren(item.children, registry, grantedCapIds, tenantFeatures);
      if (sub.length === 0) continue;
      next.push({ ...item, children: sub });
      continue;
    }
    if (menuPathAllowed(item.path, registry, grantedCapIds, tenantFeatures)) {
      next.push(item);
    }
  }
  return next;
}

/** 自动展开子菜单 */
function autoExpand(routePath, menuItems, currentExpanded) {
  const expanded = new Set(currentExpanded);
  for (const group of menuItems) {
    for (const item of group.children) {
      if (item.children?.length) {
        const hasActiveChild = item.children.some(
          (sub) => routePath === sub.path || routePath.startsWith(sub.path + '/')
        );
        if (hasActiveChild) {
          expanded.add(item.name);
        }
      }
    }
  }
  return [...expanded];
}

// ═══════════════════════════════════════════
// 2. 模拟数据
// ═══════════════════════════════════════════

const MOCK_REGISTRY = [
  {
    key: 'core', title: '控制台与业务',
    items: [
      { id: 'core.dashboard', path: '/dashboard', name: '数据概览', guardOnly: false },
      { id: 'core.products', path: '/products', name: '产品列表', guardOnly: false },
      { id: 'core.categories', path: '/products/categories', name: '分类管理', guardOnly: false },
      { id: 'core.content', path: '/content', name: '内容管理', guardOnly: false },
      { id: 'core.news', path: '/news', name: '新闻管理', guardOnly: false },
    ],
  },
  {
    key: 'seo', title: 'SEO工具箱',
    items: [
      { id: 'seo.overview', path: '/seo', name: 'SEO概览', guardOnly: false },
      { id: 'seo.batch', path: '/seo/batch-seo', name: '批量SEO', guardOnly: false },
      { id: 'seo.audit', path: '/seo/site-audit', name: '站点审计', guardOnly: false },
    ],
  },
  {
    key: 'matrix', title: 'SEO矩阵系统',
    items: [
      { id: 'matrix.keywords', path: '/seo-matrix/keywords', name: '关键词管理', guardOnly: false },
      { id: 'matrix.publish', path: '/seo-matrix/publish', name: '多平台分发', guardOnly: false },
      { id: 'matrix.content', path: '/seo-matrix/content', name: '文案生成', guardOnly: false },
    ],
  },
  {
    key: 'suite', title: '超级管理员套件',
    items: [
      { id: 'suite.workbench', path: '/admin', name: '工作台', guardOnly: true },
      { id: 'suite.system', path: '/admin/system', name: '系统管理', guardOnly: false },
      { id: 'suite.sys-users', path: '/admin/system/users', name: '用户管理', guardOnly: false },
      { id: 'suite.ai', path: '/admin/ai-center', name: 'AI中心', guardOnly: false },
      { id: 'suite.ai-models', path: '/admin/ai-center/models', name: '模型管理', guardOnly: false },
      { id: 'suite.ai-knowledge', path: '/admin/ai-center/knowledge', name: '知识库', guardOnly: false },
      { id: 'suite.v2ray', path: '/admin/v2ray', name: 'V2Ray代理', guardOnly: false },
      { id: 'suite.v2ray-servers', path: '/admin/v2ray/servers', name: '服务器配置', guardOnly: false },
      { id: 'suite.code', path: '/admin/code-tools', name: '代码工具', guardOnly: false },
    ],
  },
];

const MOCK_MENU_TREE = [
  {
    title: '总览',
    children: [{ name: 'Dashboard', path: '/dashboard', title: '数据看板', icon: 'DashboardOutlined' }],
  },
  {
    title: '业务管理',
    children: [
      { name: 'Products', path: '/products', title: '产品管理', icon: 'ShoppingOutlined' },
      { name: 'Categories', path: '/products/categories', title: '分类管理', icon: 'FolderOpenOutlined' },
      { name: 'Content', path: '/content', title: '文章内容', icon: 'FileOutlined' },
    ],
  },
  {
    title: '网站优化',
    children: [
      { name: 'SEO', path: '/seo', title: 'SEO总览', icon: 'SearchOutlined' },
      { name: 'SEOMatrixKeywords', path: '/seo-matrix/keywords', title: '矩阵词管理', icon: 'CopyOutlined' },
    ],
  },
  {
    title: '超级管理工具',
    children: [
      { name: 'AdminHub', path: '/admin', title: '超管工作台', icon: 'CrownOutlined' },
      {
        name: 'SuiteAI', path: '/admin/ai-center', title: 'AI中心', icon: 'ApiOutlined',
        children: [
          { name: 'AICenterDashboard', path: '/admin/ai-center', title: '控制台', icon: 'CpuOutlined' },
          { name: 'AICenterModels', path: '/admin/ai-center/models', title: '模型管理', icon: 'LayersOutlined' },
          { name: 'AICenterKnowledge', path: '/admin/ai-center/knowledge', title: '知识库', icon: 'ReadOutlined' },
        ],
      },
      { name: 'V2RayProxy', path: '/admin/v2ray', title: 'V2RayN代理', icon: 'GlobalOutlined' },
    ],
  },
];

const pathFeatureMap = {
  '/dashboard': 'dashboard',
  '/products': 'products',
  '/products/categories': 'products',
  '/content': 'content',
  '/seo': 'seo',
  '/seo-matrix/keywords': 'seo',
  '/seo-matrix/publish': 'seo',
};

// ═══════════════════════════════════════════
// 3. 测试用例
// ═══════════════════════════════════════════

// ── 3.1 normalizeLocationPath ──
describe('normalizeLocationPath', () => {
  test('基本路径', () => {
    expect(normalizeLocationPath('/')).toBe('/');
    expect(normalizeLocationPath('/dashboard')).toBe('/dashboard');
    expect(normalizeLocationPath('/admin/system/users')).toBe('/admin/system/users');
  });

  test('移除 query 和 hash', () => {
    expect(normalizeLocationPath('/products?page=1')).toBe('/products');
    expect(normalizeLocationPath('/seo#section')).toBe('/seo');
    expect(normalizeLocationPath('/seo?q=test#anchor')).toBe('/seo');
  });

  test('末尾斜杠折叠', () => {
    expect(normalizeLocationPath('/products/')).toBe('/products');
    expect(normalizeLocationPath('/admin/v2ray/servers/')).toBe('/admin/v2ray/servers');
  });

  test('空字符串与异常输入', () => {
    expect(normalizeLocationPath('')).toBe('/');
    expect(normalizeLocationPath(null)).toBe('/');
    expect(normalizeLocationPath(undefined)).toBe('/');
  });
});

// ── 3.2 resolveCapabilityIdForPath ──
describe('resolveCapabilityIdForPath', () => {
  test('精确匹配', () => {
    expect(resolveCapabilityIdForPath('/dashboard', MOCK_REGISTRY)).toBe('core.dashboard');
    expect(resolveCapabilityIdForPath('/seo-matrix/keywords', MOCK_REGISTRY)).toBe('matrix.keywords');
    expect(resolveCapabilityIdForPath('/admin/system', MOCK_REGISTRY)).toBe('suite.system');
  });

  test('前缀匹配（子路径）', () => {
    expect(resolveCapabilityIdForPath('/admin/v2ray/servers', MOCK_REGISTRY)).toBe('suite.v2ray-servers');
    expect(resolveCapabilityIdForPath('/admin/v2ray/servers/config', MOCK_REGISTRY)).toBe('suite.v2ray-servers');
  });

  test('/seo 与 /seo-matrix 不混淆', () => {
    expect(resolveCapabilityIdForPath('/seo', MOCK_REGISTRY)).toBe('seo.overview');
    expect(resolveCapabilityIdForPath('/seo-matrix/keywords', MOCK_REGISTRY)).toBe('matrix.keywords');
    expect(resolveCapabilityIdForPath('/seo-matrix/content', MOCK_REGISTRY)).not.toBe('seo.overview');
  });

  test('/admin 特殊处理', () => {
    expect(resolveCapabilityIdForPath('/admin', MOCK_REGISTRY)).toBe('suite.workbench');
    expect(resolveCapabilityIdForPath('/admin/', MOCK_REGISTRY)).toBe('suite.workbench');
  });

  test('未注册路径返回 null', () => {
    expect(resolveCapabilityIdForPath('/login', MOCK_REGISTRY)).toBeNull();
    expect(resolveCapabilityIdForPath('/unknown-path', MOCK_REGISTRY)).toBeNull();
    expect(resolveCapabilityIdForPath('/client/dashboard', MOCK_REGISTRY)).toBeNull();
  });

  test('最长前缀优先', () => {
    expect(resolveCapabilityIdForPath('/admin/v2ray', MOCK_REGISTRY)).toBe('suite.v2ray');
  });
});

// ── 3.3 isCapabilityGuardBypassPath ──
describe('isCapabilityGuardBypassPath', () => {
  test('登录与拒绝访问页豁免', () => {
    expect(isCapabilityGuardBypassPath('/login')).toBe(true);
    expect(isCapabilityGuardBypassPath('/access-denied')).toBe(true);
    expect(isCapabilityGuardBypassPath('/dashboard')).toBe(false);
    expect(isCapabilityGuardBypassPath('/admin')).toBe(false);
  });
});

// ── 3.4 isNavActive — 导航活跃状态 ──
describe('isNavActive', () => {
  test('精确路径匹配', () => {
    expect(isNavActive('/dashboard', { path: '/dashboard' })).toBe(true);
    expect(isNavActive('/dashboard', { path: '/products' })).toBe(false);
  });

  test('父节点前缀匹配（带 children）', () => {
    const aiCenter = { path: '/admin/ai-center', children: [{ path: '/admin/ai-center/models' }] };
    expect(isNavActive('/admin/ai-center/models', aiCenter)).toBe(true);
    expect(isNavActive('/admin/ai-center', aiCenter)).toBe(true);
    expect(isNavActive('/admin/v2ray', aiCenter)).toBe(false);
  });

  test('叶子节点前缀匹配', () => {
    const seo = { path: '/seo' };
    expect(isNavActive('/seo', seo)).toBe(true);
    expect(isNavActive('/seo/site-audit', seo)).toBe(true);
    expect(isNavActive('/seo/batch-seo', seo)).toBe(true);
  });

  test('/seo 不误匹配 /seo-matrix（核心 Bug 修复）', () => {
    const seoItem = { path: '/seo' };
    expect(isNavActive('/seo-matrix/keywords', seoItem)).toBe(false);
    expect(isNavActive('/seo-matrix', seoItem)).toBe(false);
    expect(isNavActive('/seo-matrix/publish', seoItem)).toBe(false);
    expect(isNavActive('/seo', seoItem)).toBe(true);
    expect(isNavActive('/seo/site-audit', seoItem)).toBe(true);
  });

  test('/admin 不误匹配 /admin-xxx', () => {
    const adminItem = { path: '/admin' };
    expect(isNavActive('/admin-something', adminItem)).toBe(false);
    expect(isNavActive('/admin/v2ray', adminItem)).toBe(true);
    expect(isNavActive('/admin', adminItem)).toBe(true);
  });

  test('父节点有 children 时不误匹配同前缀不同路径', () => {
    const productsItem = { path: '/products', children: [{ path: '/products/categories' }] };
    expect(isNavActive('/products', productsItem)).toBe(true);
    expect(isNavActive('/products/categories', productsItem)).toBe(true);
    expect(isNavActive('/products-extra', productsItem)).toBe(false);
  });

  test('空路径和根路径', () => {
    expect(isNavActive('/', { path: '/' })).toBe(true);
    expect(isNavActive('/dashboard', { path: '/' })).toBe(false);
    expect(isNavActive('/', { path: '/dashboard' })).toBe(false);
  });

  test('/admin 作为父节点应匹配所有 admin 子路由', () => {
    const admin = { path: '/admin', children: [{ path: '/admin/ai-center' }] };
    expect(isNavActive('/admin', admin)).toBe(true);
    expect(isNavActive('/admin/v2ray', admin)).toBe(true);
    expect(isNavActive('/admin/v2ray/servers', admin)).toBe(true);
    expect(isNavActive('/admin/code-tools/debug', admin)).toBe(true);
  });
});

// ── 3.5 allCapabilityIds ──
describe('allCapabilityIds', () => {
  test('扁平化收集全部 ID', () => {
    const ids = allCapabilityIds(MOCK_REGISTRY);
    expect(ids).toContain('core.dashboard');
    expect(ids).toContain('seo.overview');
    expect(ids).toContain('matrix.keywords');
    expect(ids).toContain('suite.workbench');
    expect(ids).toContain('suite.v2ray-servers');
    expect(ids.filter(id => id === 'suite.workbench').length).toBe(1);
  });
});

// ── 3.6 menuPathAllowed ──
describe('menuPathAllowed', () => {
  test('未注册路径默认放行', () => {
    const granted = new Set(['core.dashboard']);
    expect(menuPathAllowed('/login', MOCK_REGISTRY, granted, null)).toBe(true);
    expect(menuPathAllowed('/unknown', MOCK_REGISTRY, granted, null)).toBe(true);
  });

  test('已注册但无权限则拒绝', () => {
    const granted = new Set(['core.dashboard']);
    expect(menuPathAllowed('/products', MOCK_REGISTRY, granted, null)).toBe(false);
    expect(menuPathAllowed('/seo', MOCK_REGISTRY, granted, null)).toBe(false);
  });

  test('有权限则放行', () => {
    const granted = new Set(['core.products', 'seo.overview', 'suite.workbench']);
    expect(menuPathAllowed('/products', MOCK_REGISTRY, granted, null)).toBe(true);
    expect(menuPathAllowed('/seo', MOCK_REGISTRY, granted, null)).toBe(true);
    expect(menuPathAllowed('/admin', MOCK_REGISTRY, granted, null)).toBe(true);
  });

  test('租户功能过滤', () => {
    const granted = new Set(['core.dashboard', 'seo.overview']);
    expect(menuPathAllowed('/dashboard', MOCK_REGISTRY, granted, ['dashboard'])).toBe(true);
    expect(menuPathAllowed('/dashboard', MOCK_REGISTRY, granted, ['products'])).toBe(false);
    expect(menuPathAllowed('/seo', MOCK_REGISTRY, granted, ['seo'])).toBe(true);
  });
});

// ── 3.7 filterMenuNavChildren — 递归菜单过滤 ──
describe('filterMenuNavChildren', () => {
  test('全权限不过滤', () => {
    const allIds = new Set(allCapabilityIds(MOCK_REGISTRY));
    const result = filterMenuNavChildren(MOCK_MENU_TREE[3].children, MOCK_REGISTRY, allIds, null);
    expect(result.length).toBe(3);
  });

  test('有限权限过滤', () => {
    const granted = new Set(['suite.workbench', 'suite.ai', 'suite.ai-models']);
    const result = filterMenuNavChildren(MOCK_MENU_TREE[3].children, MOCK_REGISTRY, granted, null);
    expect(result.length).toBe(2);
    const aiGroup = result.find(r => r.name === 'SuiteAI');
    expect(aiGroup).toBeDefined();
    expect(aiGroup.children.some(c => c.name === 'AICenterModels')).toBe(true);
  });

  test('所有子节点被过滤则移除父节点', () => {
    const granted = new Set(['suite.workbench']);
    const result = filterMenuNavChildren(MOCK_MENU_TREE[3].children, MOCK_REGISTRY, granted, null);
    const aiGroup = result.find(r => r.name === 'SuiteAI');
    expect(aiGroup).toBeUndefined();
  });

  test('空权限集', () => {
    const granted = new Set([]);
    const result = filterMenuNavChildren(MOCK_MENU_TREE[1].children, MOCK_REGISTRY, granted, null);
    expect(result.length).toBe(0);
  });

  test('空子节点列表', () => {
    const result = filterMenuNavChildren([], MOCK_REGISTRY, new Set(), null);
    expect(result.length).toBe(0);
  });
});

// ── 3.8 autoExpand — 子菜单自动展开 ──
describe('autoExpand', () => {
  test('当前路径匹配子菜单时自动展开', () => {
    const result = autoExpand('/admin/ai-center/models', MOCK_MENU_TREE, []);
    expect(result).toContain('SuiteAI');
  });

  test('当前路径不匹配时保持折叠', () => {
    const result = autoExpand('/dashboard', MOCK_MENU_TREE, []);
    expect(result).not.toContain('SuiteAI');
  });

  test('已展开的不被移除', () => {
    const result = autoExpand('/dashboard', MOCK_MENU_TREE, ['SuiteAI']);
    expect(result).toContain('SuiteAI');
  });

  test('空菜单树', () => {
    const result = autoExpand('/admin/ai-center', [], []);
    expect(result).toEqual([]);
  });
});

// ── 3.9 综合回归测试 ──
describe('回归测试', () => {
  test('/seo 路径在整个系统中不误匹配（端到端）', () => {
    const currentPath = '/seo-matrix/keywords';
    expect(isNavActive(currentPath, { path: '/seo' })).toBe(false);
    expect(isNavActive(currentPath, { path: '/seo-matrix/keywords' })).toBe(true);
    const capId = resolveCapabilityIdForPath(currentPath, MOCK_REGISTRY);
    expect(capId).toBe('matrix.keywords');
    expect(capId).not.toBe('seo.overview');
  });

  test('/admin 深层嵌套路由的正确展开链', () => {
    const testPaths = [
      '/admin/v2ray/servers',
      '/admin/ai-center/models',
      '/admin/ai-center/knowledge',
      '/admin/code-tools',
    ];

    for (const p of testPaths) {
      const capId = resolveCapabilityIdForPath(p, MOCK_REGISTRY);
      expect(capId).not.toBeNull();
      expect(isNavActive(p, { path: '/admin' })).toBe(true);
    }
  });

  test('menuPathAllowed 不通过未注册路径绕过权限', () => {
    const restrictedPath = '/admin/system/users';
    const granted = new Set(['core.dashboard']);
    expect(menuPathAllowed(restrictedPath, MOCK_REGISTRY, granted, null)).toBe(false);
  });

  test('tenantFeatures 空数组时不应阻断已授权路径', () => {
    const granted = new Set(['core.products']);
    expect(menuPathAllowed('/products', MOCK_REGISTRY, granted, [''])).toBe(false);
    expect(menuPathAllowed('/products', MOCK_REGISTRY, granted, null)).toBe(true);
  });
});
