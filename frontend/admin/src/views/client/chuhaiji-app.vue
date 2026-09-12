<template>
  <YdPage surface="elevated">
  <div class="chj-app">
    <header class="chj-header">
      <div class="chj-brand-wrap">
        <span class="chj-brand">{{ brandName }}</span>
        <span class="chj-app-tag">出海计</span>
      </div>
      <button type="button" class="chj-link" @click="goDesktop">桌面版</button>
    </header>

    <section class="chj-panel" v-show="tab === 'assistant'">
      <div ref="chatEl" class="chj-chat">
        <div v-for="(m, i) in messages" :key="i" class="chj-msg" :class="m.role">
          <p class="whitespace-pre-wrap">{{ m.text }}</p>
          <p v-if="m.disclaimer" class="chj-disclaimer">{{ m.disclaimer }}</p>
        </div>
      </div>
      <div class="chj-chips">
        <button v-for="q in chips" :key="q" type="button" @click="ask(q)">{{ q }}</button>
      </div>
      <form class="chj-input-row" @submit.prevent="sendChat">
        <button type="button" class="chj-voice" title="语音输入" @click="startVoice" aria-label="语音输入">
          <YdNavIcon name="AudioOutlined" size="sm" />
        </button>
        <input v-model="chatInput" placeholder="问出口、蓝海、询盘…" />
        <button type="submit" :disabled="chatLoading">发送</button>
      </form>
    </section>

    <section class="chj-panel" v-show="tab === 'today'">
      <p class="chj-sub">今日待办</p>
      <ul v-if="todos.length" class="chj-todos">
        <li v-for="t in todos" :key="t.id" @click="openPath(t.path)">
          <span :class="['dot', t.priority]"></span>
          <span>{{ t.title }}</span>
        </li>
      </ul>
      <p v-else class="chj-muted">暂无待办，去助手问问下一步</p>
      <div v-if="blueHint" class="chj-card">
        <p class="text-xs text-gray-500">出海参谋 · 蓝海提示</p>
        <p class="font-medium">{{ blueHint.country_label || blueHint.country }} · {{ blueHint.category }}</p>
        <p class="text-sm text-gray-600">{{ blueHint.reason }}</p>
        <p v-if="disclaimer" class="chj-disclaimer">{{ disclaimer }}</p>
      </div>
    </section>

    <section class="chj-panel" v-show="tab === 'publish'">
      <p class="chj-sub">发布枢纽</p>
      <button type="button" class="chj-action" @click="openPath('/client/content')">内容发布中心</button>
      <button type="button" class="chj-action secondary" @click="openPath('/client/products')">管理产品</button>
      <p class="chj-muted">完整进度与多平台任务请在内容页查看</p>
    </section>

    <section class="chj-panel" v-show="tab === 'profile'">
      <p class="chj-sub">我的</p>
      <button type="button" class="chj-action" @click="openPath('/client/settings')">账号与设置</button>
      <button type="button" class="chj-action secondary" @click="openPath('/client/referral')">邀请好友</button>
      <button type="button" class="chj-action secondary" @click="openPath('/client/onboarding')">开通向导</button>
      <button type="button" class="chj-action danger" @click="logout">退出登录</button>
      <p v-if="pushMode" class="chj-muted">Push：{{ pushMode }}</p>
      <button type="button" class="chj-action secondary" @click="testPush">测试推送</button>
      <button type="button" class="chj-action secondary" @click="refreshOfflineCache">刷新离线询盘</button>
      <p v-if="offlineCount >= 0" class="chj-muted">离线缓存：{{ offlineCount }} 条待回复询盘</p>
    </section>

    <nav class="chj-tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        :class="{ active: tab === t.id }"
        @click="switchTab(t.id)"
      >
        <YdNavIcon :name="t.icon" size="sm" class="chj-tab-icon" />
        <span class="label">{{ t.label }}</span>
      </button>
    </nav>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { YdNavIcon, YdPage } from '@/components/youding';
import { useAuthStore } from '@/stores/auth'
import { getAuthToken } from '@/utils/api'
import { assistantGreeting } from '@/constants/sales-assistant-brand'

type TabId = 'assistant' | 'today' | 'publish' | 'profile'
type Msg = { role: 'user' | 'assistant'; text: string; disclaimer?: string }

