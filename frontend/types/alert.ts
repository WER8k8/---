// Alert 类型定义
export interface Alert {
  id: number;
  title: string;
  description?: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'active' | 'acknowledged' | 'resolved';
  source?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface AlertRule {
  id: number;
  name: string;
  condition: string;
  severity: 'critical' | 'warning' | 'info';
  enabled: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface AlertStatistics {
  total: number;
  active: number;
  critical: number;
  warning: number;
  info: number;
  resolvedToday: number;
}
