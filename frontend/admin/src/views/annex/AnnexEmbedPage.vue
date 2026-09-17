/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage :title="pageTitle" :subtitle="pageSubtitle" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="handleBack">
          <template #icon><ArrowLeftOutlined /></template>
          返回工作台
        </a-button>
        <a-button
          v-if="embedUrl"
          :loading="ticketLoading"
          type="primary"
          ghost
          @click="requestTicket"
        >
          <template #icon><ReloadOutlined /></template>
          刷新票据 / 重新握手
        </a-button>
      </a-space>
    </template>

    <!-- 异常状态 1: 未配置或未部署 -->
    <a-alert
      v-if="!embedUrl"
      type="warning"
      show-icon
      class="mb-4"
      :message="`${annexLabel} 未部署或未配置`"
      :description="deployHint"
    />

    <!-- 异常状态 2: 票据握手失败 -->
    <a-alert
      v-else-if="ticketError"
      type="error"
      show-icon
      class="mb-4"
      message="统一身份票据握手失败"
      :description="`${ticketError}（GoodJob 已深度并入优丁 YouDing，独立登录已去除，请确认后端 8001 服务正常或点击右上角重新握手）`"
    >
      <template #action>
        <a-button size="small" type="primary" danger ghost @click="requestTicket">
          重试握手
        </a-button>
      </template>
    </a-alert>

    <!-- 正常或握手中状态 -->
    <a-alert
      v-else
      type="info"
      show-icon
      class="mb-4"
      :message="`${annexLabel} · ${ticketReady ? '统一身份已授权' : '票据签发握手中...'}`"
      :description="`单点进入：${annexReady ? '双向通信已就绪' : '等待应用握手响应'}。票据 5 分钟有效，遇会话失效可直接点击「重新握手」。`"
    />

    <!-- GoodJob CRM 功能模块切换（票据中心管理 / 客户管理） -->
    <div v-if="isGoodJob" class="gj-module-bar">
      <a-space size="small" wrap>
        <strong class="gj-module-label">GoodJob CRM</strong>
        <a-button
          v-for="m in GOODJOB_MODULES"
          :key="m.key"
          size="small"
          :type="annexModule === m.key ? 'primary' : 'default'"
          :ghost="annexModule !== m.key"
          @click="goAnnexModule(m.key)"
        >
          {{ m.label }}
        </a-button>
        <a-button
          v-if="annexModule"
          size="small"
          type="text"
          @click="goAnnexModule('')"
        >
          返回 GoodJob 全景
        </a-button>
      </a-space>
    </div>

    <!-- 嵌入容器 -->
    <div v-if="embedUrl" class="embed-shell">
      <div v-if="!ticketReady || ticketLoading" class="embed-loading">
        <a-spin size="large" tip="正在为您安全接入 GoodJob CRM..." />
      </div>
      <iframe
        v-if="ticketReady"
        :src="embedUrlWithTicket"
        class="embed-frame"
        :title="annexLabel"
        allow="fullscreen"
        referrerpolicy="no-referrer-when-downgrade"
        @load="onIframeLoad"
      />
    </div>

    <div class="mt-4 flex items-center justify-between">
      <a-space>
        <a-button @click="handleBack">返回工作台</a-button>
        <a-button v-if="embedUrl" :loading="ticketLoading" @click="requestTicket">
          重新握手
        </a-button>
      </a-space>
      <span class="text-xs text-slate-400">
        YouDing AEOS · GoodJob CRM 附属统一执行台 (单点登录受 SYSTEM-LOCK-02 与 LOGIN-LOCK-01 保护)
      </span>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons-vue';

import { YdPage } from '@/components/youding';
import { annexMeta, resolveAnnexEmbedUrl, goodjobModuleMeta, GOODJOB_MODULES } from '@/constants/annexModules';
import { useAuthStore } from '@/stores/auth';
import { apiPost } from '@/utils/api';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const annexReady = ref(false);
const annexTicket = ref('');
const ticketReady = ref(false);
const ticketLoading = ref(false);
const ticketError = ref('');

