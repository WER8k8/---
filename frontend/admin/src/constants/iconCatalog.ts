/**
 * 业务图标目录（Ant Design 图标名，禁止 emoji）
 * 与 antIconMap.resolveAntIcon 配合使用
 */

/** 架构组件图标 */
export const ARCH_COMPONENT_ICONS: Record<string, string> = {
  hermes: 'RocketOutlined',
  deerflow: 'ClusterOutlined',
  ubrain: 'BrainOutlined',
  paperclip: 'ApartmentOutlined',
  acciowork: 'CarryOutOutlined',
  wangcai: 'TrophyOutlined',
  ai_engine: 'ApiOutlined',
  seo_matrix: 'GridOutlined',
  geo_engine: 'SearchOutlined',
  edge_cdn: 'CloudServerOutlined',
  crawler: 'SpiderOutlined',
  scheduler: 'CalendarOutlined',
  flywheel: 'SyncOutlined',
};

export function archComponentIconName(name: string): string {
  return ARCH_COMPONENT_ICONS[name] || 'AppstoreOutlined';
}

/** 角色图标 */
export const ROLE_ICONS: Record<string, string> = {
  super_admin: 'CrownOutlined',
  admin: 'ClusterOutlined',
  tenant_admin: 'BuildingOutlined',
  agent: 'TeamOutlined',
  partner: 'UserOutlined',
};

export function roleIconName(role: string): string {
  return ROLE_ICONS[role] || 'UserOutlined';
}

/** 业务模块图标 */
export const BUSINESS_MODULE_ICONS: Record<string, string> = {
  sales: 'ShopOutlined',
  marketing: 'GlobalOutlined',
  seo: 'SearchOutlined',
  content: 'FileTextOutlined',
  product: 'PackageOutlined',
  inquiries: 'MessageSquareOutlined',
  finance: 'AccountBookOutlined',
  system: 'SettingOutlined',
  security: 'ShieldOutlined',
  automation: 'ZapOutlined',
  logistics: 'CarOutlined',
  globalization: 'TranslationOutlined',
  media: 'VideoCameraOutlined',
  developer: 'CodeSandboxOutlined',
  tenant: 'TeamOutlined',
  referral: 'TrophyOutlined',
  cognitive: 'NodeIndexOutlined',
  health: 'HeartOutlined',
  learning: 'BulbOutlined',
};

export function businessModuleIconName(name: string): string {
  return BUSINESS_MODULE_ICONS[name] || 'AppstoreOutlined';
}

/** 系统层级图标 */
export const SYSTEM_LAYER_ICONS: Record<string, string> = {
  frontend: 'MonitorOutlined',
  backend: 'ServerOutlined',
  database: 'DatabaseOutlined',
  cache: 'CloudOutlined',
  queue: 'OrderedListOutlined',
  ai: 'RobotOutlined',
  api: 'ApiOutlined',
  cdn: 'CloudServerOutlined',
  worker: 'CarryOutOutlined',
  scheduler: 'ClockCircleOutlined',
};

export function systemLayerIconName(layer: string): string {
  return SYSTEM_LAYER_ICONS[layer] || 'AppstoreOutlined';
}

/** 多平台发布 — 平台显示名 → 图标名 */
export const SEO_PLATFORM_ICON_NAMES: Record<string, string> = {
  微信公众号: 'CommentOutlined',
  抖音: 'VideoCameraOutlined',
  快手: 'PlayCircleOutlined',
  小红书: 'HeartOutlined',
  百家号: 'SearchOutlined',
  微博: 'MessageOutlined',
  哔哩哔哩: 'VideoCameraOutlined',
  知乎: 'ReadOutlined',
  头条号: 'FileTextOutlined',
  企鹅号: 'TeamOutlined',
  网易号: 'FileOutlined',
  搜狐号: 'EditOutlined',
  一点资讯: 'FileOutlined',
  大鱼号: 'AppstoreOutlined',
  简书: 'EditOutlined',
  脉脉: 'TeamOutlined',
  微信视频号: 'VideoCameraOutlined',
  淘宝逛逛: 'ShoppingOutlined',
  '1688': 'ShopOutlined',
  慧聪网: 'BankOutlined',
  YouTube: 'PlayCircleOutlined',
  TikTok: 'VideoCameraOutlined',
  LinkedIn: 'TeamOutlined',
  Facebook: 'GlobalOutlined',
  Instagram: 'PictureOutlined',
  X: 'MessageOutlined',
  'X (Twitter)': 'MessageOutlined',
  Pinterest: 'PictureOutlined',
  Reddit: 'RedditCircleFilled',
  Snapchat: 'VideoCameraOutlined',
  Medium: 'EditOutlined',
  Tumblr: 'FileTextOutlined',
  'Telegram Channel': 'SendOutlined',
  WhatsApp: 'PhoneOutlined',
  'WhatsApp Business': 'PhoneOutlined',
  'LINE Official': 'MessageOutlined',
  Zalo: 'MessageOutlined',
  VK: 'GlobalOutlined',
  Quora: 'QuestionCircleOutlined',
  Blogger: 'EditOutlined',
  'WordPress.com': 'GlobalOutlined',
  'Amazon Seller': 'ShoppingOutlined',
  'Alibaba.com': 'GlobalOutlined',
};

