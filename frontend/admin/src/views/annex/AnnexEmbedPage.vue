<template>
  <YdPage :title="pageTitle" :subtitle="pageSubtitle" surface="elevated">
    <a-alert
      v-if="!embedUrl"
      type="warning"
      show-icon
      class="mb-4"
      :message="`${annexLabel} 未部署`"
      :description="deployHint"
    />
    <a-alert
      v-else-if="ticketError"
      type="error"
      show-icon
      class="mb-4"
      message="票据握手失败"
      :description="`${ticketError}（附属本地登录已停用，须从本主控台进入）`"
    />
    <a-alert
      v-else
      type="info"
      show-icon
      class="mb-4"
      :message="`附属嵌入 · ${ticketReady ? '票据已签发' : '票据签发中'}`"
      :description="`握手${annexReady ? '完成' : '等待中'}：annex.ready → 联动开始；annex.navigate → 主站路由跳转；annex.result → 回写真相层。票据 5 分钟一次性有效，附属刷新后点「重新握手」。`"
    />
    <div v-if="embedUrl" class="embed-shell">
      <iframe
        v-if="ticketReady"
        :src="embedUrlWithTicket"
        class="embed-frame"
        :title="annexLabel"
        allow="fullscreen"
        referrerpolicy="no-referrer-when-downgrade"
      />
    </div>
    <a-space class="mt-4">
      <a-button @click="router.push('/admin')">返回工作台</a-button>
      <a-button v-if="embedUrl && !ticketError" :loading="ticketLoading" @click="requestTicket">
        重新握手
      </a-button>
    </a-space>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { YdPage } from '@/components/youding';
import { apiPost } from '@/utils/api';

const route = useRoute();
const router = useRouter();
const annexReady = ref(false);
const annexTicket = ref('');
const ticketReady = ref(false);
const ticketLoading = ref(false);
const ticketError = ref('');

const ANNEX_META: Record<string, { label: string; envKey: string; desc: string }> = {
  'trade-ai': {
    label: 'TradeAI 执行台',
    envKey: 'TRADEAI_EMBED_URL',
    desc: '附属一 · AI 营销执行台',
  },
  goodjob: {
    label: 'GoodJob 执行台',
    envKey: 'GOODJOB_EMBED_URL',
    desc: '附属二 · 外贸 CRM 执行台',
  },
};

const annexKey = computed(() => String(route.meta.annexKey || ''));
const meta = computed(() => ANNEX_META[annexKey.value] || null);

const annexLabel = computed(() => meta.value?.label || '附属项目');
const pageTitle = computed(() => annexLabel.value);
const pageSubtitle = computed(() => meta.value?.desc || '附属项目接入壳页');

const embedUrl = computed(() => {
  const envKey = meta.value?.envKey;
  if (!envKey) return '';
  return String((import.meta.env as Record<string, string | undefined>)[envKey] || '').trim();
});

const embedUrlWithTicket = computed(() => {
  if (!embedUrl.value || !annexTicket.value) return '';
  const url = new URL(embedUrl.value);
  url.searchParams.set('annex_ticket', annexTicket.value);
  url.searchParams.set('annex', annexKey.value);
  return url.toString();
});

const deployHint = computed(() => {
  const envKey = meta.value?.envKey || 'TRADEAI_EMBED_URL';
  return `请在 backend .env 配置 ${envKey}。未配置时本页为 PoC 壳页。`;
});

async function requestTicket() {
  if (!embedUrl.value) return;
  ticketLoading.value = true;
  ticketError.value = '';
  try {
    const res = await apiPost<{ annex_ticket?: string }>('/annex/ticket', { annex: annexKey.value });
    if (!res?.annex_ticket) {
      ticketError.value = '后端未返回票据';
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
  width: 100%;
  min-height: 72vh;
  border: 1px solid var(--yd-border, #e5e7eb);
  border-radius: 8px;
  overflow: hidden;
  background: #0f172a;
}
.embed-frame {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
}
</style>
