/**
 * 技能包相关类型定义
 */

export interface Skill {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'accio_work' | 'deer_flow';
  isCore: boolean;
  parameters?: SkillParameter[];
}

export interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'file';
  required: boolean;
  description: string;
  defaultValue?: any;
}

export interface SkillListResponse {
  skills: Skill[];
  total: number;
}

export interface SkillDetailResponse {
  skill: Skill;
  parameters: SkillParameter[];
}

export interface ExecuteSkillRequest {
  parameters: Record<string, any>;
}

export interface ExecuteSkillResponse {
  taskId: string;
  estimatedTime?: number;
}

export type SkillCategory = 'accio_work' | 'deer_flow';

export interface SkillExecutionResult {
  skillId: string;
  success: boolean;
  data?: any;
  error?: string;
  executionTime: number;
}