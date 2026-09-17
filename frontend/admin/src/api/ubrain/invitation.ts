/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import axios from 'axios';

export interface Invitation {
  id: string;
  code: string;
  link: string;
  createdAt: Date;
  expiresAt?: Date;
  usedBy?: string;
  usedAt?: Date;
  status: 'active' | 'used' | 'expired';
}

export interface InvitationStats {
  totalInvited: number;
  totalEarnings: number;
  invitations: Invitation[];
}

export interface GenerateInvitationResponse {
  code: string;
  link: string;
  expiresAt?: Date;
}

const API_BASE = '/api/invitations';

/**
 * 生成邀请码
 */
export async function generateInvitation(): Promise<GenerateInvitationResponse> {
  const response = await axios.post(`${API_BASE}/generate`);
  return response.data;
}

/**
 * 获取邀请统计
 */
export async function getInvitationStats(): Promise<InvitationStats> {
  const response = await axios.get(`${API_BASE}/stats`);
  return response.data;
}

/**
 * 获取邀请列表
 */
export async function getInvitations(page: number = 1, limit: number = 20): Promise<{
  invitations: Invitation[];
  total: number;
  page: number;
  limit: number;
}> {
  const response = await axios.get(API_BASE, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 验证邀请码
 */
export async function validateInvitationCode(code: string): Promise<{
  valid: boolean;
  invitation?: Invitation;
  error?: string;
}> {
  const response = await axios.get(`${API_BASE}/validate/${code}`);
  return response.data;
}

/**
 * 使用邀请码
 */
export async function useInvitationCode(code: string): Promise<{
  success: boolean;
  reward?: number;
  error?: string;
}> {
  const response = await axios.post(`${API_BASE}/use/${code}`);
  return response.data;
}

/**
 * 获取邀请历史
 */
export async function getInvitationHistory(page: number = 1, limit: number = 20): Promise<{
  history: Array<{
    id: string;
    invitedUser: string;
    invitedAt: Date;
    reward: number;
    status: 'pending' | 'completed';
  }>;
  total: number;
}> {
  const response = await axios.get(`${API_BASE}/history`, {
    params: { page, limit }
  });
  return response.data;
}

/**
 * 获取佣金记录
 */
export async function getCommissionRecords(page: number = 1, limit: number = 20): Promise<{
  records: Array<{
    id: string;
    amount: number;
    type: 'invitation' | 'purchase';
    description: string;
    createdAt: Date;
    status: 'pending' | 'paid';
  }>;
  total: number;
  totalAmount: number;
}> {
  const response = await axios.get(`${API_BASE}/commissions`, {
    params: { page, limit }
  });
  return response.data;
}