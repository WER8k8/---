# GB/T 25000.51-2016 合规性检查清单与测试计划

## 文档信息
- **项目名称**: 优丁建材AI SaaS企业网站
- **标准**: GB/T 25000.51-2016 软件产品质量要求与评价（SQuaRE）
- **创建日期**: 2025年
- **版本**: v1.0

---

## 一、合规性检查清单

### 1. 功能性（Functional Suitability）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| F1.1 | 完备性 | 功能完整实现，无遗漏功能项 | 功能清单对照测试 | 待测 | |
| F1.2 | 正确性 | 功能输出结果正确，符合规格 | 边界值测试 | 待测 | |
| F1.3 | 适用性 | 功能适合预期用途和用户需求 | 用户场景测试 | 待测 | |
| F1.4 | 权限控制 | 菜单权限、角色权限、功能访问控制正确 | 权限矩阵测试 | 已修复 | navRouteRegistry.ts已完善 |
| F1.5 | 导航功能 | 所有菜单项可点击跳转，路由正确映射 | 逐项点击测试 | 已修复 | menuItems逻辑已完善 |
| F1.6 | 数据加载 | API返回数据格式正确，前端正确处理 | 异常数据测试 | 已修复 | tenants/dashboard.vue已修复 |

### 2. 可靠性（Reliability）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| R2.1 | 成熟性 | 错误处理完善，无未捕获异常 | 异常场景测试 | 待测 | |
| R2.2 | 容错性 | 异常数据输入不会导致系统崩溃 | 边界值、异常数据测试 | 已修复 | items.filter问题已修复 |
| R2.3 | 易恢复性 | 失败后能恢复到正常状态 | 故障注入测试 | 待测 | |
| R2.4 | 防抖机制 | 按钮防抖、请求幂等 | 快速连续点击测试 | 待测 | |

### 3. 可用性（Usability）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| U3.1 | 可辨识性 | 界面元素清晰可辨认 | 视觉检查 | 待测 | |
| U3.2 | 易学性 | 用户能快速学习使用 | 用户测试 | 待测 | |
| U3.3 | 可操作性 | 操作便捷，无多余步骤 | 操作流测试 | 待测 | |
| U3.4 | 用户差错防范 | 防止用户误操作造成损失 | 确认机制测试 | 待测 | |

### 4. 性能效率（Performance Efficiency）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| P4.1 | 时间特性 | 响应时间符合要求 | 性能测试 | 待测 | |
| P4.2 | 资源利用 | CPU、内存使用合理 | 资源监控 | 待测 | |
| P4.3 | 负载能力 | 并发用户数支持 | 负载测试 | 待测 | |
| P4.4 | 图片加载 | 媒体资源加载优化 | 缓存测试 | 已修复 | 关键词排名图片缓存已实现 |

### 5. 维护性（Maintainability）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| M5.1 | 模块化 | 代码模块化，耦合度低 | 代码审查 | 待测 | |
| M5.2 | 可重用性 | 组件可重用 | 代码审查 | 待测 | |
| M5.3 | 可分析性 | 错误定位容易 | 日志检查 | 待测 | |
| M5.4 | 可修改性 | 代码修改不影响其他功能 | 变更影响分析 | 待测 | |

### 6. 可移植性（Portability）

| 序号 | 检查项 | 要求说明 | 检查方法 | 状态 | 备注 |
|------|--------|----------|----------|------|------|
| T6.1 | 适应性 | 支持不同浏览器/设备 | 兼容性测试 | 待测 | |
| T6.2 | 可安装性 | 部署安装简便 | 安装测试 | 待测 | |
| T6.3 | 可替换性 | 组件可替换 | 依赖检查 | 待测 | |

---

## 二、核心测试用例（防止复发关键路径）

### 2.1 导航栏功能测试

