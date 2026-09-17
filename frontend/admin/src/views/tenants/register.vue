/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="register-wrap min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50/40 to-indigo-100/50 p-6">
    <div class="w-full max-w-2xl rounded-2xl border border-white/70 bg-white/80 p-8 shadow-xl backdrop-blur-xl">
      <!-- Header -->
      <div class="mb-8 text-center">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30">
          <svg class="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-slate-900">开通 SaaS 服务</h1>
        <p class="mt-1 text-sm text-slate-500">验证码开户 · 产品图平台代开 · 发视频/绑平台按清单自备账号</p>
      </div>

      <a-alert
        v-if="externalPreview"
        type="info"
        show-icon
        class="mb-6"
        :message="externalPreview.headline || '云存储与第三方账号'"
      >
        <template #description>
          <p class="text-sm mb-2">{{ externalPreview.platform_managed_summary }}</p>
          <p class="text-sm mb-2">{{ externalPreview.tenant_managed_summary }}</p>
          <div v-if="externalPreview.tenant_items?.length" class="text-sm">
            <strong>开户后您可能需要自备：</strong>
            <ul class="list-disc pl-5 mt-1 space-y-0.5">
              <li v-for="(t, i) in externalPreview.tenant_items" :key="i">{{ t.title }}</li>
            </ul>
          </div>
        </template>
      </a-alert>

      <a-alert
        v-if="bundledServices.length"
        type="info"
        show-icon
        class="mb-6"
        message="一次开户，全部预置"
      >
        <template #description>
          <ul class="text-sm list-disc pl-4 space-y-1">
            <li v-for="(s, i) in bundledServices" :key="i">{{ s }}</li>
          </ul>
        </template>
      </a-alert>

      <a-form :model="form" layout="vertical" @finish="onSubmit">
        <!-- 基本信息 -->
        <div class="mb-6 rounded-lg bg-slate-50/70 p-5">
          <h3 class="mb-4 text-sm font-semibold text-slate-700">基本信息</h3>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="公司名称" name="company_name" :rules="[{ required: true, message: '请输入公司名称' }]">
                <a-input v-model:value="form.company_name" size="large" placeholder="您的公司或品牌名称" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="管理员姓名" name="admin_name" :rules="[{ required: true, message: '请输入管理员姓名' }]">
                <a-input v-model:value="form.admin_name" size="large" placeholder="管理员姓名" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="邮箱" name="email" :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '邮箱格式不正确' },
          ]">
            <a-input v-model:value="form.email" size="large" placeholder="请输入邮箱地址" autocomplete="email" />
          </a-form-item>
          <a-form-item label="邮箱验证码" required>
            <div class="flex gap-2">
              <a-input
                v-model:value="form.email_code"
                size="large"
                placeholder="6 位验证码"
                :maxlength="6"
                class="flex-1"
              />
              <a-button size="large" :loading="sendingCode" :disabled="codeCooldown > 0" @click="sendEmailCode">
                {{ codeCooldown > 0 ? `${codeCooldown}s` : '获取验证码' }}
              </a-button>
            </div>
            <p v-if="devCode" class="mt-1 text-xs text-amber-600">开发环境验证码：{{ devCode }}</p>
          </a-form-item>
          <a-form-item label="联系电话" name="contact_phone">
            <a-input v-model:value="form.contact_phone" size="large" placeholder="选填，用于客户回呼" />
          </a-form-item>
          <a-form-item label="主营产品" name="primary_product">
            <a-input
              v-model:value="form.primary_product"
              size="large"
              placeholder="如：岩棉板、橡塑保温管、玻璃棉毡（须与您产品库一致）"
            />
          </a-form-item>
          <a-form-item label="产地/产业带" name="location_hint">
            <a-input
              v-model:value="form.location_hint"
              size="large"
              placeholder="如：河北廊坊大城县、河间（用于识别产业带与联网调研）"
            />
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="密码" name="password" :rules="[
                { required: true, message: '请设置密码' },
                { min: 6, message: '密码至少 6 位' },
              ]">
                <a-input-password v-model:value="form.password" size="large" placeholder="至少 6 位密码" autocomplete="new-password" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="确认密码" name="confirm_password" :rules="[
                { required: true, message: '请确认密码' },
                { validator: confirmPasswordValidator },
              ]">
                <a-input-password v-model:value="form.confirm_password" size="large" placeholder="再次输入密码" autocomplete="new-password" />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 邀请码 -->
        <div class="mb-6 rounded-lg bg-gradient-to-r from-blue-50/60 to-emerald-50/60 p-5">
          <h3 class="mb-4 text-sm font-semibold text-slate-700">
            <GiftOutlined class="mr-1 text-blue-500" />
            邀请码 <span class="font-normal text-slate-400">(选填)</span>
          </h3>
          <div class="flex items-center gap-3">
            <a-input
              v-model:value="form.referral_code"
              size="large"
              placeholder="请输入朋友的邀请码（6位）"
              class="flex-1"
              :maxlength="6"
              style="text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600;"
            >
              <template #prefix>
                <TeamOutlined class="text-blue-400" />
              </template>
            </a-input>
            <a-tooltip title="邀请码是您朋友的6位专属代码，填写后双方均可获得额外奖励">
              <QuestionCircleOutlined class="text-slate-400 cursor-help text-base" />
            </a-tooltip>
          </div>
          <p class="mt-2 text-xs text-slate-400">填写邀请码，您和邀请人均可获得额外福利</p>
        </div>

        <!-- 平台预置 -->
        <div v-if="platformOptions.length" class="mb-6 rounded-lg bg-slate-50/70 p-5">
          <h3 class="mb-2 text-sm font-semibold text-slate-700">预置发布平台（可选，开户后可再自选/自填）</h3>
          <p class="text-xs text-slate-500 mb-3">不勾选不影响使用；多平台分发页可勾选任意平台或填写我们未收录的平台名称</p>
          <a-checkbox-group v-model:value="form.platform_names" class="flex flex-col gap-2 max-h-48 overflow-y-auto">
            <a-checkbox v-for="p in platformOptions" :key="p.name" :value="p.name">
              <span>{{ p.name }}</span>
              <a-tag class="ml-2" :color="p.region === 'global' ? 'blue' : 'green'" size="small">
                {{ p.region === 'global' ? '海外' : '国内' }}
              </a-tag>
            </a-checkbox>
          </a-checkbox-group>
        </div>

        <!-- 套餐选择 -->
        <div class="mb-6 rounded-lg bg-slate-50/70 p-5">
          <h3 class="mb-4 text-sm font-semibold text-slate-700">选择套餐</h3>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div
              v-for="plan in plans"
              :key="plan.code"
              class="plan-card"
              :class="{ 'plan-card--selected': form.plan_code === plan.code, 'plan-card--recommended': plan.recommended }"
              @click="form.plan_code = plan.code"
            >
              <div v-if="plan.recommended" class="plan-badge">推荐</div>
              <div class="plan-name">{{ plan.name }}</div>
              <div class="plan-price">
                <span class="plan-price-amount">¥{{ plan.price }}</span>
                <span class="plan-price-period">/月</span>
              </div>
              <ul class="plan-features">
                <li v-for="(f, fi) in plan.features" :key="fi">{{ f }}</li>
              </ul>
            </div>
          </div>
        </div>

        <a-alert v-if="errorMsg" type="error" show-icon class="mb-4" :message="errorMsg" />

        <a-button type="primary" html-type="submit" size="large" block :loading="loading">
          免费开始试用
        </a-button>
      </a-form>

      <div class="mt-6 text-center">
        <span class="text-sm text-slate-500">已有账号？</span>
        <router-link to="/login" class="text-sm font-medium text-blue-600 hover:text-blue-700">去登录</router-link>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { GiftOutlined, TeamOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { unwrapFetchedJson } from '@/api'

interface PlanOption {
  code: string
  name: string
  price: number
  recommended: boolean
  features: string[]
}

const plans: PlanOption[] = [
  { code: 'free', name: '体验版', price: 0, recommended: false, features: ['独立域绑定', '多平台发布（试用）', '询盘 inbox（试用）', '7 天试用'] },
  { code: 'basic', name: '启航版', price: 299, recommended: false, features: ['独立域绑定', '多平台发布', '询盘 inbox', '3 站点 · 50 产品'] },
  { code: 'pro', name: '专业版', price: 699, recommended: true, features: ['含启航版', 'GEO 引擎 · AI 收录', 'GEO 内容矩阵', 'SEO 矩阵 + IM'] },
  { code: 'enterprise', name: '企业版', price: 1999, recommended: false, features: ['含专业版 GEO', '收录巡检告警', '白标登录', '操作审计'] },
]

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const errorMsg = ref('')
const sendingCode = ref(false)
const codeCooldown = ref(0)
const devCode = ref('')
const bundledServices = ref<string[]>([])
const externalPreview = ref<{
  headline?: string
  platform_managed_summary?: string
  tenant_managed_summary?: string
  tenant_items?: { title: string }[]
} | null>(null)
const platformOptions = ref<{ name: string; region: string; default_selected?: boolean }[]>([])

const form = reactive({
  company_name: '',
  admin_name: '',
  email: '',
  email_code: '',
  contact_phone: '',
  primary_product: '',
  location_hint: '',
  password: '',
  confirm_password: '',
  plan_code: 'free',
  referral_code: '',
  platform_names: [] as string[],
})

onMounted(async () => {
  const qPlan = String(route.query.plan || '').trim()
  if (qPlan && plans.some((p) => p.code === qPlan)) {
    form.plan_code = qPlan
  }

  try {
    const gs = await fetch('/api/v1/media-factory/guest-session', { credentials: 'include' })
    const gsRaw = await gs.json()
    const gsData = unwrapFetchedJson<{ guest_token?: string }>(gsRaw)
    if (gsData?.guest_token) {
      localStorage.setItem('mf_guest_token', gsData.guest_token)
    }
  } catch {
    /* 访客 token 可选 */
  }

  try {
    const res = await fetch('/api/v1/tenants/register/catalog')
    const raw = await res.json()
    const data = unwrapFetchedJson<{ platforms?: typeof platformOptions.value; bundled_services?: string[]; external_accounts_preview?: typeof externalPreview.value }>(raw)
    if (data?.platforms?.length) {
      platformOptions.value = data.platforms
      form.platform_names = []
    }
    bundledServices.value = data?.bundled_services || []
    externalPreview.value = data?.external_accounts_preview || null
  } catch {
    /* 使用空列表，仍可注册 */
  }
})

async function sendEmailCode() {
  const email = form.email.trim()
  if (!email) {
    message.warning('请先填写邮箱')
    return
  }
  sendingCode.value = true
  devCode.value = ''
  try {
    const res = await fetch('/api/v1/auth/send-email-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    const raw = await res.json()
    if (!res.ok) {
      message.error((raw as { message?: string })?.message || '发送失败')
      return
    }
    const data = unwrapFetchedJson<{ dev_code?: string; message?: string }>(raw)
    devCode.value = data?.dev_code || ''
    message.success(data?.message || '验证码已发送')
    codeCooldown.value = 60
    const timer = setInterval(() => {
      codeCooldown.value -= 1
      if (codeCooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } finally {
    sendingCode.value = false
  }
}

function confirmPasswordValidator(_rule: unknown, value: string) {
  return value === form.password ? Promise.resolve() : Promise.reject('两次密码不一致')
}

async function onSubmit() {
  if (!form.email_code.trim()) {
    message.warning('请输入邮箱验证码')
    return
  }
  errorMsg.value = ''
  loading.value = true

  const guestToken = localStorage.getItem('mf_guest_token') || ''

  try {
    const res = await fetch('/api/v1/tenants/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name: form.company_name.trim(),
        admin_name: form.admin_name.trim(),
        email: form.email.trim(),
        email_code: form.email_code.trim(),
        contact_phone: form.contact_phone.trim() || undefined,
        primary_product: form.primary_product.trim() || undefined,
        location_hint: form.location_hint.trim() || undefined,
        password: form.password,
        plan_code: form.plan_code,
        referral_code: form.referral_code.trim() || undefined,
        platform_names: form.platform_names.length ? form.platform_names : undefined,
        guest_token: guestToken || undefined,
      }),
    })

    const raw = await res.json().catch(() => ({}))

    if (!res.ok) {
      const msg = (raw as any)?.message || '注册失败，请稍后再试'
      errorMsg.value = msg
      message.error(msg)
      return
    }

    const data = unwrapFetchedJson<{
      access_token: string
      refresh_token?: string
      user?: { username: string }
    }>(raw)

    if (!data?.access_token) {
      errorMsg.value = '注册失败，请稍后再试'
      message.error(errorMsg.value)
      return
    }

    // 自动登录 - 保存 token（优先 sessionStorage，回退 localStorage）
    const store = typeof sessionStorage !== 'undefined' ? sessionStorage : localStorage
    store.setItem('admin_token', data.access_token)
    if (data.refresh_token) {
      store.setItem('admin_refresh_token', data.refresh_token)
    }
    if (data.user?.username) {
      store.setItem('admin_username', data.user.username)
    }

    const onboarding = (data as { onboarding?: { checklist?: { title: string; status: string }[] } }).onboarding
    const pending = onboarding?.checklist?.filter(c => c.status === 'pending').length || 0
    message.success(
      pending
        ? '开户成功！请按新手指引完成快速建站'
        : '开户成功！全部服务已预置',
    )

    localStorage.setItem('tenant_onboarding_pending', '1')
    const product = form.primary_product.trim()
    await router.replace({
      path: '/client/onboarding',
      query: product ? { product } : undefined,
    })
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '网络异常，请稍后再试'
    errorMsg.value = msg
    message.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.plan-card {
  position: relative;
  padding: 1rem 0.75rem;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background: white;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
}
.plan-card:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}
.plan-card--selected {
  border-color: var(--uj-brand, #4a9b8c);
  background: #f0f7ff;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}
.plan-card--recommended {
  border-color: #8b5cf6;
}
.plan-card--recommended.plan-card--selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}
.plan-badge {
  position: absolute;
  top: -8px;
  right: 8px;
  padding: 1px 10px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
}
.plan-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.35rem;
}
.plan-price {
  margin-bottom: 0.5rem;
}
.plan-price-amount {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
}
.plan-price-period {
  font-size: 0.75rem;
  color: #94a3b8;
}
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.72rem;
  color: #64748b;
  line-height: 1.8;
}
.plan-features li::before {
  content: '';
  color: #22c55e;
  font-weight: 700;
}
</style>
