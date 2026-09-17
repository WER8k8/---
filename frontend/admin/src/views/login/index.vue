/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="login-page brand-hero" data-portal="platform">
    <LoginBrandColumn />

    <!-- Right Form Column -->
    <div class="form-col">
      <div class="mobile-logo">
        <div class="mobile-logo-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
        </div>
        <span class="mobile-logo-text">优丁</span>
      </div>

      <div class="form-wrapper">
        <h2 class="form-heading">欢迎回来</h2>
        <p class="form-subheading">登录您的优丁账号，继续管理您的外贸业务</p>

        <div class="card-surface">
          <LoginOAuthRow
            :items="oauthDisplayItems"
            :loading="oauthLoading"
            :hint="oauthHint"
            :dev-bypass="oauthDevBypass"
            @start-oauth="startOAuth"
          />

          <div class="divider">
            <div class="divider-line" />
            <span class="divider-text">{{ loginMode === 'password' ? '或使用邮箱密码' : '或使用邮箱验证码' }}</span>
            <div class="divider-line" />
          </div>

          <a-form :model="form" layout="vertical" class="login-form" @finish="onSubmit">
            <template v-if="loginMode === 'password'">
              <div class="form-field">
                <label class="field-label">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--uj-text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" /></svg>
                  <span>用户名或邮箱</span>
                </label>
                <a-input
                  v-model:value="form.username"
                  size="large"
                  autocomplete="username"
                  placeholder="请输入用户名或邮箱"
                  :bordered="false"
                />
              </div>
              <div class="form-field">
                <label class="field-label">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--uj-text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <span>密码</span>
                </label>
                <a-input-password
                  v-model:value="form.password"
                  size="large"
                  autocomplete="current-password"
                  placeholder="请输入密码"
                  :bordered="false"
                />
              </div>
            </template>
            <template v-else>
              <div class="form-field">
                <label class="field-label">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--uj-text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" /></svg>
                  <span>邮箱</span>
                </label>
                <a-input
                  v-model:value="form.email"
                  size="large"
                  autocomplete="email"
                  placeholder="请输入邮箱地址"
                  :bordered="false"
                />
              </div>
              <div class="form-field">
                <label class="field-label">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--uj-text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <span>验证码</span>
                </label>
                <div class="email-code-row">
                  <a-input
                    v-model:value="form.emailCode"
                    size="large"
                    :maxlength="6"
                    placeholder="6 位验证码"
                    :bordered="false"
                  />
                  <button
                    type="button"
                    class="send-code-btn"
                    :disabled="emailCodeSending || emailCodeCooldown > 0"
                    @click="onSendEmailCode"
                  >
                    {{ emailCodeCooldown > 0 ? `${emailCodeCooldown}s` : '获取' }}
                  </button>
                </div>
              </div>
            </template>

            <div
              v-if="!devSkipCaptcha"
              ref="sliderTrack"
              class="captcha-track"
              @mousedown="startDrag"
              @touchstart.prevent="startDrag"
            >
              <div class="captcha-fill" :style="{ width: sliderPercent + '%' }" />
              <div
                v-if="!captchaVerified"
                class="captcha-hint"
                :class="{ 'captcha-hint--hide': dragging }"
              >向右滑动完成验证</div>
              <div
                class="captcha-thumb"
                :class="{ 'captcha-thumb--ok': captchaVerified }"
                :style="{ left: sliderLeft + 'px' }"
              >
                <svg v-if="!captchaVerified" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5l7 7-7 7" /></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 13l4 4L19 7" /></svg>
              </div>
            </div>

            <a-alert v-if="errorMsg" type="error" show-icon class="error-banner" :message="errorMsg" />

            <div class="remember-forgot">
              <button type="button" class="text-link" @click="toggleLoginMode">
                {{ loginMode === 'password' ? '邮箱验证码登录' : '账号密码登录' }}
              </button>
              <button type="button" class="text-link" @click="router.push('/forgot-password')">忘记密码?</button>
            </div>

            <button type="submit" class="btn-primary" :disabled="loading">
              <svg v-if="loading" class="btn-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 3a9 9 0 1 0 9 9" /></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
              <span>{{ loading ? '登录中...' : '登录' }}</span>
            </button>
          </a-form>

          <LoginSocialButtons @start-oauth="startOAuth" />
        </div>

        <p class="footer-register">
          还没有账号? <a href="/tenants/register" class="text-link" @click.prevent="goRegister">立即注册</a>
        </p>
        <p class="footer-copyright">
          Copyright &copy; 2024-2026 优丁科技 版权所有
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, onUnmounted, watchEffect } from 'vue'
import LoginBrandColumn from './LoginBrandColumn.vue'
import LoginOAuthRow from './LoginOAuthRow.vue'
import LoginSocialButtons from './LoginSocialButtons.vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PLATFORM_LOGIN_COPY } from '@/constants/loginPortalCopy'
import { postLoginNavigatePath, postLoginShellHint, roleFromAccessToken } from '@/utils/postLoginNavigation'
import { prefetchLoginShellChunks, prefetchShellForRole } from '@/utils/prefetchPostLoginShell'
import { useAuthStore } from '@/stores/auth'
import { sendEmailLoginCode } from '@/api/emailAuth'
import {
  fetchOAuthAuthorizeUrl,
  fetchOAuthProvidersStatus,
  oauthProviderLabel,
  type OAuthProvider,
} from '@/api/oauth'
import { consumeSessionKickedMessage } from '@/utils/sessionKick'