const router = useRouter()
const auth = useAuthStore()
const tab = ref<TabId>('assistant')
const brandName = ref('您的公司')
const pushMode = ref('')
const chatInput = ref('')
const chatLoading = ref(false)
const chatEl = ref<HTMLElement | null>(null)
const todos = ref<{ id: string; title: string; path: string; priority: string }[]>([])
const blueHint = ref<{ country?: string; country_label?: string; category?: string; reason?: string } | null>(null)
const disclaimer = ref('')
const offlineCount = ref(-1)

const tabs = [
  { id: 'assistant' as TabId, label: '助手', icon: 'RobotOutlined' },
  { id: 'today' as TabId, label: '今日', icon: 'CalendarOutlined' },
  { id: 'publish' as TabId, label: '发布', icon: 'EditOutlined' },
  { id: 'profile' as TabId, label: '我的', icon: 'UserOutlined' },
]

const chips = ['保温板能出口沙特吗？', '混凝土蓝海市场', '帮我回一条询盘']

const messages = ref<Msg[]>([
  { role: 'assistant', text: `${assistantGreeting(brandName.value)} 说出目标，我来查数据或起草回复。` },
])

function syncAssistantWelcome() {
  if (messages.value[0]?.role === 'assistant') {
    messages.value[0].text = `${assistantGreeting(brandName.value)} 说出目标，我来查数据或起草回复。`
  }
}

watch(brandName, () => syncAssistantWelcome())

function authHeaders(): Record<string, string> {
  const tk = getAuthToken()
  return {
    'Content-Type': 'application/json',
    ...(tk ? { Authorization: `Bearer ${tk}` } : {}),
  }
}

async function apiGet(path: string) {
  const res = await fetch(path, { headers: authHeaders() })
  const j = await res.json()
  return j.data ?? j
}

async function loadConfig() {
  try {
    const res = await fetch('/api/v1/client/branding', { headers: authHeaders() })
    const body = await res.json()
    const data = body.data ?? body
    if (data.company_name) brandName.value = data.company_name
  } catch {}
  try {
    const d = await apiGet('/api/v1/app/v1/config')
    if (brandName.value === '您的公司' && d.app_name) brandName.value = d.app_name
    pushMode.value = d.push?.provider || ''
  } catch {}
  syncAssistantWelcome()
}

async function loadHome() {
  try {
    const d = await apiGet('/api/v1/app/v1/home')
    if (d.brand?.name) brandName.value = d.brand.name
  } catch {}
}

async function loadToday() {
  try {
    const d = await apiGet('/api/v1/app/v1/today')
    todos.value = d.todos || []
    blueHint.value = d.blue_ocean_hint || null
    disclaimer.value = d.disclaimer || ''
  } catch {}
}

function detectPlatform(): string {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('android')) return 'android'
  if (/iphone|ipad|ipod/.test(ua)) return 'ios'
  return 'web'
}

async function registerDevice() {
  const tk = getAuthToken()
  if (!tk) return
  let token =
    localStorage.getItem('chuhaiji_device_token') ||
    `web-${crypto.randomUUID?.() || Date.now()}`
  localStorage.setItem('chuhaiji_device_token', token)
  try {
    await fetch('/api/v1/app/v1/devices/register', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        device_token: token,
        platform: detectPlatform(),
        app_version: '1.0.0-pwa',
      }),
    })
  } catch {}
}

async function refreshOfflineCache() {
  try {
    const d = await apiGet('/api/v1/app/v1/inquiries/offline?limit=80')
    const items = d.items || []
    localStorage.setItem('chuhaiji_offline_inquiries', JSON.stringify(items))
    localStorage.setItem('chuhaiji_offline_cached_at', d.cached_at || '')
    offlineCount.value = items.length
  } catch {
    const raw = localStorage.getItem('chuhaiji_offline_inquiries')
    offlineCount.value = raw ? JSON.parse(raw).length : 0
  }
}

async function testPush() {
  try {
    const d = await fetch('/api/v1/app/v1/push/test', {
      method: 'POST',
      headers: authHeaders(),
    })
    const j = await d.json()
    alert(j.message || '已触发测试推送')
  } catch {
    alert('推送测试失败')
  }
}

