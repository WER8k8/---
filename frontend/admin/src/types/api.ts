/**
 * API响应类型定义
 */

export interface ApiResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface ErrorResponse {
  code: number;
  message: string;
  details?: any;
}

export interface SuccessResponse {
  success: boolean;
  message?: string;
}

export interface ApiError {
  status: number;
  message: string;
  data?: any;
}

export type ApiErrorCode = 
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'VALIDATION_ERROR'
  | 'INTERNAL_ERROR'
  | 'NETWORK_ERROR'
  | 'TIMEOUT_ERROR';

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}