const LS_LOCK = 'admin_login_client_lock_until'
const LS_FAIL = 'admin_login_client_fail_count'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const portalCopy = PLATFORM_LOGIN_COPY
const isLoginMode = ref(true)

watchEffect(() => {
  document.title = `优丁 · ${portalCopy.welcomeTitle}`
})

const loginMode = ref<'password' | 'email'>('password')
const devSkipCaptcha = import.meta.env.DEV

const form = reactive({
  username: '',
  password: '',
  email: '',
  emailCode: '',
})

const emailCodeSending = ref(false)
const emailCodeCooldown = ref(0)
let emailCooldownTimer: ReturnType<typeof setInterval> | null = null

const loading = ref(false)
const errorMsg = ref('')

const sliderTrack = ref<HTMLElement>()
const sliderLeft = ref(0)
const sliderPercent = ref(0)
const captchaVerified = ref(false)
const dragging = ref(false)

let trackWidth = 280
const SLIDER_WIDTH = 32

const oauthLoading = ref<OAuthProvider | ''>('')
const oauthHint = ref('')
const oauthReady = ref<Record<OAuthProvider, boolean>>({
  qq: false,
  wechat: false,
  feishu: false,
  dingtalk: false,
})
const oauthDevBypass = ref(false)

const oauthItems: { id: OAuthProvider; icon: string }[] = [
  {
    id: 'wechat',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#07C160"/><path fill="#fff" d="M8.5 7.5c-2.5 0-4.5 1.6-4.5 3.6 0 1.1.6 2.1 1.6 2.8l-.4 1.8 1.9-.9c.6.2 1.3.3 2 .3.1 0 .3 0 .4 0-.1-.4-.2-.8-.2-1.2 0-2.4 2.2-4.4 5-4.4.3 0 .6 0 .9.1C14.2 8.5 11.5 7.5 8.5 7.5zm-1.3 3a.9.9 0 1 1 0-1.8.9.9 0 0 1 0 1.8zm2.6 0a.9.9 0 1 1 0-1.8.9.9 0 0 1 0 1.8zm5.2 1.2c-2.2 0-4 1.4-4 3.1 0 .9.5 1.7 1.3 2.3l-.3 1.3 1.4-.7c.5.1 1 .2 1.5.2 2.2 0 4-1.4 4-3.1s-1.8-3.1-4-3.1zm-1.1 2.2a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4zm2.2 0a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4z"/></svg>',
  },
  {
    id: 'qq',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#12B7F5"/><path fill="#fff" d="M12 6c-3.3 0-6 2.4-6 5.4v2.2c0 .8.2 1.5.6 2.1L6 17l1.8-.5c1 .3 2.1.5 3.2.5h.5c1.1 0 2.2-.2 3.2-.5L17 17l-.6-1.3c.4-.6.6-1.3.6-2.1v-2.2C17 8.4 15.3 6 12 6zm-2.2 4.2a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm4.4 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>',
  },
  {
    id: 'feishu',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><rect width="24" height="24" rx="6" fill="#3370FF"/><path fill="#fff" d="M6 8.5 10.5 6v4.5L6 13V8.5zm12 0L13.5 6v4.5L18 13V8.5zM6 15.5 10.5 18v-4.5L6 11v4.5zm12 0L13.5 18v-4.5L18 11v4.5z"/></svg>',
  },
  {
    id: 'dingtalk',
    icon: '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><rect width="24" height="24" rx="6" fill="#0089FF"/><path fill="#fff" d="M12 5.5 7 18.5h2.1l.9-2.4h3.8l.9 2.4H17L12 5.5zm-.2 8.2-.9-2.4h1.8l-.9 2.4z"/></svg>',
  },
]

