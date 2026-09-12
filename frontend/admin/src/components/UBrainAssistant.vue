<template>
  <Teleport to="body">
    <div
      ref="rootEl"
      class="ubrain-root"
      :class="{ dragging, open }"
      role="complementary"
      aria-label="悬浮卖货智能助手"
      :style="rootStyle"
    >
      <span v-if="!open" class="ubrain-hint">
        <AssistantMascot :size="18" mood="idle" class="hint-mascot" />
        {{ ASSISTANT_MASCOT.name }}
      </span>
      <div v-if="open" class="ubrain-panel">
        <header
          class="ubrain-header"
          title="按住拖动"
          @pointerdown="onHeaderPointerDown"
        >
          <div class="header-brand">
            <AssistantMascot :size="36" :mood="loading ? 'think' : 'happy'" />
            <div>
              <strong class="text-sm">{{ assistantTitleText }}</strong>
              <p class="text-[10px] text-slate-500 mt-0.5">{{ ASSISTANT_MASCOT.tagline }}</p>
            </div>
          </div>
          <div class="header-actions">
            <span class="drag-tip">⠿ 可拖动</span>
            <button type="button" class="ubrain-link" @click="goFullCopilot">完整版</button>
          </div>
        </header>
        <div ref="scrollEl" class="ubrain-messages">
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="ubrain-msg"
            :class="msg.role"
          >
            <AssistantMascot
              v-if="msg.role === 'assistant'"
              :size="28"
              mood="happy"
              class="msg-avatar"
            />
            <div class="msg-body">
              <p class="whitespace-pre-wrap text-sm">{{ msg.text }}</p>
              <p v-if="msg.disclaimer" class="text-[10px] text-gray-400 mt-1">{{ msg.disclaimer }}</p>
            </div>
          </div>
          <div v-if="loading" class="ubrain-msg assistant">
            <AssistantMascot :size="28" mood="think" class="msg-avatar" />
            <p class="text-xs text-gray-400">{{ ASSISTANT_MASCOT.thinking }}</p>
          </div>
        </div>
        <form class="ubrain-input" @submit.prevent="send">
          <input
            v-model="input"
            type="text"
            placeholder="例如：保温板能出口沙特吗？"
            :disabled="loading"
          />
          <button type="submit" :disabled="loading || !input.trim()">发送</button>
        </form>
      </div>
      <button
        type="button"
        class="ubrain-fab"
        :class="{ open, pulsing: fabPulsing }"
        :aria-label="assistantTitleText"
        :aria-expanded="open"
        title="点击打开 · 按住拖动"
        @pointerdown="onFabPointerDown"
      >
        <AssistantMascot v-if="!open" :size="44" :mood="loading ? 'think' : 'happy'" />
        <span v-else class="fab-close" aria-hidden="true">×</span>
      </button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthToken } from '@/utils/api'
import { useAssistantPanel } from '@/composables/useAssistantPanel'
import { useFloatingDrag } from '@/composables/useFloatingDrag'
import { useTenantBrand } from '@/composables/useTenantBrand'
import { useUbrainChatContext } from '@/composables/useUbrainChatContext'
import AssistantMascot from '@/components/assistant/AssistantMascot.vue'
import { ASSISTANT_MASCOT } from '@/constants/assistant-mascot'

type Msg = { role: 'user' | 'assistant'; text: string; disclaimer?: string }

const router = useRouter()
const tenantBrand = useTenantBrand()
const ubrainCtx = useUbrainChatContext()
const panel = useAssistantPanel()
const open = panel.isOpen
const fabPulsing = computed(() => {
  if (import.meta.env.DEV) return false
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return false
  }
  return !open.value && !dragging.value
})
const input = ref('')
const loading = ref(false)
const scrollEl = ref<HTMLElement | null>(null)
const rootEl = ref<HTMLElement | null>(null)

function togglePanel() {
  panel.toggle()
}

const { pos, dragging, beginDrag, clamp } = useFloatingDrag(rootEl, open, {
  onFabClick: togglePanel,
})

const rootStyle = computed(() => ({
  left: `${pos.value.x}px`,
  top: `${pos.value.y}px`,
}))

const assistantTitleText = computed(() => tenantBrand.assistantTitle.value)

const messages = ref<Msg[]>([
  {
    role: 'assistant',
    text: tenantBrand.greetingMessage.value,
  },
])

watch(
  () => tenantBrand.greetingMessage.value,
  (text) => {
    if (messages.value[0]?.role === 'assistant') {
      messages.value[0].text = text
    }
  },
)

watch(open, async () => {
  await nextTick()
  pos.value = clamp(pos.value.x, pos.value.y)
})

function onFabPointerDown(e: PointerEvent) {
  beginDrag(e, 'fab', e.currentTarget as HTMLElement)
}

