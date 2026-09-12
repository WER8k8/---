/** 租户站缺省社证/案例 — 建站未填内容时的建材外贸语境后备 */

export type TenantProofCase = {
  region: string;
  product: string;
  outcome: string;
};

export const DEFAULT_TENANT_PROOF_CASES: TenantProofCase[] = [
  { region: '东南亚', product: '保温建材', outcome: '工程询盘 24h 内响应，样品快速寄出' },
  { region: '中东', product: '轻集料 / 砂浆', outcome: 'data sheet 与规格书随询盘一并回复' },
  { region: '欧美', product: '橡塑 / 岩棉', outcome: '多规格 SKU 分行展示，减少串品咨询' },
];

export const DEFAULT_EXPORT_BADGES = [
  'OEM / ODM',
  'Factory Direct',
  'Export Ready',
  'Batch Traceable',
];
