/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import axios from 'axios';
import type { 
  Skill, 
  SkillListResponse, 
  SkillDetailResponse,
  ExecuteSkillRequest,
  ExecuteSkillResponse,
  SkillExecutionResult
} from '@/types/skill';

const API_BASE = '/api/skills';

/**
 * 获取所有技能包
 */
export async function getSkills(): Promise<SkillListResponse> {
  const response = await axios.get(API_BASE);
  return response.data;
}

/**
 * 获取技能包详情
 */
export async function getSkillDetail(id: string): Promise<SkillDetailResponse> {
  const response = await axios.get(`${API_BASE}/${id}`);
  return response.data;
}

/**
 * 调用技能包
 */
export async function executeSkill(id: string, data: ExecuteSkillRequest): Promise<ExecuteSkillResponse> {
  const response = await axios.post(`${API_BASE}/${id}/execute`, data);
  return response.data;
}

/**
 * 获取技能包执行历史
 */
export async function getSkillExecutions(skillId: string, page: number = 1, limit: number = 20): Promise<{
  executions: SkillExecutionResult[];
  total: number;
  page: number;
  limit: number;
}> {
  const response = await axios.get(`${API_BASE}/${skillId}/executions`, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 获取技能包分类
 */
export async function getSkillCategories(): Promise<{ categories: string[] }> {
  const response = await axios.get(`${API_BASE}/categories`);
  return response.data;
}

/**
 * 按分类获取技能包
 */
export async function getSkillsByCategory(category: string): Promise<SkillListResponse> {
  const response = await axios.get(`${API_BASE}/category/${category}`);
  return response.data;
}

/**
 * 搜索技能包
 */
export async function searchSkills(query: string): Promise<SkillListResponse> {
  const response = await axios.get(`${API_BASE}/search`, {
    params: { q: query }
  });
  return response.data;
}

/**
 * 收藏技能包
 */
export async function favoriteSkill(skillId: string): Promise<{ success: boolean }> {
  const response = await axios.post(`${API_BASE}/${skillId}/favorite`);
  return response.data;
}

/**
 * 取消收藏技能包
 */
export async function unfavoriteSkill(skillId: string): Promise<{ success: boolean }> {
  const response = await axios.delete(`${API_BASE}/${skillId}/favorite`);
  return response.data;
}

/**
 * 获取收藏的技能包
 */
export async function getFavoriteSkills(): Promise<SkillListResponse> {
  const response = await axios.get(`${API_BASE}/favorites`);
  return response.data;
}