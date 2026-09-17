/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: 'admin' | 'user' | 'guest';
  createdAt: Date;
  lastLogin?: Date;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: 'zh-CN' | 'en-US';
  notifications: {
    email: boolean;
    push: boolean;
    taskUpdates: boolean;
    conversationMessages: boolean;
  };
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);
  const isAuthenticated = ref(false);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 计算属性
  const isAdmin = computed(() => {
    return user.value?.role === 'admin';
  });

  const userDisplayName = computed(() => {
    return user.value?.username || user.value?.email || '未登录用户';
  });

  const userAvatar = computed(() => {
    return user.value?.avatar || '/default-avatar.png';
  });

  const userPreferences = computed(() => {
    return user.value?.preferences || {
      theme: 'light',
      language: 'zh-CN',
      notifications: {
        email: true,
        push: true,
        taskUpdates: true,
        conversationMessages: true,
      },
    };
  });

  // 方法
  function setUser(newUser: User | null) {
    user.value = newUser;
    isAuthenticated.value = !!newUser;
  }

  function setToken(newToken: string | null) {
    token.value = newToken;
    if (newToken) {
      localStorage.setItem('auth_token', newToken);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  function setLoading(value: boolean) {
    loading.value = value;
  }

  function setError(value: string | null) {
    error.value = value;
  }

  function updateUserPreferences(preferences: Partial<UserPreferences>) {
    if (user.value) {
      user.value.preferences = {
        ...user.value.preferences,
        ...preferences,
      } as UserPreferences;
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    isAuthenticated.value = false;
    localStorage.removeItem('auth_token');
  }

  function initializeFromStorage() {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      token.value = storedToken;
      isAuthenticated.value = true;
    }
  }

  function hasPermission(permission: string): boolean {
    if (!user.value) return false;
    if (user.value.role === 'admin') return true;
    
    // 这里可以扩展更复杂的权限系统
    const userPermissions: Record<string, string[]> = {
      admin: ['read', 'write', 'delete', 'manage'],
      user: ['read', 'write'],
      guest: ['read'],
    };
    
    return userPermissions[user.value.role]?.includes(permission) || false;
  }

  return {
    // 状态
    user,
    token,
    isAuthenticated,
    loading,
    error,
    // 计算属性
    isAdmin,
    userDisplayName,
    userAvatar,
    userPreferences,
    // 方法
    setUser,
    setToken,
    setLoading,
    setError,
    updateUserPreferences,
    logout,
    initializeFromStorage,
    hasPermission,
  };
});