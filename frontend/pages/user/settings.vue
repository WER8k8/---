/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="user-settings-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          账户设置
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          管理您的账户信息和偏好设置
        </p>
      </div>
    </section>

    <!-- Settings Content -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-3xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Success Message -->
        <div
          v-if="successMessage"
          class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3"
        >
          <svg
            class="w-5 h-5 text-green-500 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span class="text-green-700 text-sm">{{ successMessage }}</span>
        </div>

        <!-- Error Message -->
        <div
          v-if="errorMessage"
          class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3"
        >
          <svg
            class="w-5 h-5 text-red-500 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span class="text-red-700 text-sm">{{ errorMessage }}</span>
        </div>

        <!-- Profile Settings -->
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">
            基本信息
          </h2>
          <form @submit.prevent="updateProfile">
            <!-- Avatar -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-text-primary mb-2">头像</label>
              <div class="flex items-center gap-4">
                <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  <img
                    v-if="profileForm.avatar"
                    :src="profileForm.avatar"
                    alt="头像"
                    class="w-full h-full object-cover"
                  >
                  <svg
                    v-else
                    class="w-8 h-8 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
                <button
                  type="button"
                  @click="uploadAvatar"
                  class="px-4 py-2 border border-border rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-elevated transition-colors"
                >
                  上传头像
                </button>
                <input
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleAvatarUpload"
                >
              </div>
            </div>

            <!-- Username -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-text-primary mb-2">用户名</label>
              <input
                v-model="profileForm.name"
                type="text"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                placeholder="请输入用户名"
              >
            </div>

            <!-- Email -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-text-primary mb-2">邮箱</label>
              <input
                v-model="profileForm.email"
                type="email"
                disabled
                class="w-full px-4 py-2.5 border border-border rounded-lg bg-surface-elevated text-text-secondary"
              >
            </div>

            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="profileLoading"
                class="btn-primary"
              >
                {{ profileLoading ? '保存中...' : '保存修改' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Password Settings -->
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">
            修改密码
          </h2>
          <form @submit.prevent="changePassword">
            <div class="mb-4">
              <label class="block text-sm font-medium text-text-primary mb-2">当前密码</label>
              <input
                v-model="passwordForm.oldPassword"
                type="password"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                placeholder="请输入当前密码"
              >
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-text-primary mb-2">新密码</label>
              <input
                v-model="passwordForm.newPassword"
                type="password"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                placeholder="请输入新密码（至少6位）"
              >
            </div>
            <div class="mb-6">
              <label class="block text-sm font-medium text-text-primary mb-2">确认新密码</label>
              <input
                v-model="passwordForm.confirmPassword"
                type="password"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                placeholder="请再次输入新密码"
              >
            </div>
            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="passwordLoading"
                class="btn-primary"
              >
                {{ passwordLoading ? '修改中...' : '修改密码' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Language Settings -->
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">
            语言设置
          </h2>
          <div class="space-y-3">
            <label
              v-for="lang in languageOptions"
              :key="lang.value"
              class="flex items-center gap-3 p-3 rounded-lg hover:bg-surface-elevated cursor-pointer transition-colors"
            >
              <input
                v-model="languageForm.language"
                type="radio"
                :value="lang.value"
                class="w-4 h-4 text-primary focus:ring-primary/20"
              >
              <span class="text-text-primary">{{ lang.label }}</span>
            </label>
          </div>
          <div class="flex justify-end mt-4">
            <button
              @click="saveLanguage"
              :disabled="languageLoading"
              class="btn-primary"
            >
              {{ languageLoading ? '保存中...' : '保存设置' }}
            </button>
          </div>
        </div>

        <!-- Notification Preferences -->
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
          <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">
            通知偏好
          </h2>
          <div class="space-y-4">
            <div
              v-for="pref in notificationPrefs"
              :key="pref.key"
              class="flex items-center justify-between p-3 rounded-lg hover:bg-surface-elevated transition-colors"
            >
              <div>
                <h4 class="font-medium text-text-primary">
                  {{ pref.label }}
                </h4>
                <p class="text-sm text-text-secondary">
                  {{ pref.description }}
                </p>
              </div>
              <button
                @click="toggleNotification(pref.key)"
                :class="[
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  pref.enabled ? 'bg-primary' : 'bg-gray-300'
                ]"
              >
                <span
                  :class="[
                    'inline-block h-4 w-4 rounded-full bg-white transition-transform',
                    pref.enabled ? 'translate-x-6' : 'translate-x-1'
                  ]"
                />
              </button>
            </div>
          </div>
          <div class="flex justify-end mt-4">
            <button
              @click="saveNotificationPrefs"
              :disabled="notifLoading"
              class="btn-primary"
            >
              {{ notifLoading ? '保存中...' : '保存设置' }}
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const api = (path: string) => useApiV1Url(path);

const successMessage = ref('');
const errorMessage = ref('');
const profileLoading = ref(false);
const passwordLoading = ref(false);
const languageLoading = ref(false);
const notifLoading = ref(false);
const avatarInput = ref<HTMLInputElement | null>(null);

// 个人资料表单
const profileForm = ref({
  name: '',
  email: '',
  avatar: '',
});

// 密码表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
});

