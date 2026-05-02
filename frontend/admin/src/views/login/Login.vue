<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-4">
          <svg
            class="w-8 h-8 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">
          优丁管理后台
        </h1>
        <p class="text-gray-500 text-sm mt-2">
          请登录以继续
        </p>
      </div>
      <form
        class="space-y-5"
        @submit.prevent="handleLogin"
      >
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">用户名</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
            placeholder="请输入用户名"
          >
        </div>
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">密码</label>
          <div class="relative">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              class="w-full px-4 py-3 pr-12 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
              placeholder="请输入密码"
            >
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg
                v-if="!showPassword"
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <svg
                v-else
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                />
              </svg>
            </button>
          </div>
        </div>
        <a-alert
          v-if="error"
          :type="errorType"
          show-icon
          class="mb-4"
        >
          {{ error }}
        </a-alert>
        <button
          type="submit"
          :loading="loading"
          class="w-full px-4 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-xl text-sm font-semibold hover:from-primary-600 hover:to-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary-200"
        >
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Alert as AAlert } from 'ant-design-vue'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const errorType = ref<'error' | 'warning'>('error')
const showPassword = ref(false)

async function handleLogin() {
  // 表单验证
  if (!username.value.trim()) {
    error.value = '请输入用户名'
    errorType.value = 'warning'
    return
  }
  
  if (!password.value.trim()) {
    error.value = '请输入密码'
    errorType.value = 'warning'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await auth.login(username.value.trim(), password.value)
    router.push('/dashboard')
  } catch (e: any) {
    console.error('登录错误:', e)
    // 根据错误类型显示不同提示
    if (e.message && e.message.includes('NetworkError')) {
      error.value = '网络连接失败，请检查后端服务是否正常运行'
      errorType.value = 'warning'
    } else if (e.message && e.message.includes('401')) {
      error.value = '用户名或密码错误，请重试'
      errorType.value = 'error'
    } else if (e.message && e.message.includes('403')) {
      error.value = '访问被拒绝，请联系管理员'
      errorType.value = 'error'
    } else if (e.message && e.message.includes('请求超时')) {
      error.value = '请求超时，请稍后重试'
      errorType.value = 'warning'
    } else {
      error.value = e.message || '登录失败，请检查用户名和密码'
      errorType.value = 'error'
    }
  } finally {
    loading.value = false
  }
}
</script>