const oauthDisplayItems = computed(() =>
  oauthItems.map((item) => ({
    id: item.id,
    icon: item.icon,
    available: isOAuthAvailable(item.id),
    title: oauthTitle(item.id),
  })),
)

const canSubmit = computed(() => {
  if (!devSkipCaptcha && !captchaVerified.value) return false
  if (loginMode.value === 'password') {
    return Boolean(form.username.trim() && form.password)
  }
  return Boolean(form.email.trim() && form.emailCode.trim().length >= 4)
})

function toggleLoginMode() {
  loginMode.value = loginMode.value === 'password' ? 'email' : 'password'
}

function goRegister() {
  void router.push('/tenants/register')
}

function calcTrackWidth() {
  if (sliderTrack.value) {
    trackWidth = sliderTrack.value.clientWidth
  }
}

function startDrag(e: MouseEvent | TouchEvent) {
  if (captchaVerified.value) return
  dragging.value = true
  calcTrackWidth()

  const onMove = (ev: MouseEvent | TouchEvent) => {
    const clientX = 'touches' in ev ? ev.touches[0].clientX : ev.clientX
    const rect = sliderTrack.value?.getBoundingClientRect()
    if (!rect) return
    let x = clientX - rect.left - SLIDER_WIDTH / 2
    x = Math.max(0, Math.min(x, trackWidth - SLIDER_WIDTH))
    sliderLeft.value = x
    sliderPercent.value = Math.round((x / (trackWidth - SLIDER_WIDTH)) * 100)
  }

  const onEnd = () => {
    dragging.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onEnd)
    document.removeEventListener('touchmove', onMove)
    document.removeEventListener('touchend', onEnd)

    if (sliderPercent.value >= 95) {
      sliderLeft.value = trackWidth - SLIDER_WIDTH
      sliderPercent.value = 100
      captchaVerified.value = true
    } else {
      sliderLeft.value = 0
      sliderPercent.value = 0
    }
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onEnd)
  document.addEventListener('touchmove', onMove, { passive: false })
  document.addEventListener('touchend', onEnd)
}

function resetCaptcha() {
  captchaVerified.value = false
  sliderLeft.value = 0
  sliderPercent.value = 0
}

function isOAuthAvailable(provider: OAuthProvider): boolean {
  return oauthDevBypass.value || oauthReady.value[provider]
}

function oauthTitle(provider: OAuthProvider): string {
  if (isOAuthAvailable(provider)) {
    return oauthDevBypass.value
      ? `开发模式：点击模拟${oauthProviderLabel(provider)}登录`
      : `使用${oauthProviderLabel(provider)}登录`
  }
  return `${oauthProviderLabel(provider)} 登录（暂未开通）`
}

async function loadOAuthStatus() {
  try {
    const st = await fetchOAuthProvidersStatus()
    oauthReady.value = st.providers
    oauthDevBypass.value = st.dev_bypass ?? import.meta.env.DEV
    if (oauthDevBypass.value) {
      oauthHint.value = '开发模式：点击图标可模拟登录'
    } else if (!Object.values(st.providers).some(Boolean)) {
      oauthHint.value = '更多登录方式即将上线'
    } else {
      oauthHint.value = ''
    }
  } catch {
    if (import.meta.env.DEV) {
      oauthDevBypass.value = true
      oauthReady.value = { qq: true, wechat: true, feishu: true, dingtalk: true }
      oauthHint.value = '开发模式：社交图标可点击模拟登录'
    } else {
      oauthHint.value = '无法检测第三方登录配置'
    }
  }
}