const annexKey = computed(() => String(route.meta.annexKey || ''));
const meta = computed(() => annexMeta(annexKey.value));


const annexLabel = computed(() => meta.value?.label || '附属执行台');
const annexModule = computed(() => String(route.meta.annexModule || ''));
const moduleMeta = computed(() => goodjobModuleMeta(annexModule.value));
const isGoodJob = computed(() => annexKey.value === 'goodjob');
const pageTitle = computed(() => {
  if (moduleMeta.value) return `GoodJob CRM · ${moduleMeta.value.label}`;
  return annexLabel.value;
});
const pageSubtitle = computed(() => {
  if (moduleMeta.value) return moduleMeta.value.desc;
  return meta.value?.desc || '附属项目统一接入中枢';
});

const isTenantShell = computed(() => route.path.startsWith('/client'));

function handleBack() {
  if (isTenantShell.value) {
    void router.push('/client/today');
  } else {
    void router.push('/admin');
  }
}

function goAnnexModule(key: string) {
  const base = isTenantShell.value
    ? meta.value?.clientPath || '/client/annex/goodjob'
    : meta.value?.adminPath || '/admin/annex/goodjob';
  void router.push(key ? `${base}/${key}` : base);
}

const embedUrl = computed(() => {
  return resolveAnnexEmbedUrl(annexKey.value);
});

const embedUrlWithTicket = computed(() => {
  if (!embedUrl.value || !annexTicket.value) return '';
  try {
    const url = new URL(embedUrl.value);
    url.searchParams.set('annex_ticket', annexTicket.value);
    url.searchParams.set('annex', annexKey.value);
    if (moduleMeta.value) url.searchParams.set('gj_view', moduleMeta.value.view);
    return url.toString();
  } catch {
    return '';
  }
});

const deployHint = computed(() => {
  const envKey = meta.value?.envKey || 'VITE_GOODJOB_EMBED_URL';
  return `请在 frontend/admin/.env.development.local 中配置 ${envKey}（必须带 VITE_ 前缀，例如 http://127.0.0.1:5188/），并启动对应附属服务。`;
});

async function requestTicket() {
  if (!embedUrl.value) return;
  ticketLoading.value = true;
  ticketError.value = '';
  try {
    const res = await apiPost<{ annex_ticket?: string }>('/annex/ticket', { annex: annexKey.value });
    if (!res?.annex_ticket) {
      ticketError.value = '主站后端未签发有效票据';
      ticketReady.value = false;
      return;
    }
    annexTicket.value = res.annex_ticket;
    ticketReady.value = true;
  } catch (err) {
    ticketError.value = err instanceof Error ? err.message : '票据签发失败';
    ticketReady.value = false;
  } finally {
    ticketLoading.value = false;
  }
}

function onIframeLoad() {
  annexReady.value = true;
}

function onAnnexMessage(event: MessageEvent) {
  if (!embedUrl.value) return;
  let allowed = '';
  try {
    allowed = new URL(embedUrl.value).origin;
  } catch {
    return;
  }
  if (event.origin !== allowed) return;
  const data = (event.data || {}) as { type?: string; path?: string };
  if (data.type === 'annex.ready') {
    annexReady.value = true;
    return;
  }
  if (data.type === 'annex.reauth') {
    void requestTicket();
    return;
  }
  if (data.type === 'annex.navigate' && data.path && data.path.startsWith('/')) {
    void router.push(data.path);
  }
}

onMounted(() => {
  window.addEventListener('message', onAnnexMessage);
  void requestTicket();
});
onUnmounted(() => window.removeEventListener('message', onAnnexMessage));
</script>

<style scoped>
.embed-shell {
  position: relative;
  width: 100%;
  min-height: 80vh;
  height: calc(100vh - 210px);
  border: 1px solid var(--yd-border, #e2e8f0);
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.embed-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(248, 250, 252, 0.9);
  z-index: 5;
}
.embed-frame {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
  background: #ffffff;
}
.gj-module-bar {
  margin-bottom: 12px;
}
.gj-module-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--yd-text-secondary, #475569);
}
</style>