export function seoPlatformIconName(name: string): string {
  return SEO_PLATFORM_ICON_NAMES[name] || 'SendOutlined';
}

/** AI 平台接入 — provider id → 图标名 */
export const AI_PROVIDER_ICON_NAMES: Record<string, string> = {
  deepseek: 'ExperimentOutlined',
  baidu: 'ReadOutlined',
  aliyun: 'CloudOutlined',
  bytedance: 'BulbOutlined',
  zhipu: 'ExperimentOutlined',
  moonshot: 'HighlightOutlined',
  lingyi: 'StarOutlined',
  siliconflow: 'CloudServerOutlined',
  minimax: 'RobotOutlined',
  iflytek: 'ThunderboltOutlined',
  openai: 'RobotOutlined',
  anthropic: 'ApiOutlined',
  google: 'GlobalOutlined',
  nvidia: 'DeploymentUnitOutlined',
  meta: 'NodeIndexOutlined',
};

export function aiProviderIconName(id: string): string {
  return AI_PROVIDER_ICON_NAMES[id] || 'ApiOutlined';
}

/** GEO 引擎快捷链接 */
export const GEO_QUICK_LINK_ICON_NAMES: Record<string, string> = {
  DeepSeek: 'SearchOutlined',
  豆包: 'BulbOutlined',
  元宝: 'GoldOutlined',
  通义千问: 'CloudOutlined',
  文心一言: 'ReadOutlined',
  Kimi: 'HighlightOutlined',
};

export function geoQuickLinkIconName(name: string): string {
  return GEO_QUICK_LINK_ICON_NAMES[name] || 'LinkOutlined';
}

/** 低代码组件/模板 */
export const LOWCODE_COMPONENT_ICONS: Record<string, string> = {
  输入框: 'EditOutlined',
  图表: 'BarChartOutlined',
  表格: 'OrderedListOutlined',
  搜索: 'SearchOutlined',
  轮播图: 'PictureOutlined',
  列表: 'UnorderedListOutlined',
  导航栏: 'AppstoreOutlined',
  联系方式: 'PhoneOutlined',
  日期选择: 'CalendarOutlined',
  按钮组: 'AppstoreOutlined',
  标签页: 'FileTextOutlined',
  信息提示: 'MessageOutlined',
};

export const LOWCODE_TEMPLATE_ICONS: Record<string, string> = {
  表单模板: 'FormOutlined',
  列表模板: 'OrderedListOutlined',
  详情模板: 'FileOutlined',
  仪表盘模板: 'DashboardOutlined',
};

export function lowcodeIconForName(name: string): string {
  return (
    LOWCODE_COMPONENT_ICONS[name] ||
    LOWCODE_TEMPLATE_ICONS[name] ||
    'AppstoreOutlined'
  );
}

/** 转化漏斗阶段 */
export const FUNNEL_STAGE_ICONS = [
  'EyeOutlined',
  'ReadOutlined',
  'MailOutlined',
  'DollarOutlined',
] as const;

/** 国际化区域（无国旗 emoji，用图标名供 YdNavIcon） */
export const REGION_ICON_NAMES: Record<string, string> = {
  global: 'GlobalOutlined',
  cn: 'EnvironmentOutlined',
  us: 'GlobalOutlined',
  eu: 'GlobalOutlined',
  sea: 'GlobalOutlined',
};

export function regionIconName(region: string): string {
  return REGION_ICON_NAMES[region] || 'GlobalOutlined';
}