async function startOAuth(provider: OAuthProvider) {
  errorMsg.value = ''
  oauthHint.value = ''
  if (clientLocked()) {
    message.warning(errorMsg.value)
    return
  }
  if (!isOAuthAvailable(provider)) {
    const msg = `${oauthProviderLabel(provider)} 登录尚未配置`
    errorMsg.value = msg
    oauthHint.value = msg
    message.warning(msg)
    return
  }
  oauthLoading.value = provider
  try {
    const redirect = postLoginNavigatePath(route.query.redirect, undefined)
    const state = btoa(JSON.stringify({ redirect, ts: Date.now(), provider }))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
    sessionStorage.setItem(`oauth_state_${provider}`, state)
    const { authorize_url } = await fetchOAuthAuthorizeUrl(provider, state)
    window.location.assign(authorize_url)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : `${oauthProviderLabel(provider)} 登录失败`
    errorMsg.value = msg
    oauthHint.value = msg
    message.error(msg)
  } finally {
    oauthLoading.value = ''
  }
}

function clientLocked(): boolean {
  const until = Number(sessionStorage.getItem(LS_LOCK) || '0')
  if (!until || Number.isNaN(until)) return false
  if (Date.now() < until) {
    const left = Math.ceil((until - Date.now()) / 60000)
    errorMsg.value = `尝试次数过多，请约 ${left} 分钟后再试`
    return true
  }
  sessionStorage.removeItem(LS_LOCK)
  sessionStorage.removeItem(LS_FAIL)
  return false
}

function recordClientFailure() {
  const n = Number(sessionStorage.getItem(LS_FAIL) || '0') + 1
  sessionStorage.setItem(LS_FAIL, String(n))
  if (n >= 5) sessionStorage.setItem(LS_LOCK, String(Date.now() + 15 * 60 * 1000))
}

function clearClientFailures() {
  sessionStorage.removeItem(LS_FAIL)
  sessionStorage.removeItem(LS_LOCK)
}

function roleAfterLogin(): string | undefined {
  return auth.currentRole ?? roleFromAccessToken(auth.token)
}

function navigateAfterLogin() {
  const role = roleAfterLogin()
  const target = postLoginNavigatePath(route.query.redirect, role)
  message.success(postLoginShellHint(role))
  prefetchShellForRole(role)
  void router.replace(target)
}

async function onSendEmailCode() {
  const email = form.email.trim()
  if (!email || !email.includes('@')) {
    message.warning('请输入有效邮箱')
    return
  }
  emailCodeSending.value = true
  try {
    const res = await sendEmailLoginCode(email)
    message.success(res.message || '验证码已发送')
    if (
      res.dev_code &&
      import.meta.env.DEV &&
      typeof window !== 'undefined' &&
      (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ) {
      form.emailCode = res.dev_code
    }
    emailCodeCooldown.value = 60
    if (emailCooldownTimer) clearInterval(emailCooldownTimer)
    emailCooldownTimer = setInterval(() => {
      emailCodeCooldown.value -= 1
      if (emailCodeCooldown.value <= 0 && emailCooldownTimer) {
        clearInterval(emailCooldownTimer)
        emailCooldownTimer = null
      }
    }, 1000)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '发送失败')
  } finally {
    emailCodeSending.value = false
  }
}