```typescript
// 导航栏回归测试用例
const navTestCases = [
  // 角色权限测试
  { role: 'super_admin', expectedMenuCount: '全部', description: '超级管理员显示全部菜单' },
  { role: 'admin', expectedMenuCount: '全部+实验室', description: '管理员显示全部菜单+实验室' },
  { role: 'editor', expectedMenuCount: '部分', description: '编辑角色菜单过滤' },
  { role: null, expectedMenuCount: '全部', description: '无角色降级处理' },

  // 菜单项逐项点击测试
  {
    group: '总览',
    items: [
      { name: '数据看板', path: '/dashboard' },
      { name: '流量看板', path: '/operations/traffic' }
    ]
  },
  {
    group: '业务管理',
    items: [
      { name: '产品管理', path: '/products' },
      { name: '分类管理', path: '/products/categories' },
      { name: '文章内容', path: '/content' },
      { name: '案例展示', path: '/cases' },
      { name: '新闻动态', path: '/news' }
    ]
  },
  {
    group: '客户线索',
    items: [
      { name: '询盘留言', path: '/inquiries' }
    ]
  },
  {
    group: 'AccioWork 销售',
    items: [
      { name: '销售工作台', path: '/sales/dashboard' },
      { name: '客户开发', path: '/sales/customer-finder' },
      { name: '自动谈单', path: '/sales/auto-negotiator' },
      { name: '开发信管理', path: '/sales/email-automation' }
    ]
  },
  {
    group: '网站优化',
    items: [
      { name: 'SEO总览', path: '/seo' },
      { name: 'AI建材百科', path: '/seo/building-wiki' },
      { name: 'AI内容优化', path: '/seo/content-optimizer' },
      { name: '关键词排名', path: '/seo/keyword-ranking' },
      { name: '百度站长工具', path: '/seo/baidu-tools' },
      { name: '站点体检', path: '/seo/site-audit' },
      { name: '矩阵词管理', path: '/seo-matrix/keywords' },
      { name: '多平台发布', path: '/seo-matrix/publish' }
    ]
  },
  {
    group: '代理中心',
    items: [
      { name: '业绩看板', path: '/agent/performance' },
      { name: '流量看板', path: '/agent/traffic' },
      { name: '佣金管理', path: '/agent/commission' },
      { name: '客户开户', path: '/agent/account-opening' },
      { name: '经营日报', path: '/agent/daily-report' },
      { name: '流失预警', path: '/agent/churn-warning' }
    ]
  },
  {
    group: '超级管理工具',
    items: [
      { name: '超管工作台', path: '/admin' },
      { name: '数据中心', path: '/admin/aggregation' },
      { name: '全平台流量', path: '/admin/traffic-board' },
      { name: '系统管理', path: '/admin/system' },
      { name: '能力划拨', path: '/admin/system/agent-capabilities' },
      { name: 'AI中心', path: '/admin/ai-center' },
      { name: '代码工具', path: '/admin/code-tools' },
      { name: '文件管理', path: '/admin/file-manager' },
      { name: '安全合规', path: '/admin/security' },
      { name: '自动化', path: '/admin/automation' },
      { name: '项目中心', path: '/admin/projects' },
      { name: '调度中心', path: '/admin/scheduler-hub' },
      { name: 'GEO引擎收录', path: '/admin/geo-engine' },
      { name: 'GEO基因分析', path: '/admin/geo' },
      { name: 'V2RayN代理', path: '/admin/v2ray' }
    ]
  }
]
```

### 2.2 租户管理模块测试

```typescript
// 租户模块回归测试用例
const tenantTestCases = [
  {
    id: 'T-001',
    scenario: '正常数据加载',
    steps: ['访问 /tenants/dashboard', '观察租户列表加载'],
    expected: '表格正常显示数据，无console错误'
  },
  {
    id: 'T-002',
    scenario: 'API返回空数据',
    steps: ['模拟API返回 {data: null}', '观察前端处理'],
    expected: '表格显示空状态，不崩溃'
  },
  {
    id: 'T-003',
    scenario: 'API返回异常格式',
    steps: ['模拟API返回字符串而非对象', '观察前端处理'],
    expected: '使用Array.isArray防护，不报.filter错误'
  },
  {
    id: 'T-004',
    scenario: '创建租户',
    steps: ['点击创建租户', '填写表单', '提交'],
    expected: '创建成功，列表刷新'
  },
  {
    id: 'T-005',
    scenario: '切换租户状态',
    steps: ['点击暂停按钮', '确认切换'],
    expected: '状态变更成功'
  }
]
```

### 2.3 防抖和幂等测试

