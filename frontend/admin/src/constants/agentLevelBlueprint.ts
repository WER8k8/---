/**
 * 四级代理：后台职责与前台功能边界（产品/权限设计单源）。
 * 与 `agentCapabilities` 默认划拨一致；上线后由 JWT + 后端 RBAC 落库校验。
 * 层级：超管(L1)、省级代理(L2)、市级代理(L3)、官网租户(L4)
 */
import type { AgentLevelId } from '@/stores/agentCapabilities';

export interface AgentLevelBackendModule {
  /** 模块名（给后端拆服务或路由前缀时对齐） */
  key: string;
  /** 该级别是否应暴露此模块的写/管能力 */
  scope: 'full' | 'read' | 'scoped_write' | 'none';
  /** 一句话说明 */
  note: string;
}

export interface AgentLevelBlueprint {
  id: AgentLevelId;
  /** 一句话定位 */
  tagline: string;
  /** 典型组织形态 */
  orgShape: string;
  /** 建议的后台 API / 服务边界 */
  backendModules: AgentLevelBackendModule[];
  /** 前台工作台能力主题（与 workbenchCapabilityRegistry 分区对应） */
  workbenchThemes: string[];
  /** 业务功能要点（产品向） */
  features: string[];
  /** 明确禁止或需上级代操作的事项 */
  restrictions: string[];
  /** 数据隔离与审计期望 */
  dataScope: string;
}

export const AGENT_LEVEL_BLUEPRINTS: AgentLevelBlueprint[] = [
  {
    id: 'L1',
    tagline: '超管：平台侧最高运营主体，可管全租户、全能力与向下划拨。',
    orgShape: '总部 / 平台运营方；可创建与管理 L2～L4 主体。',
    backendModules: [
      { key: 'platform.tenants', scope: 'full', note: '租户开通、套餐、白标域名与计费策略' },
      {
        key: 'platform.secrets',
        scope: 'full',
        note: '全局密钥、三方集成（飞书/AI Provider）根配置',
      },
      { key: 'platform.audit', scope: 'full', note: '全链路操作审计、导出与留存策略' },
      { key: 'platform.agent-tree', scope: 'full', note: '代理树、级别升降、能力模板下发' },
      {
        key: 'core.* + seo.* + matrix.* + system.* + suite.* + ext.*',
        scope: 'full',
        note: '全部业务域与超管套件、扩展域',
      },
    ],
    workbenchThemes: [
      '控制台与业务',
      'SEO 工具箱',
      'SEO 矩阵',
      '系统与设置',
      '平台集成',
      '超管套件',
      '侧栏扩展域',
    ],
    features: [
      '工作台：全部能力项（含扩展域与超管套件）。',
      '为下级维护「能力模板」并批量同步划拨结果。',
      '合规与安全的最高裁决与例外审批（与审计绑定）。',
    ],
    restrictions: ['无（在合同与法规范围内仍受平台超级账号约束）。'],
    dataScope: '跨租户聚合可读；写入需显式选择租户并写审计。',
  },
  {
    id: 'L2',
    tagline: '省级代理：管理下辖市级代理与商业条款，不触碰平台根密钥。',
    orgShape: '省级经销商；下辖 L3 市级代理或多个 L4 官网租户。',
    backendModules: [
      { key: 'orgs.children', scope: 'full', note: '创建/冻结 L3/L4、分配配额与价格策略副本' },
      { key: 'billing.usage', scope: 'read', note: '用量与账单只读；调价回传平台审批' },
      { key: 'compliance.exports', scope: 'scoped_write', note: '辖区合规报表生成与导出' },
      { key: 'platform.secrets', scope: 'none', note: '不可见平台根密钥；仅使用已下发的集成实例' },
      {
        key: 'core.* + seo.* + matrix.* + system.* + suite.*',
        scope: 'full',
        note: '业务与系统设置、超管套件（无扩展域演示项）',
      },
    ],
    workbenchThemes: [
      '控制台与业务',
      'SEO 工具箱',
      'SEO 矩阵',
      '系统与设置',
      '平台集成',
      '超管套件',
    ],
    features: [
      '默认划拨：全能力除「侧栏扩展域」演示/规划类入口。',
      '辖区看板：汇总下级 KPI、任务完成率与合规分数。',
      '批量策略：对下级统一 SEO/矩阵参数模板（下发非强制覆盖时可配置）。',
    ],
    restrictions: ['不可管理其他 L2 同级组织树；不可变更平台级模型与全局计费规则。'],
    dataScope: '本组织及子树内全量；平级组织数据不可见。',
  },
  {
    id: 'L3',
    tagline: '市级代理：深耕矩阵与地域词，服务多个官网租户。',
    orgShape: '市级运营中心；连接多个 L4 官网租户。',
    backendModules: [
      { key: 'matrix.*', scope: 'full', note: '地域词库、生成任务、分发与收录监控（辖区内）' },
      { key: 'seo.batch', scope: 'full', note: '批量 SEO、站点审计调度' },
      { key: 'orgs.children', scope: 'scoped_write', note: '仅创建/维护 L4 业务代理账号' },
      { key: 'system.users', scope: 'scoped_write', note: '仅限本组织内角色分配，不可建平台角色' },
      { key: 'suite.agent-cap', scope: 'read', note: '可查看对下划拨结果，不可改平台模板' },
    ],
    workbenchThemes: ['控制台与业务', 'SEO 工具箱', 'SEO 矩阵', '系统与设置'],
    features: [
      '默认划拨：core / seo / matrix / system 能力域。',
      '区域词库与矩阵流水线为工作重心；询盘与客户可下放到 L4。',
      '收录与排名监控可配置告警到辖区群（飞书 webhook 等由上级下发）。',
    ],
    restrictions: [
      '不可访问超管套件中的系统配置、代码与文件底层工具（除非上级单独开通）。',
      '不可创建 L2 或跨区组织。',
    ],
    dataScope: '绑定区域维度过滤；客户数据按组织挂载，禁止跨区导出未授权字段。',
  },
  {
    id: 'L4',
    tagline: '官网租户：维护自己的官网内容、产品与日常获客。',
    orgShape: '官网租户 / 企业客户；拥有自己的官网站点与产品。',
    backendModules: [
      { key: 'core.*', scope: 'scoped_write', note: '产品、内容、案例、询盘、新闻（绑定站点）' },
      {
        key: 'seo.*',
        scope: 'scoped_write',
        note: '单站 SEO、合规扫描、关键词与 Schema（无矩阵全局）',
      },
      { key: 'matrix.*', scope: 'none', note: '默认关闭矩阵全局设置与词库根表' },
      { key: 'system.users', scope: 'none', note: '不可管理系统用户；仅可操作分配给自己的站点' },
    ],
    workbenchThemes: ['控制台与业务', 'SEO 工具箱'],
    features: [
      '默认划拨：仪表盘、询盘、产品与 SEO 相关入口。',
      '侧重：内容更新、广告法合规自检、询盘跟进与简单报表。',
    ],
    restrictions: [
      '不可访问矩阵看板系统设置、平台 AI 根配置、多租户与白标。',
      '不可导出全库或跨客户数据。',
    ],
    dataScope: '单租户或多站点但在「客户合约」列出的 site_id 集合内。',
  },
];

export function blueprintForLevel(id: AgentLevelId): AgentLevelBlueprint {
  return AGENT_LEVEL_BLUEPRINTS.find((b) => b.id === id) ?? AGENT_LEVEL_BLUEPRINTS[0];
}