function onHeaderPointerDown(e: PointerEvent) {
  beginDrag(e, 'header', e.currentTarget as HTMLElement)
}

function goFullCopilot() {
  panel.close()
  router.push('/client/copilot')
}

async function send() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', text })
  input.value = ''
  loading.value = true
  await nextTick()
  scrollEl.value?.scrollTo({ top: 99999, behavior: 'smooth' })

  try {
    const tk = getAuthToken()
    const csrfEcho = sessionStorage.getItem('csrf_echo_token')
    const res = await fetch('/api/v1/ubrain/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // FIX-CSRF: token 哨兵 'cookie' 时发 "Bearer cookie" 会被后端判为
        // 无效令牌 401 —— Cookie 模式认证走 HttpOnly cookie（credentials: 同源），
        // 改为回放 X-CSRF-Token 通过 double-submit 校验。
        ...(tk && tk !== 'cookie' ? { Authorization: `Bearer ${tk}` } : {}),
        ...(tk === 'cookie' && csrfEcho ? { 'X-CSRF-Token': csrfEcho } : {}),
      },
      body: JSON.stringify(ubrainCtx.buildBody(text, messages.value)),
    })
    const body = await res.json()
    const data = body.data || body
    ubrainCtx.applyReply(data)
    messages.value.push({
      role: 'assistant',
      text: data.reply || '暂时无法回答，请稍后再试。',
      disclaimer: data.disclaimer || undefined,
    })
  } catch {
    messages.value.push({
      role: 'assistant',
      text: '网络异常，请检查登录状态后重试。',
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollEl.value?.scrollTo({ top: 99999, behavior: 'smooth' })
  }
}
</script>

<style scoped>
.ubrain-root {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
  touch-action: none;
  user-select: none;
}
.ubrain-root.dragging {
  cursor: grabbing;
}
.ubrain-root.dragging * {
  cursor: grabbing !important;
}
.ubrain-hint {
  pointer-events: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
  padding: 3px 10px 3px 6px;
  border-radius: 999px;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.18);
}
.hint-mascot {
  margin-top: -1px;
}
.ubrain-fab {
  pointer-events: auto;
  width: 60px;
  height: 60px;
  border-radius: 9999px;
  background: linear-gradient(145deg, #fffbeb, #fef3c7);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 28px rgba(245, 158, 11, 0.38);
  border: 2px solid #fff;
  cursor: grab;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  overflow: hidden;
  flex-shrink: 0;
}
.ubrain-fab.pulsing {
  animation: fab-pulse 2.4s ease-in-out infinite;
}
.ubrain-fab:hover {
  transform: scale(1.06);
  box-shadow: 0 12px 32px rgba(245, 158, 11, 0.48);
}
.ubrain-fab.open {
  background: #475569;
  animation: none;
}
.ubrain-root.dragging .ubrain-fab:hover {
  transform: none;
}
.fab-close {
  font-size: 1.75rem;
  line-height: 1;
  color: #fff;
  font-weight: 300;
}
@keyframes fab-pulse {
  0%,
  100% {
    box-shadow: 0 10px 28px rgba(245, 158, 11, 0.35);
  }
  50% {
    box-shadow: 0 10px 32px rgba(245, 158, 11, 0.55), 0 0 0 6px rgba(251, 191, 36, 0.18);
  }
}
.ubrain-panel {
  pointer-events: auto;
  width: min(380px, calc(100vw - 40px));
  max-height: min(70vh, 520px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.22);
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  order: -1;
}
.ubrain-header {
  padding: 12px 14px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  cursor: grab;
}
.ubrain-root.dragging .ubrain-header {
  cursor: grabbing;
}
.header-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.header-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}
.drag-tip {
  font-size: 10px;
  color: #a8a29e;
  line-height: 1;
}
.ubrain-link {
  pointer-events: auto;
  font-size: 11px;
  color: var(--uj-brand, #4a9b8c);
  background: none;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  padding: 2px 0;
}
.ubrain-link:hover {
  text-decoration: underline;
}
.ubrain-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 200px;
  cursor: default;
  user-select: text;
}
.ubrain-msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 10px;
}
.ubrain-msg.user {
  flex-direction: row-reverse;
}
.msg-avatar {
  margin-top: 2px;
}
.msg-body {
  max-width: calc(100% - 40px);
}
.ubrain-msg.user .msg-body p {
  background: #dbeafe;
  padding: 8px 10px;
  border-radius: 12px 12px 4px 12px;
}
.ubrain-msg.assistant .msg-body p {
  background: #fffbeb;
  padding: 8px 10px;
  border-radius: 12px 12px 12px 4px;
  border: 1px solid #fef3c7;
}
.ubrain-input {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid #f1f5f9;
  cursor: default;
}
.ubrain-input input {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
  user-select: text;
}
.ubrain-input button {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0 14px;
  font-size: 14px;
  cursor: pointer;
}
</style>
