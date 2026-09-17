/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="飞书集成"
    subtitle="Webhook、绑定与日报：/api/v1/feishu/*（docs §15）。此处展示绑定与日志拉取。"
    surface="elevated"
  >
    <template #actions>
      <a-button
        class="rounded-xl"
        :loading="loading"
        @click="loadAll"
      >
        刷新
      </a-button>
    </template>

    <div class="glass panel">
      <h2 class="h2">
        绑定状态
      </h2>
      <pre class="json">{{ bindJson }}</pre>
    </div>

    <div class="glass panel">
      <h2 class="h2">
        最近日志
      </h2>
      <pre class="json">{{ logsJson }}</pre>
    </div>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'
import { YdPage } from '@/components/youding';

onMounted(async () => {
  try { await apiGet('/feishu') } catch { /* 空状态 */ }
})
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { feishuAPI } from '@/api';

const loading = ref(false);
const bindRaw = ref<unknown>(null);
const logsRaw = ref<unknown>(null);

const bindJson = computed(() => JSON.stringify(bindRaw.value, null, 2));
const logsJson = computed(() => JSON.stringify(logsRaw.value, null, 2));

async function loadAll() {
  loading.value = true;
  try {
    const [b, l] = await Promise.all([
      feishuAPI.getBind().catch(() => ({ data: null })),
      feishuAPI.logs({ page: 1, page_size: 20 }).catch(() => ({ data: null })),
    ]);
    bindRaw.value = b.data;
    logsRaw.value = l.data;
  } catch {
    message.error('加载飞书数据失败');
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);
</script>

<style scoped lang="scss">
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.glass {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
  backdrop-filter: blur(16px);
}
.head {
  padding: 1.25rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 1rem;
}
.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}
.sub {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
}
.code {
  font-size: 0.78rem;
  background: rgba(15, 23, 42, 0.06);
  padding: 0.1rem 0.35rem;
  border-radius: 6px;
}
.panel {
  padding: 1.25rem 1.5rem;
}
.h2 {
  margin: 0 0 1rem;
  font-size: 1.05rem;
  font-weight: 600;
}
.json {
  margin: 0;
  font-size: 0.8rem;
  overflow: auto;
  max-height: 240px;
  background: rgba(15, 23, 42, 0.04);
  padding: 1rem;
  border-radius: 12px;
}
</style>
