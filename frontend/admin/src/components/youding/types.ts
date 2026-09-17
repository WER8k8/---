/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export interface OnboardingStep {
  id: string;
  title: string;
  done?: boolean;
  route?: string;
}

export interface QueueItem {
  id: string;
  label: string;
  priority?: 'high' | 'normal';
  /** 有 route 时待办行可点击跳转 */
  route?: string;
}

export interface YdSchemaField {
  key: string;
  label: string;
  type: 'string' | 'textarea' | 'number' | 'select' | 'boolean';
  required?: boolean;
  placeholder?: string;
  rows?: number;
  min?: number;
  max?: number;
  options?: Array<{ label: string; value: string | number }>;
  default?: unknown;
}
