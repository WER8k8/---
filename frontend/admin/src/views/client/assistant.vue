/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage :title="pageTitle" subtitle="全屏对话 · 出口研判、蓝海市场、询盘回复" surface="elevated">
  <div class="assistant-page">
    <div class="chat-card">
      <div ref="listEl" class="chat-list">
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="chat-row"
          :class="m.role"
        >
          <p class="whitespace-pre-wrap">{{ m.text }}</p>
          <p v-if="m.disclaimer" class="disclaimer">{{ m.disclaimer }}</p>
        </div>
      </div>
      <form class="chat-form" @submit.prevent="send">
        <textarea
          v-model="input"
          rows="2"
          placeholder="出口可行性、蓝海市场、询盘回复…"
        />
        <button type="submit" :disabled="loading">发送</button>
      </form>
    </div>

    <div class="quick-chips">
      <button
        v-for="q in samples"
        :key="q"
        type="button"
        class="chip"
        @click="ask(q)"
      >
        {{ q }}
      </button>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { YdPage } from '@/components/youding';
import { getAuthToken } from '@/utils/api';
import { useTenantBrand } from '@/composables/useTenantBrand';
import { useUbrainChatContext } from '@/composables/useUbrainChatContext';

const tenantBrand = useTenantBrand();
const ubrainCtx = useUbrainChatContext();
const pageTitle = computed(() => tenantBrand.assistantTitle.value);

type Msg = { role: 'user' | 'assistant'; text: string; disclaimer?: string }

const input = ref('')
const loading = ref(false)
const listEl = ref<HTMLElement | null>(null)
const samples = [
  '保温板能出口沙特吗？',
  '混凝土蓝海市场推荐',
  '域名 SSL 好了没',
]
const messages = ref<Msg[]>([
  {
    role: 'assistant',
    text: `${tenantBrand.greetingMessage.value} 说出目标，我来查数据或起草回复。`,
  },
])

watch(
  () => tenantBrand.greetingMessage.value,
  (greeting) => {
    if (messages.value[0]?.role === 'assistant') {
      messages.value[0].text = `${greeting} 说出目标，我来查数据或起草回复。`
    }
  },
)

async function ask(text: string) {
  input.value = text
  await send()
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  await scrollBottom()
  try {
    const tk = getAuthToken()
    const res = await fetch('/api/v1/ubrain/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(tk ? { Authorization: `Bearer ${tk}` } : {}),
      },
      body: JSON.stringify(ubrainCtx.buildBody(text, messages.value)),
    })
    const body = await res.json()
    const data = body.data || body
    ubrainCtx.applyReply(data)
    messages.value.push({
      role: 'assistant',
      text: data.reply || '暂无回复',
      disclaimer: data.disclaimer,
    })
  } catch {
    messages.value.push({ role: 'assistant', text: '请求失败，请检查网络与登录。' })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

async function scrollBottom() {
  await nextTick()
  listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })
}
</script>

<style scoped>
.assistant-page {
  max-width: 640px;
  margin: 0 auto;
}
.chat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  min-height: 420px;
  display: flex;
  flex-direction: column;
}
.chat-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  max-height: 55vh;
}
.chat-row.user p {
  background: #dbeafe;
  margin-left: 24px;
  padding: 10px 12px;
  border-radius: 12px;
}
.chat-row.assistant p {
  background: #f1f5f9;
  margin-right: 24px;
  padding: 10px 12px;
  border-radius: 12px;
}
.disclaimer {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 4px;
}
.chat-form {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #f1f5f9;
}
.chat-form textarea {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 8px;
  resize: none;
}
.chat-form button {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0 16px;
}
.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.chip {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
}
</style>