// 语言设置
const languageForm = ref({
  language: 'zh-CN',
});

const languageOptions = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'ar', label: 'العربية' },
];

// 通知偏好
const notificationPrefs = ref([
  { key: 'email_order', label: '订单通知', description: '订单状态变更时通过邮件通知', enabled: true },
  { key: 'email_inquiry', label: '询盘通知', description: '收到新询盘时通过邮件通知', enabled: true },
  { key: 'email_promotion', label: '促销通知', description: '接收产品和促销邮件', enabled: false },
  { key: 'sms_order', label: '订单短信', description: '订单状态变更时通过短信通知', enabled: false },
  { key: 'sms_inquiry', label: '询盘短信', description: '收到新询盘时通过短信通知', enabled: false },
]);

// 清除消息
const clearMessages = () => {
  successMessage.value = '';
  errorMessage.value = '';
};

// 显示成功消息
const showSuccess = (msg: string) => {
  successMessage.value = msg;
  errorMessage.value = '';
  setTimeout(() => { successMessage.value = ''; }, 3000);
};

// 显示错误消息
const showError = (msg: string) => {
  errorMessage.value = msg;
  successMessage.value = '';
};

// 获取用户资料
const fetchProfile = async () => {
  try {
    const response = await fetch(api('/users/me'), {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      profileForm.value = {
        name: data.name || '',
        email: data.email || '',
        avatar: data.avatar || '',
      };
    }
  } catch (err) {
    console.error('Failed to fetch profile:', err);
  }
};

// 更新个人资料
const updateProfile = async () => {
  clearMessages();
  profileLoading.value = true;
  try {
    const response = await fetch(api('/users/me'), {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: profileForm.value.name,
        avatar: profileForm.value.avatar,
      }),
    });
    if (response.ok) {
      showSuccess('个人资料已更新');
    } else {
      showError('更新失败，请重试');
    }
  } catch (err) {
    showError('更新失败，请检查网络连接');
  } finally {
    profileLoading.value = false;
  }
};

// 修改密码
const changePassword = async () => {
  clearMessages();
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    showError('两次输入的新密码不一致');
    return;
  }
  if (passwordForm.value.newPassword.length < 6) {
    showError('新密码长度不能少于6位');
    return;
  }
  passwordLoading.value = true;
  try {
    const response = await fetch(api('/users/me/password'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        old_password: passwordForm.value.oldPassword,
        new_password: passwordForm.value.newPassword,
      }),
    });
    if (response.ok) {
      showSuccess('密码已修改');
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
    } else {
      const data = await response.json();
      showError(data.message || '修改失败，请检查当前密码');
    }
  } catch (err) {
    showError('修改失败，请检查网络连接');
  } finally {
    passwordLoading.value = false;
  }
};

// 上传头像
const uploadAvatar = () => {
  avatarInput.value?.click();
};

const handleAvatarUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(api('/upload/avatar'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: formData,
    });
    if (response.ok) {
      const data = await response.json();
      profileForm.value.avatar = data.url;
      showSuccess('头像已更新');
    }
  } catch (err) {
    showError('头像上传失败');
  }
};

// 保存语言设置
const saveLanguage = async () => {
  languageLoading.value = true;
  try {
    const response = await fetch(api('/users/me/settings'), {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language: languageForm.value.language }),
    });
    if (response.ok) {
      showSuccess('语言设置已保存');
    }
  } catch (err) {
    showError('保存失败');
  } finally {
    languageLoading.value = false;
  }
};

// 切换通知开关
const toggleNotification = (key: string) => {
  const pref = notificationPrefs.value.find(p => p.key === key);
  if (pref) pref.enabled = !pref.enabled;
};

// 保存通知偏好
const saveNotificationPrefs = async () => {
  notifLoading.value = true;
  try {
    const prefs = notificationPrefs.value.reduce((acc, pref) => {
      acc[pref.key] = pref.enabled;
      return acc;
    }, {} as Record<string, boolean>);

    const response = await fetch(api('/users/me/notification-prefs'), {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(prefs),
    });
    if (response.ok) {
      showSuccess('通知偏好已保存');
    }
  } catch (err) {
    showError('保存失败');
  } finally {
    notifLoading.value = false;
  }
};

// SEO元数据
useHead({
  title: '账户设置 - 建材B2B外贸平台',
  meta: [
    { name: 'description', content: '管理您的账户信息和偏好设置' },
  ],
});

onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