async function onSubmit() {
  if (loading.value) return
  errorMsg.value = ''
  if (clientLocked()) {
    message.warning(errorMsg.value)
    return
  }
  if (!canSubmit.value) {
    errorMsg.value = devSkipCaptcha ? '请填写完整' : '请拖动滑块完成验证'
    message.warning(errorMsg.value)
    return
  }

  if (loginMode.value === 'email') {
    const email = form.email.trim()
    const code = form.emailCode.trim()
    if (!email || code.length < 4) {
      errorMsg.value = '请输入邮箱和验证码'
      message.warning(errorMsg.value)
      return
    }
    loading.value = true
    try {
      await auth.loginWithEmail(email, code)
      clearClientFailures()
      resetCaptcha()
      navigateAfterLogin()
    } catch (e: unknown) {
      recordClientFailure()
      resetCaptcha()
      const msg = e instanceof Error ? e.message : '登录失败'
      errorMsg.value = msg
      message.error(msg)
    } finally {
      loading.value = false
    }
    return
  }

  if (!form.username.trim() || !form.password) {
    errorMsg.value = '请输入用户名和密码'
    message.warning(errorMsg.value)
    return
  }

  loading.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    clearClientFailures()
    resetCaptcha()
    navigateAfterLogin()
  } catch (e: unknown) {
    recordClientFailure()
    resetCaptcha()
    const msg = e instanceof Error ? e.message : '登录失败'
    errorMsg.value = msg
    message.error(msg)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (import.meta.env.DEV) clearClientFailures()
  else clientLocked()
  calcTrackWidth()
  loadOAuthStatus()
  prefetchLoginShellChunks(route.query.redirect)
  if (devSkipCaptcha) captchaVerified.value = true
  window.addEventListener('resize', calcTrackWidth)
  const kicked = consumeSessionKickedMessage()
  if (kicked) {
    errorMsg.value = kicked
    message.warning(kicked)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', calcTrackWidth)
  if (emailCooldownTimer) clearInterval(emailCooldownTimer)
})
</script>

<style scoped>
/* ==========================================
   CSS Variables (var(--uj-*))
   ========================================== */
.login-page {
  --uj-brand: #4a9b8c;
  --uj-brand-hover: #3d8578;
  --uj-brand-light: rgba(74, 155, 140, 0.1);
  --uj-bg-page: transparent;
  --uj-bg-card: #ffffff;
  --uj-bg-input: #fafafa;
  --uj-border: #d9d9d9;
  --uj-text: #1a1a2e;
  --uj-text-card: #1a1a2e;
  --uj-text-muted: #8c8c8c;
  --uj-radius-sm: 4px;
  --uj-radius-md: 8px;
  --uj-radius-lg: 12px;
  --uj-radius-xl: 16px;
  --uj-ease: cubic-bezier(0.16, 1, 0.3, 1);
  --uj-duration: 200ms;

  display: flex;
  min-height: 100vh;
  font-family: 'DM Sans', 'Noto Sans SC', system-ui, sans-serif;
  background:
    radial-gradient(1100px 560px at 88% -12%, rgba(45, 212, 191, 0.16), transparent 60%),
    radial-gradient(820px 460px at 4% 112%, rgba(74, 155, 140, 0.12), transparent 58%),
    linear-gradient(160deg, #eafaf4 0%, #f6fbf9 45%, #eef7f3 100%);
  color: var(--uj-text);
  position: relative;
  overflow: hidden;
}

/* Dark theme — Ant Design 5 dark tokens */
:root[data-uj-theme='dark'] .login-page {
  background:
    radial-gradient(1000px 520px at 88% -12%, rgba(45, 212, 191, 0.1), transparent 60%),
    radial-gradient(800px 460px at 4% 112%, rgba(74, 155, 140, 0.08), transparent 58%),
    #141414;
  --uj-bg-page: #141414;
  --uj-bg-card: #1f1f1f;
  --uj-bg-input: #262626;
  --uj-border: #303030;
  --uj-text: #e8e8e8;
  --uj-text-card: #e8e8e8;
  --uj-text-muted: #8c8c8c;
}

/* Light theme is now the default */

/* Brand column styles live in LoginBrandColumn.vue */

/* Desktop: form column takes half width */
@media (min-width: 1024px) {
  .form-col { width: 50%; }
}

/* ==========================================
   Form Column (Right)
   ========================================== */
.form-col {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  z-index: 1;
  background:
    radial-gradient(620px 520px at 100% 0%, rgba(74, 155, 140, 0.06), transparent 60%),
    #f8fbfa;
}
:root[data-uj-theme='dark'] .form-col {
  background: #141414;
}

.mobile-logo {
  display: none;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}
@media (max-width: 1023px) {
  .mobile-logo { display: flex; }
}
@media (min-width: 1024px) {
  .mobile-logo { display: none !important; }
}

.mobile-logo-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.625rem;
  background: #4a9b8c;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mobile-logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a2e;
}
:root[data-uj-theme='dark'] .mobile-logo-text {
  color: #e8e8e8;
}

