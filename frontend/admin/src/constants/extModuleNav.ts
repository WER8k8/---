/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 扩展域子模块导航（侧栏「建设中」页面统一动作） */

export interface ExtModuleNavLink {
  label: string;
  path: string;
}

export interface ExtModuleNavConfig {
  title: string;
  subtitle: string;
  /** 本子模块内可切换的子页 */
  siblings: ExtModuleNavLink[];
  /** 已上线后台能力入口 */
  related: ExtModuleNavLink[];
}

const COMMON_RELATED: ExtModuleNavLink[] = [
  { label: '超级管理员工作台', path: '/admin' },
  { label: '能力导航', path: '/admin/capability-hub' },
  { label: 'AI 配置', path: '/ai-config' },
  { label: '系统设置', path: '/settings' },
];

function cfg(
  title: string,
  subtitle: string,
  siblings: ExtModuleNavLink[],
  related: ExtModuleNavLink[] = COMMON_RELATED
): ExtModuleNavConfig {
  return { title, subtitle, siblings, related };
}

/** 按路由 path 前缀匹配 */
export const EXT_MODULE_NAV_BY_PREFIX: { prefix: string; config: ExtModuleNavConfig }[] = [
  {
    prefix: '/agent-hub',
    config: cfg(
      '智能体协同',
      'MCP 桥接 · 任务编排 · 执行复盘',
      [
        { label: '协同看板', path: '/agent-hub' },
        { label: 'MCP 桥接', path: '/agent-hub/mcp-bridge' },
        { label: '任务调度', path: '/agent-hub/task-orchestrator' },
        { label: '执行复盘', path: '/agent-hub/execution-review' },
      ],
      [...COMMON_RELATED, { label: '自动化工作流', path: '/admin/automation/workflows' }]
    ),
  },
  {
    prefix: '/media-factory',
    config: cfg('多媒体工厂', '视频 · TTS · 图表 · 渲染队列', [
      { label: '视频工厂', path: '/media-factory' },
      { label: 'TTS 配音', path: '/media-factory/tts' },
      { label: '动态图表', path: '/media-factory/charts' },
      { label: '渲染队列', path: '/media-factory/render-queue' },
    ]),
  },
  {
    prefix: '/globalization',
    config: cfg('全球化多语言', '术语 · 翻译 · 文化适配', [
      { label: '多语言总览', path: '/globalization' },
      { label: '术语库', path: '/globalization/glossary' },
      { label: '翻译引擎', path: '/globalization/translator' },
      { label: '文化适配', path: '/globalization/culture-adapt' },
    ]),
  },
  {
    prefix: '/logistics',
    config: cfg('智能物流', 'LBS · 运费 · 报价单', [
      { label: '物流看板', path: '/logistics' },
      { label: 'LBS 测距', path: '/logistics/lbs-routing' },
      { label: '运费精算', path: '/logistics/freight-calc' },
      { label: '报价单', path: '/logistics/quotation' },
    ]),
  },
  {
    prefix: '/system-health',
    config: cfg(
      '系统健康',
      '压测 · 监控 · 备份',
      [
        { label: '健康看板', path: '/system-health' },
        { label: '压测管理', path: '/system-health/stress-test' },
        { label: '资源监控', path: '/system-health/resource-monitor' },
        { label: '备份回滚', path: '/system-health/backup' },
      ],
      [...COMMON_RELATED, { label: '性能与安全', path: '/seo/performance' }]
    ),
  },
  {
    prefix: '/ai-learning',
    config: cfg(
      'AI 深度学习',
      '行为 · 漏斗 · A/B',
      [
        { label: '学习看板', path: '/ai-learning' },
        { label: '行为分析', path: '/ai-learning/behavior' },
        { label: '转化漏斗', path: '/ai-learning/conversion-funnel' },
        { label: 'A/B 自动化', path: '/ai-learning/auto-ab-test' },
      ],
      [...COMMON_RELATED, { label: 'A/B 测试', path: '/ab-test' }]
    ),
  },
  {
    prefix: '/tenants',
    config: cfg('SaaS 租户', '套餐 · 计费 · 白标', [
      { label: '租户管理', path: '/tenants/dashboard' },
      { label: '套餐配置', path: '/tenants/plans' },
      { label: '计费结算', path: '/tenants/billing' },
      { label: '白标品牌', path: '/tenants/white-label' },
    ]),
  },
  {
    prefix: '/cognitive',
    config: cfg('认知智能', '知识图谱 · 问答 · 专家系统', [
      { label: '知识图谱', path: '/cognitive/dashboard' },
      { label: '智能问答', path: '/cognitive/qa-engine' },
      { label: '专家系统', path: '/cognitive/expert-system' },
      { label: '语义索引', path: '/cognitive/semantic-index' },
    ]),
  },
  {
    prefix: '/edge-cdn',
    config: cfg('边缘 CDN', '节点 · 预热 · 协议', [
      { label: 'CDN 管理', path: '/edge-cdn' },
      { label: '边缘节点', path: '/edge-cdn/nodes' },
      { label: '内容预热', path: '/edge-cdn/preheat' },
      { label: '协议优化', path: '/edge-cdn/protocol' },
    ]),
  },
  {
    prefix: '/developer',
    config: cfg(
      '开发者生态',
      '网关 · SDK · 低代码 · 插件',
      [
        { label: 'API 网关', path: '/developer' },
        { label: 'SDK 管理', path: '/developer/sdk' },
        { label: '低代码', path: '/developer/low-code' },
        { label: '插件市场', path: '/developer/plugins' },
      ],
      [...COMMON_RELATED, { label: '代码工具套件', path: '/admin/code-tools' }]
    ),
  },
  {
    prefix: '/admin/annex',
    config: cfg(
      '附属项目接入',
      'TradeAI · GoodJob · 第三方仓库 ERP 对接',
      [
        { label: 'TradeAI 执行台', path: '/admin/annex/trade-ai' },
        { label: 'GoodJob 执行台', path: '/admin/annex/goodjob' },
      ],
      [...COMMON_RELATED, { label: '集成栈', path: '/admin/system/integrations-stack' }]
    ),
  },
];

export function resolveExtModuleNav(path: string): ExtModuleNavConfig | null {
  const loc = path.split('?')[0] || '/';
  for (const row of EXT_MODULE_NAV_BY_PREFIX) {
    if (loc === row.prefix || loc.startsWith(`${row.prefix}/`)) return row.config;
  }
  return null;
}
