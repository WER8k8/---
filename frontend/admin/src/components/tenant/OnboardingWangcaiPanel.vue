<template>
  <div class="wangcai-panel">
    <p class="wangcai-panel__hint">
      此处仅预览 <strong>Trade Q&amp;A 智能顾问</strong>（与开户 IM 指引分离）。客户在官网右下角看到的出口问答与此同源。
    </p>
    <div class="wangcai-panel__chips">
      <button
        v-for="p in prompts"
        :key="p.id"
        type="button"
        class="wangcai-chip"
        :disabled="loading"
        @click="ask(p.label)"
      >
        {{ p.label }}
      </button>
    </div>

    <div v-if="messages.length" class="wangcai-panel__chat">
      <div v-for="(m, i) in messages" :key="i" class="wangcai-msg" :class="m.role">
        <p class="whitespace-pre-wrap">{{ m.text }}</p>
      </div>
    </div>

    <form class="wangcai-panel__input" @submit.prevent="ask(input)">
      <a-input
        v-model:value="input"
        placeholder="例如：保温板出口越南可行性？"
        :disabled="loading"
      />
      <a-button type="primary" html-type="submit" :loading="loading">问旺财</a-button>
    </form>

    <p v-if="disclaimer" class="wangcai-panel__disclaimer">{{ disclaimer }}</p>

    <div class="wangcai-panel__actions">
      <a-button type="primary" :disabled="!previewDone && !messages.length" @click="emit('done')">
        {{ previewDone ? '继续发布首篇' : '完成预览并继续' }}
      </a-button>
      <a-button v-if="sitePreviewUrl" type="link" :href="sitePreviewUrl" target="_blank" rel="noopener">
        新窗口打开官网预览
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { message } from 'ant-design-vue';
import { apiPost } from '@/utils/api';

interface WangcaiPrompt {
  id: string;
  label: string;
}

const props = defineProps<{
  productHint?: string;
  sitePreviewUrl?: string;
  previewDone?: boolean;
  initialPrompts?: WangcaiPrompt[];
}>();

const emit = defineEmits<{ done: [] }>();

const prompts = ref<WangcaiPrompt[]>(props.initialPrompts || []);
const messages = ref<{ role: 'user' | 'assistant'; text: string }[]>([]);
const input = ref('');
const loading = ref(false);
const disclaimer = ref('');

onMounted(() => {
  if (!prompts.value.length) {
    prompts.value = [
      { id: 'blue', label: `${props.productHint || '产品'}哪些国家好卖？` },
      { id: 'export', label: `出口${props.productHint || '产品'}要哪些证书？` },
    ];
  }
});

async function ask(text: string) {
  const q = text.trim();
  if (!q || loading.value) return;
  input.value = '';
  messages.value.push({ role: 'user', text: q });
  loading.value = true;
  try {
    const data = await apiPost<{
      reply?: string;
      disclaimer?: string;
      intent?: string;
    }>('/tenants/self/onboarding-chain/wangcai-preview', { message: q });
    messages.value.push({
      role: 'assistant',
      text: data?.reply || '暂无回复，请稍后重试',
    });
    disclaimer.value = String(data?.disclaimer || '');
    message.success('旺财已回复（与公开站同源）');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '旺财预览失败');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
.wangcai-panel {
  &__hint {
    font-size: 13px;
    color: #64748b;
    margin: 0 0 12px;
  }
  &__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }
  &__chat {
    max-height: 240px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 12px;
    background: #f8fafc;
  }
  &__input {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }
  &__disclaimer {
    font-size: 11px;
    color: #94a3b8;
    margin: 0 0 12px;
  }
  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    justify-content: flex-end;
  }
}
.wangcai-chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  cursor: pointer;
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}
.wangcai-msg {
  margin-bottom: 10px;
  font-size: 13px;
  &.user p {
    color: #1e293b;
    font-weight: 500;
  }
  &.assistant p {
    color: #334155;
  }
}
</style>