.form-wrapper {
  width: 100%;
  max-width: 26rem;
  animation: uj-rise 0.7s var(--uj-ease) both;
}

.form-heading {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
  color: #1a1a2e;
}
:root[data-uj-theme='dark'] .form-heading {
  color: #e8e8e8;
}

.form-subheading {
  font-size: 0.875rem;
  color: #8c8c8c;
  margin-bottom: 2rem;
}

/* ==========================================
   Card Surface
   ========================================== */
.card-surface {
  position: relative;
  background: #fff;
  border: 1px solid #eef2f1;
  border-radius: var(--uj-radius-xl);
  padding: 2rem;
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 12px 30px rgba(15, 23, 42, 0.06),
    0 24px 60px rgba(74, 155, 140, 0.05);
  overflow: hidden;
}
.card-surface::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  /* 同色相薄荷渐变（DESIGN.md §2：禁止跨色相渐变） */
  background: linear-gradient(90deg, #2a6b60, #4a9b8c 60%, #5eb8a8);
}
:root[data-uj-theme='dark'] .card-surface {
  background: #1f1f1f;
  border-color: #303030;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* OAuth row styles live in LoginOAuthRow.vue */

/* ==========================================
   Divider
   ========================================== */
.divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
}
.divider-line {
  flex: 1;
  height: 1px;
  background-color: #e8e8e8;
}
:root[data-uj-theme='dark'] .divider-line {
  background-color: #303030;
}
.divider-text {
  font-size: 0.75rem;
  color: #8c8c8c;
  white-space: nowrap;
}

/* ==========================================
   Form
   ========================================== */
.login-form {
  width: 100%;
}

.form-field {
  margin-bottom: 1.25rem;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #595959;
}
:root[data-uj-theme='dark'] .field-label {
  color: #bfbfbf;
}

:deep(.ant-input) {
  background-color: #fafafa !important;
  border: 1px solid #d9d9d9 !important;
  border-radius: var(--uj-radius-md) !important;
  color: #1a1a2e !important;
  transition: border-color var(--uj-duration) var(--uj-ease), box-shadow var(--uj-duration) var(--uj-ease);
}
:deep(.ant-input-password .ant-input),
:deep(.ant-input-affix-wrapper .ant-input) {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
:deep(.ant-input:focus),
:deep(.ant-input-focused) {
  border-color: var(--uj-brand) !important;
  box-shadow: 0 0 0 2px rgba(74, 155, 140, 0.15) !important;
}
:deep(.ant-input-password .ant-input:focus),
:deep(.ant-input-affix-wrapper .ant-input:focus) {
  border: none !important;
  box-shadow: none !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input) {
  background-color: #262626 !important;
  border-color: #424242 !important;
  color: #e8e8e8 !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input-password .ant-input),
:root[data-uj-theme='dark'] :deep(.ant-input-affix-wrapper .ant-input) {
  background-color: transparent !important;
  border: none !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input:focus),
:root[data-uj-theme='dark'] :deep(.ant-input-focused) {
  border-color: var(--uj-brand) !important;
  box-shadow: 0 0 0 2px rgba(74, 155, 140, 0.2) !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input-password .ant-input:focus),
:root[data-uj-theme='dark'] :deep(.ant-input-affix-wrapper .ant-input:focus) {
  border: none !important;
  box-shadow: none !important;
}
:deep(.ant-input::placeholder) {
  color: var(--uj-text-muted) !important;
}
:deep(.ant-input-password .ant-input-suffix) {
  color: var(--uj-text-muted);
}
:deep(.ant-input-affix-wrapper) {
  background-color: #fafafa !important;
  border: 1px solid #d9d9d9 !important;
  border-radius: var(--uj-radius-md) !important;
}
:deep(.ant-input-affix-wrapper:focus),
:deep(.ant-input-affix-wrapper-focused) {
  border-color: var(--uj-brand) !important;
  box-shadow: 0 0 0 2px rgba(74, 155, 140, 0.15) !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input-affix-wrapper) {
  background-color: #262626 !important;
  border-color: #424242 !important;
}
:root[data-uj-theme='dark'] :deep(.ant-input-affix-wrapper:focus),
:root[data-uj-theme='dark'] :deep(.ant-input-affix-wrapper-focused) {
  border-color: var(--uj-brand) !important;
  box-shadow: 0 0 0 2px rgba(74, 155, 140, 0.2) !important;
}

/* Email code row */
.email-code-row {
  display: flex;
  gap: 0.5rem;
}
.email-code-row .ant-input-wrapper {
  flex: 1;
}

.send-code-btn {
  white-space: nowrap;
  padding: 0 1rem;
  border-radius: var(--uj-radius-md);
  border: 1px solid #4a9b8c;
  background: rgba(74, 155, 140, 0.08);
  color: #3d8578;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--uj-duration) var(--uj-ease);
}
:root[data-uj-theme='dark'] .send-code-btn {
  border-color: #4a9b8c;
  background: rgba(74, 155, 140, 0.15);
  color: #6bb8a8;
}
.send-code-btn:hover:not(:disabled) {
  background: rgba(74, 155, 140, 0.15);
}
.send-code-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ==========================================
   Captcha
   ========================================== */
.captcha-track {
  position: relative;
  height: 38px;
  background: #f1f5f4;
  border: 1px solid #e2e8e6;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 1rem;
  cursor: pointer;
  user-select: none;
}
:root[data-uj-theme='dark'] .captcha-track {
  background: #262626;
  border-color: #424242;
}

.captcha-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(74, 155, 140, 0.28), rgba(45, 212, 191, 0.42));
  transition: width 0.05s;
  pointer-events: none;
}

