/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="账号绑定" subtitle="绑定第三方账号后，可在登录页使用该方式登录" surface="elevated">
  <div class="p-4 max-w-2xl">
    <template v-if="loading">
      <SkeletonCard variant="table" :rows="4" />
    </template>
    <template v-else>
      <a-list
        bordered
        :data-source="providers"
      >
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.label" />
            <template #actions>
              <span
                v-if="isBound(item.id)"
                class="text-xs text-slate-500 mr-2"
              >
                {{ bindingLabel(item.id) }}
              </span>
              <a-button
                v-if="isBound(item.id)"
                size="small"
                danger
                :loading="actionLoading === item.id"
                @click="onUnbind(item.id)"
              >
                解绑
              </a-button>
              <a-button
                v-else
                size="small"
                type="primary"
                :disabled="!isOAuthAvailable(item.id)"
                :loading="actionLoading === item.id"
                @click="onBind(item.id)"
              >
                绑定
              </a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { message } from 'ant-design-vue'
import {
  fetchOAuthBindings,
  unbindOAuthAccount,
  type OAuthBindingRow,
} from '@/api/oauthBindings'
import {
  fetchOAuthAuthorizeUrl,
  fetchOAuthProvidersStatus,
  oauthProviderLabel,
  type OAuthProvider,
} from '@/api/oauth'

const providers: { id: OAuthProvider; label: string }[] = [
  { id: 'qq', label: 'QQ' },
  { id: 'wechat', label: '微信' },
  { id: 'feishu', label: '飞书' },
  { id: 'dingtalk', label: '钉钉' },
]

const loading = ref(false)
const actionLoading = ref<OAuthProvider | ''>('')
const bindings = ref<OAuthBindingRow[]>([])
const oauthReady = ref<Record<OAuthProvider, boolean>>({
  qq: false,
  wechat: false,
  feishu: false,
  dingtalk: false,
})
const oauthDevBypass = ref(false)

function isBound(p: OAuthProvider) {
  return bindings.value.some((b) => b.provider === p)
}

function bindingLabel(p: OAuthProvider) {
  const row = bindings.value.find((b) => b.provider === p)
  return row?.provider_id_masked ? `已绑定 ${row.provider_id_masked}` : '已绑定'
}

function isOAuthAvailable(p: OAuthProvider) {
  return oauthReady.value[p] || oauthDevBypass.value
}

async function load() {
  loading.value = true
  try {
    const [rows, st] = await Promise.all([
      fetchOAuthBindings(),
      fetchOAuthProvidersStatus(),
    ])
    bindings.value = rows
    oauthReady.value = st.providers as Record<OAuthProvider, boolean>
    oauthDevBypass.value = !!st.dev_bypass
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function onBind(provider: OAuthProvider) {
  if (!isOAuthAvailable(provider)) {
    message.warning(`${oauthProviderLabel(provider)} 尚未配置 OAuth`)
    return
  }
  actionLoading.value = provider
  try {
    const state = btoa(
      JSON.stringify({
        redirect: '/admin/system/account-bindings',
        ts: Date.now(),
        provider,
        mode: 'bind',
      })
    )
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
    sessionStorage.setItem(`oauth_state_${provider}`, state)
    const { authorize_url } = await fetchOAuthAuthorizeUrl(provider, state)
    window.location.assign(authorize_url)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '无法发起绑定')
    actionLoading.value = ''
  }
}

async function onUnbind(provider: OAuthProvider) {
  actionLoading.value = provider
  try {
    await unbindOAuthAccount(provider)
    message.success('已解绑')
    await load()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '解绑失败')
  } finally {
    actionLoading.value = ''
  }
}

onMounted(() => {
  load()
})
</script>
