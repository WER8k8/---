<template>
  <div class="min-h-screen bg-gradient-to-br from-secondary-50 via-white to-accent-50 flex items-center justify-center">
    <div class="bg-surface rounded-2xl shadow-elevated border border-border p-8 w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-2xl mb-4">
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
        <h1 class="text-2xl font-bold text-primary-900">
          优丁管理后台
        </h1>
        <p class="text-text-secondary text-sm mt-2">
          请登录以继续
        </p>
      </div>
      <form
        class="space-y-5"
        @submit.prevent="handleLogin"
      >
        <div>
          <label class="block text-sm font-semibold text-primary-900 mb-2">用户名</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-sm text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            placeholder="请输入用户名"
          >
        </div>
        <div>
          <label class="block text-sm font-semibold text-primary-900 mb-2">密码</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full px-4 py-3 bg-surface-elevated border border-border rounded-xl text-sm text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            placeholder="请输入密码"
          >
        </div>
        <div
          v-if="error"
          class="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl px-4 py-3"
        >
          {{ error }}
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full px-4 py-3 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl text-sm font-semibold hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-secondary-200"
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
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

async function handleLogin() {
  loading.value = true
  error.value = null
  try {
    await auth.login(username.value, password.value)
    router.push('/admin')
  } catch (e: any) {
    error.value = e.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