.captcha-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75rem;
  color: #8c8c8c;
  pointer-events: none;
  transition: opacity var(--uj-duration);
  white-space: nowrap;
}
.captcha-hint--hide { opacity: 0; }

.captcha-thumb {
  position: absolute;
  top: 3px;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4a9b8c, #2a6b60);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  transition: left 0.05s;
  box-shadow: 0 2px 8px rgba(74, 155, 140, 0.4);
}
.captcha-thumb--ok {
  background: #10b981;
}

/* ==========================================
   Error Banner
   ========================================== */
.error-banner {
  margin-bottom: 1rem;
}
:deep(.error-banner .ant-alert) {
  border-radius: var(--uj-radius-md);
}

/* ==========================================
   Remember & Forgot
   ========================================== */
.remember-forgot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  font-size: 0.8125rem;
}
:root[data-uj-theme='dark'] .remember-forgot {
  color: #8c8c8c;
}

.text-link {
  color: var(--uj-brand);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
  font-size: 0.8125rem;
  transition: opacity var(--uj-duration);
}
.text-link:hover {
  text-decoration: underline;
  opacity: 0.85;
}

/* ==========================================
   Primary Button
   ========================================== */
.btn-primary {
  width: 100%;
  padding: 0.75rem;
  border-radius: var(--uj-radius-md);
  font-size: 0.9375rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  /* a11y：白字主按钮用同色相深薄荷渐变 #2f6960→#2a6b60（对比度 ≥6.3:1），见 DESIGN.md §5.2 */
  background: linear-gradient(135deg, #2f6960 0%, #2a6b60 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(42, 107, 96, 0.28), 0 2px 4px rgba(15, 23, 42, 0.06);
  transition: transform var(--uj-duration) var(--uj-ease), box-shadow var(--uj-duration) var(--uj-ease), filter var(--uj-duration) var(--uj-ease);
}
.btn-primary:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(42, 107, 96, 0.36), 0 4px 8px rgba(15, 23, 42, 0.08);
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}
.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.btn-spinner {
  animation: uj-spin 0.7s linear infinite;
}
@keyframes uj-spin {
  to { transform: rotate(360deg); }
}
@keyframes uj-rise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Social buttons styles live in LoginSocialButtons.vue */

/* ==========================================
   Footer
   ========================================== */
.footer-register {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.8125rem;
  color: #8c8c8c;
}

.footer-copyright {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.6875rem;
  color: #bfbfbf;
  opacity: 0.45;
}

@media (prefers-reduced-motion: reduce) {
  .form-wrapper { animation: none; }
  .btn-spinner { animation: none; }
}
</style>