```typescript
// 防抖幂等测试用例
const idempotencyTestCases = [
  {
    id: 'I-001',
    scenario: '快速连续点击同一菜单',
    action: '1秒内点击同一菜单5次',
    expected: '只触发1次路由跳转'
  },
  {
    id: 'I-002',
    scenario: '快速连续点击不同菜单',
    action: '1秒内点击5个不同菜单',
    expected: '只触发1次路由跳转（最后一次）'
  },
  {
    id: 'I-003',
    scenario: '按钮防抖测试',
    action: '快速点击创建租户按钮10次',
    expected: '只提交1次请求'
  },
  {
    id: 'I-004',
    scenario: '刷新后重复请求',
    action: 'F5刷新页面3次',
    expected: '每页只加载1次数据'
  }
]
```

---

## 三、防复发机制设计

### 3.1 数据校验层（前端）

```typescript
// 统一数据安全处理工具
export function safeArrayData(data: any): any[] {
  if (Array.isArray(data)) return data
  if (typeof data === 'object' && data !== null) {
    return data.items || data.data || []
  }
  return []
}

export function safeFilter<T>(arr: T[], predicate: (v: T) => boolean): T[] {
  if (!Array.isArray(arr)) return []
  return arr.filter(predicate)
}
```

### 3.2 API响应标准化

```typescript
// 统一API响应处理
interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export async function fetchData<T>(url: string): Promise<T[]> {
  const res = await fetch(url)
  const json = await res.json()
  const data = json.data

  if (!Array.isArray(data)) {
    console.warn(`[API] Expected array but got ${typeof data}`)
    return []
  }

  return data
}
```

### 3.3 菜单权限防御性编程

```typescript
// layout/index.vue 中的防御性检查
function menuPathAllowed(path: string): boolean {
  // 1. 超级管理员直接放行
  if (auth.currentRole === 'super_admin') return true

  // 2. 无角色时降级放行
  if (!auth.currentRole) return true

  // 3. 获取能力ID
  const capStore = useAgentCapabilitiesStore()
  const capId = resolveCapabilityIdForPath(path)

  // 4. 未注册能力ID的路径默认放行
  if (capId == null) return true

  // 5. 能力检查
  if (!capStore.canAccess(capId)) return false

  // 6. 租户功能限制
  const feature = pathFeatureMap[path]
  if (feature && tenantFeatures.value && !tenantFeatures.value.includes(feature)) {
    return false
  }

  return true
}
```

---

## 四、测试执行计划

### 第一阶段：快速冒烟测试（30分钟）
1. 导航栏全部菜单项点击测试
2. 租户管理页面加载测试
3. 核心业务流程测试

### 第二阶段：功能回归测试（2小时）
1. 所有角色权限测试
2. 边界条件和异常数据测试
3. 防抖幂等测试

### 第三阶段：性能和安全测试（待定）
1. 页面加载性能
2. API响应时间
3. 安全漏洞扫描

---

## 五、已知问题修复确认清单

| 问题编号 | 问题描述 | 修复文件 | 修复日期 | 验证状态 |
|----------|----------|----------|----------|----------|
| P-001 | 导航栏super_admin角色不显示菜单 | layout/index.vue | 2025-XX-XX | 待验证 |
| P-002 | 导航栏无角色时菜单不显示 | layout/index.vue | 2025-XX-XX | 待验证 |
| P-003 | roleGroupFilters缺少super_admin | layout/index.vue | 2025-XX-XX | 待验证 |
| P-004 | items.filter is not a function | tenants/dashboard.vue | 2025-XX-XX | 待验证 |
| P-005 | records.forEach is not a function | tenants/dashboard.vue | 2025-XX-XX | 待验证（连锁反应） |

---

## 六、合规性评分预估

| 质量特性 | 权重 | 当前评分 | 目标评分 | 差距 |
|----------|------|----------|----------|------|
| 功能性 | 30% | 75 | 90 | +15 |
| 可靠性 | 25% | 70 | 85 | +15 |
| 可用性 | 15% | 75 | 85 | +10 |
| 性能效率 | 10% | 80 | 85 | +5 |
| 维护性 | 10% | 70 | 80 | +10 |
| 可移植性 | 10% | 75 | 85 | +10 |
| **综合评分** | 100% | **74** | **86** | **+12** |

---

*文档版本: v1.0*
*创建人: AI Assistant*
*最后更新: 2025年*