function startVoice() {
  type SpeechRec = {
    continuous: boolean
    interimResults: boolean
    lang: string
    start(): void
    stop(): void
    onresult: ((ev: { results: SpeechRecognitionResultList }) => void) | null
  }
  type SpeechRecCtor = new () => SpeechRec
  const win = window as Window & { SpeechRecognition?: SpeechRecCtor; webkitSpeechRecognition?: SpeechRecCtor }
  const Ctor = win.SpeechRecognition || win.webkitSpeechRecognition
  if (!Ctor) {
    alert('当前浏览器不支持语音，请直接输入文字')
    return
  }
  const rec = new Ctor()
  rec.lang = 'zh-CN'
  rec.onresult = async (ev: { results: SpeechRecognitionResultList }) => {
    const text = ev.results[0][0].transcript
    try {
      const res = await fetch('/api/v1/app/v1/voice/transcribe', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ text }),
      })
      const j = await res.json()
      chatInput.value = j.data?.text || text
    } catch {
      chatInput.value = text
    }
  }
  rec.start()
}

function switchTab(id: TabId) {
  tab.value = id
  if (id === 'today') void loadToday()
}

function openPath(path: string) {
  router.push(path)
}

function goDesktop() {
  router.push('/client/dashboard')
}

async function logout() {
  await auth.logout()
  router.push('/login')
}

async function scrollChat() {
  await nextTick()
  if (chatEl.value) chatEl.value.scrollTop = chatEl.value.scrollHeight
}

async function ask(text: string) {
  chatInput.value = text
  await sendChat()
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value) return
  messages.value.push({ role: 'user', text })
  chatInput.value = ''
  chatLoading.value = true
  await scrollChat()
  try {
    const res = await fetch('/api/v1/app/v1/assistant/chat', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ message: text }),
    })
    const j = await res.json()
    const d = j.data ?? j
    messages.value.push({
      role: 'assistant',
      text: d.reply || d.message || JSON.stringify(d),
      disclaimer: d.disclaimer,
    })
  } catch {
    messages.value.push({ role: 'assistant', text: '网络异常，请稍后重试。' })
  } finally {
    chatLoading.value = false
    await scrollChat()
  }
}

onMounted(() => {
  void loadConfig()
  void loadHome()
  void registerDevice()
  void refreshOfflineCache()
})
</script>

<style scoped>
.chj-app {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
  max-width: 480px;
  margin: 0 auto;
}
.chj-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
}
.chj-brand-wrap { display: flex; flex-direction: column; gap: 2px; }
.chj-brand { font-weight: 700; color: #1e40af; }
.chj-app-tag { font-size: 11px; color: #64748b; letter-spacing: 0.02em; }
.chj-link { font-size: 12px; color: #64748b; }
.chj-panel {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 80px;
}
.chj-sub { font-size: 13px; color: #64748b; margin-bottom: 12px; }
.chj-chat {
  background: #fff;
  border-radius: 16px;
  padding: 12px;
  min-height: 220px;
  max-height: 50vh;
  overflow-y: auto;
  margin-bottom: 8px;
}
.chj-msg { margin-bottom: 10px; font-size: 14px; }
.chj-msg.user { text-align: right; color: #1e3a8a; }
.chj-msg.assistant { color: #334155; }
.chj-disclaimer { font-size: 11px; color: #94a3b8; margin-top: 4px; }
.chj-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.chj-chips button {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #eff6ff;
  color: #2a6b60;
  border: 1px solid #bfdbfe;
}
.chj-voice {
  padding: 8px 10px;
  border-radius: 8px;
  background: #f1f5f9;
  font-size: 16px;
}
.chj-input-row {
  display: flex;
  gap: 8px;
  background: #fff;
  padding: 8px;
  border-radius: 12px;
}
.chj-input-row input {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 14px;
}
.chj-input-row button {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 14px;
}
.chj-todos { list-style: none; padding: 0; margin: 0 0 16px; }
.chj-todos li {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; }
.dot.high { background: #ef4444; }
.chj-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #e2e8f0;
}
.chj-action {
  display: block;
  width: 100%;
  text-align: left;
  padding: 14px 16px;
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border-radius: 12px;
  margin-bottom: 8px;
  font-size: 15px;
}
.chj-action.secondary {
  background: #fff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}
.chj-action.danger {
  background: #fff;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.chj-muted { font-size: 12px; color: #94a3b8; margin-top: 8px; }
.chj-tabs {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: #fff;
  border-top: 1px solid #e2e8f0;
  padding: 6px 0 calc(6px + env(safe-area-inset-bottom));
}
.chj-tabs button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px;
  font-size: 10px;
  color: #64748b;
}
.chj-tabs button.active { color: var(--uj-brand, #4a9b8c); font-weight: 600; }
.chj-tabs .icon { font-size: 18px; }
</style>
