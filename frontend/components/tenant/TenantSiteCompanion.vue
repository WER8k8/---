<template>
  <div
    class="site-companion"
    :class="{
      'site-companion--open': panelOpen,
      'site-companion--nudge': showScrollNudge,
      'site-companion--rtl': isRtl,
    }"
    :style="{ '--accent': accentColor }"
    aria-live="polite"
  >
    <!-- 对话气泡 -->
    <Transition name="companion-bubble">
      <div v-if="bubbleVisible && !panelOpen" class="site-companion-bubble" @click="openPanel">
        <p>{{ currentMessage }}</p>
        <span class="site-companion-bubble-tail" />
      </div>
    </Transition>

    <!-- 联系面板（官网主体之外浮层） -->
    <Transition name="companion-panel">
      <div v-if="panelOpen" class="site-companion-panel">
        <div class="site-companion-panel-head">
          <strong>{{ companyName }}</strong>
          <span class="site-companion-panel-sub">{{ ui('panel_sub') }}</span>
          <button type="button" class="site-companion-close" :aria-label="ui('close')" @click="closePanel">×</button>
        </div>

        <div class="site-companion-tabs">
          <button
            type="button"
            :class="{ active: panelTab === 'contact' }"
            @click="panelTab = 'contact'"
          >
            {{ ui('tab_contact') }}
          </button>
          <button
            v-if="tradeQaEnabled"
            type="button"
            :class="{ active: panelTab === 'ask' }"
            @click="switchToAsk"
          >
            {{ ui('tab_ask') }}
          </button>
        </div>

        <template v-if="panelTab === 'contact'">
        <p class="site-companion-panel-tip">{{ panelTip }}</p>
        <div class="site-companion-actions">
          <template v-if="visibleContactChannels.length">
            <a
              v-for="ch in visibleContactChannels"
              :key="ch.channel_type + ch.value"
              :href="channelHref(ch)"
              :target="channelExternal(ch) ? '_blank' : undefined"
              :rel="channelExternal(ch) ? 'noopener noreferrer' : undefined"
              class="site-companion-action"
              :class="channelClass(ch.channel_type)"
              @click="onChannelClick(ch, $event)"
            >
              <span class="site-companion-action-icon">{{ channelIcon(ch.channel_type) }}</span>
              <span>
                <em>{{ ch.label }}</em>
                <small>{{ channelSubtext(ch) }}</small>
              </span>
            </a>
          </template>
          <p v-else class="site-companion-chat-hint">{{ ui('cn_no_contact') }}</p>
        </div>
        </template>

        <template v-else>
          <div class="site-companion-chat">
            <div ref="chatScroll" class="site-companion-chat-log">
              <p v-if="!chatMessages.length" class="site-companion-chat-hint">
              {{ ui('chat_hint') }}
              </p>
              <div
                v-for="(msg, idx) in chatMessages"
                :key="idx"
                class="site-companion-chat-row"
                :class="msg.role === 'user' ? 'is-user' : 'is-bot'"
              >
                <p>{{ msg.text }}</p>
              </div>
              <p v-if="chatLoading" class="site-companion-chat-hint">{{ ui('chat_loading') }}</p>
            </div>
            <div v-if="quickPrompts.length" class="site-companion-chips">
              <button
                v-for="p in quickPrompts"
                :key="p.id"
                type="button"
                class="site-companion-chip"
                :disabled="chatLoading"
                @click="sendAsk(p.message)"
              >
                {{ p.label || p.label_en }}
              </button>
            </div>
            <form class="site-companion-ask-form" @submit.prevent="submitAsk">
              <input
                v-model="askInput"
                type="text"
                maxlength="800"
                :placeholder="ui('ask_placeholder')"
                :disabled="chatLoading || !tenantDomain"
              />
              <button type="submit" :disabled="chatLoading || !askInput.trim() || !tenantDomain">
                {{ ui('ask_button') }}
              </button>
            </form>
            <p v-if="chatDisclaimer" class="site-companion-disclaimer">{{ chatDisclaimer }}</p>
          </div>
        </template>
      </div>
    </Transition>

    <!-- 旺财 mascot（活泼灵动 · 参考 meoo 挂件） -->
    <button
      type="button"
      class="site-companion-mascot"
      :aria-label="companyName + ' ' + ui('mascot_aria')"
      @click="togglePanel"
    >
      <span class="site-companion-glow" :style="{ '--accent': accent }" />
      <svg class="site-companion-cat" viewBox="0 0 120 120" aria-hidden="true">
        <defs>
          <linearGradient id="wc-body" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" :stop-color="accentDeep" />
            <stop offset="55%" :stop-color="accentMid" />
            <stop offset="100%" :stop-color="accentLight" />
          </linearGradient>
          <linearGradient id="wc-rim" x1="100%" y1="20%" x2="0%" y2="80%">
            <stop offset="0%" :stop-color="accentColor" />
            <stop offset="45%" stop-color="#a78bfa" />
            <stop offset="100%" stop-color="#38bdf8" />
          </linearGradient>
        </defs>
        <ellipse cx="60" cy="72" rx="38" ry="34" fill="url(#wc-body)" />
        <path d="M28 38 L38 58 L48 36 Z" fill="#0f172a" />
        <path d="M92 38 L82 58 L72 36 Z" fill="#0f172a" />
        <circle cx="44" cy="68" r="11" fill="#fff" />
        <circle cx="76" cy="68" r="11" fill="#fff" />
        <circle cx="46" cy="70" r="5" fill="#0f172a" />
        <circle cx="78" cy="70" r="5" fill="#0f172a" />
        <circle cx="48" cy="66" r="2" fill="#fff" />
        <circle cx="80" cy="66" r="2" fill="#fff" />
        <ellipse cx="60" cy="82" rx="5" ry="3" fill="#fda4af" />
        <path
          d="M52 88 Q60 94 68 88"
          fill="none"
          stroke="#64748b"
          stroke-width="2"
          stroke-linecap="round"
        />
        <ellipse
          cx="88"
          cy="58"
          rx="14"
          ry="20"
          fill="none"
          stroke="url(#wc-rim)"
          stroke-width="3"
          opacity="0.85"
        />
      </svg>
      <span v-if="hasContact" class="site-companion-badge" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import {
  buildFallbackContactChannels,
  isExternalContactChannel,
} from '../../composables/useTenantVisitorContacts';

const props = withDefaults(
  defineProps<{
    companyName?: string;
    phone?: string;
    email?: string;
    whatsapp?: string;
    wechat?: string;
    qq?: string;
    accent?: string;
    productHint?: string;
    tenantDomain?: string;
    apiBase?: string;
    visitorLanguage?: string;
    visitorCountry?: string;
    cnCompliantOnly?: boolean;
    wangcaiUi?: Record<string, string>;
    contactChannels?: Array<{ channel_type: string; value: string; label: string; im_link: string }>;
    tradeQaEnabled?: boolean;
    isRtl?: boolean;
  }>(),
  {
    companyName: 'Our team',
    phone: '',
    email: '',
    whatsapp: '',
    wechat: '',
    qq: '',
    accent: '#1e3a5f',
    productHint: '',
    tenantDomain: '',
    apiBase: '/api/v1',
    visitorLanguage: 'en',
    visitorCountry: 'US',
    cnCompliantOnly: false,
    wangcaiUi: () => ({}),
    contactChannels: () => [],
    tradeQaEnabled: true,
    isRtl: false,
  },
);

const accentColor = computed(() => props.accent || '#1e3a5f');
const accentDeep = computed(() => props.accent || '#0f172a');
const accentMid = computed(() => props.accent || '#1e3a5f');
const accentLight = computed(() => props.accent || '#312e81');
const isRtl = computed(() => props.isRtl);

const FALLBACK_UI: Record<string, string> = {
  panel_sub: 'Export sales · Quick reply',
  tab_contact: 'Contact',
  tab_ask: 'Trade Q&A',
  panel_tip_default: 'Tell us quantity, specs & destination port — we reply within 24 hours.',
  contact_wa_sub: 'International chat',
  contact_wechat_sub_copied: 'ID copied!',
  contact_email_sub: 'Email',
  contact_call_sub: 'Call',
  contact_form_sub: 'Full factory details',
  contact_form_label: 'Contact form',
  chat_hint: 'Not sure about HS codes or export markets? Ask here — 20 categories × 50 countries.',
  chat_loading: 'Checking trade data…',
  ask_placeholder: 'e.g. Best markets for rock wool?',
  ask_button: 'Ask',
  error_retry: 'Sorry — try again or use the contact form.',
  error_network: 'Network error. Please use WhatsApp or the contact form.',
  mascot_aria: 'sales assistant',
  close: 'Close',
  bubble_1: 'Hi! {name} export team here — need a quotation?',
  bubble_2: 'Ask me export markets & HS codes — tap Trade Q&A.',
  bubble_3: 'Tap for WhatsApp, email or phone.',
  bubble_4: 'Free sample & datasheet for qualified projects.',
  bubble_product: 'Looking for {product}? Ask us!',
  cn_no_contact: '请通过页面下方联系区块留言，或稍后再试。',
  contact_qq_sub_copied: 'QQ copied!',
};

function ui(key: string, vars?: Record<string, string>): string {
  let text = props.wangcaiUi[key] || FALLBACK_UI[key] || key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replace(`{${k}}`, v);
    }
  }
  return text;
}

/** 非中文界面：气泡与联系面板强调 WhatsApp / 邮件 / 电话，不推微信 QQ */
function contactBubbleLine(): string {
  const lang = (props.visitorLanguage || 'en').slice(0, 2);
  if (lang === 'zh') {
    return ui('bubble_3');
  }
  const fromApi = ui('bubble_3');
  if (fromApi && !/WeChat|微信|QQ/i.test(fromApi)) {
    return fromApi;
  }
  const exportCopy: Record<string, string> = {
    en: 'Tap for WhatsApp, email or phone.',
    ar: 'Tap for WhatsApp, email or phone.',
    es: 'Toque para WhatsApp, email o teléfono.',
    pt: 'Toque para WhatsApp, email ou telefone.',
    ru: 'Нажмите для WhatsApp, email или звонка.',
    th: 'แตะเพื่อ WhatsApp, อีเมล หรือโทร',
    vi: 'Chạm để WhatsApp, email hoặc gọi điện.',
    id: 'Ketuk untuk WhatsApp, email, atau telepon.',
    ms: 'Ketik untuk WhatsApp, e-mel atau panggilan.',
    ja: 'WhatsApp・メール・電話はこちらをタップ。',
    ko: 'WhatsApp, 이메일, 전화는 여기를 누르세요.',
  };
  return exportCopy[lang] || exportCopy.en;
}

const panelOpen = ref(false);
const panelTab = ref<'contact' | 'ask'>('contact');
const bubbleVisible = ref(true);
const showScrollNudge = ref(false);
const messageIndex = ref(0);
const wechatCopied = ref(false);
const qqCopied = ref(false);
const askInput = ref('');
const chatLoading = ref(false);
const chatDisclaimer = ref('');
const chatMessages = ref<{ role: 'user' | 'assistant'; text: string }[]>([]);
const quickPrompts = ref<{ id: string; label_en: string; label?: string; message: string }[]>([]);
const chatScroll = ref<HTMLElement | null>(null);
let rotateTimer: ReturnType<typeof setInterval> | null = null;
let nudgeTimer: ReturnType<typeof setTimeout> | null = null;

const whatsappHref = computed(() => {
  const n = props.whatsapp.replace(/\D/g, '');
  return n ? `https://wa.me/${n}` : '';
});

const wechatId = computed(() => props.wechat.trim());
const qqId = computed(() => props.qq.trim());

type ContactChannel = {
  channel_type: string;
  value: string;
  label: string;
  im_link: string;
};

const visibleContactChannels = computed<ContactChannel[]>(() => {
  let channels: ContactChannel[];
  if (props.contactChannels?.length) {
    channels = props.contactChannels;
  } else {
    channels = buildFallbackContactChannels(
      {
        phone: props.phone,
        email: props.email,
        whatsapp: props.whatsapp,
        wechat: props.wechat,
        qq: props.qq,
      },
      {
        cnCompliantOnly: props.cnCompliantOnly,
        language: props.visitorLanguage || 'en',
      },
    );
  }
  const lang = (props.visitorLanguage || 'en').slice(0, 2);
  if (lang !== 'zh' && !props.cnCompliantOnly) {
    return channels.filter((c) => c.channel_type !== 'wechat' && c.channel_type !== 'qq');
  }
  return channels;
});

const hasContact = computed(() => visibleContactChannels.value.length > 0);

function channelIcon(type: string): string {
  const icons: Record<string, string> = {
    whatsapp: '💬',
    wechat: '🟢',
    qq: '🐧',
    phone: '📞',
    email: '✉️',
    form: '📋',
  };
  return icons[type] || '•';
}

function channelClass(type: string): string {
  if (type === 'whatsapp') return 'site-companion-action--wa';
  if (type === 'wechat') return 'site-companion-action--wechat';
  if (type === 'form') return 'site-companion-action--ghost';
  return '';
}

function channelExternal(ch: ContactChannel): boolean {
  return isExternalContactChannel(ch);
}

function channelHref(ch: ContactChannel): string {
  if (ch.channel_type === 'wechat' || ch.channel_type === 'qq') return '#';
  if (ch.channel_type === 'form') return '#contact';
  return ch.im_link || '#';
}

function channelSubtext(ch: ContactChannel): string {
  if (ch.channel_type === 'wechat') {
    return wechatCopied.value ? ui('contact_wechat_sub_copied') : ch.value;
  }
  if (ch.channel_type === 'qq') {
    return qqCopied.value ? ui('contact_qq_sub_copied') : ch.value;
  }
  if (ch.channel_type === 'whatsapp') return ui('contact_wa_sub');
  if (ch.channel_type === 'form') return ui('contact_form_sub');
  return ch.value;
}

function onChannelClick(ch: ContactChannel, event: MouseEvent) {
  if (ch.channel_type === 'wechat') {
    event.preventDefault();
    copyContactValue(ch.value, 'wechat');
    return;
  }
  if (ch.channel_type === 'qq') {
    event.preventDefault();
    copyContactValue(ch.value, 'qq');
    return;
  }
  if (ch.channel_type === 'form') {
    closePanel();
  }
}

const panelTip = computed(
  () =>
    props.productHint
    || ui('panel_tip_default'),
);

watch(
  () => props.tradeQaEnabled,
  (enabled) => {
    if (!enabled && panelTab.value === 'ask') {
      panelTab.value = 'contact';
    }
  },
  { immediate: true },
);

const messages = computed(() => {
  const name = props.companyName;
  const list = [
    ui('bubble_1', { name }),
    contactBubbleLine(),
    ui('bubble_4'),
  ];
  if (props.tradeQaEnabled) {
    list.splice(1, 0, ui('bubble_2'));
  }
  if (props.productHint) {
    list.unshift(ui('bubble_product', { product: props.productHint }));
  }
  return list;
});

const currentMessage = computed(() => messages.value[messageIndex.value % messages.value.length]);

function openPanel() {
  panelOpen.value = true;
  bubbleVisible.value = false;
}

function switchToAsk() {
  if (!props.tradeQaEnabled) return;
  panelTab.value = 'ask';
  if (!quickPrompts.value.length && props.tenantDomain) {
    loadPrompts();
  }
}

async function loadPrompts() {
  if (!props.tenantDomain || !import.meta.client) return;
  try {
    const params = new URLSearchParams();
    if (props.productHint) params.set('product_hint', props.productHint);
    if (props.visitorLanguage) params.set('language', props.visitorLanguage);
    if (props.visitorCountry) params.set('country_code', props.visitorCountry);
    const qs = params.toString() ? `?${params}` : '';
    const res = await fetch(
      `${props.apiBase}/public/tenants/${encodeURIComponent(props.tenantDomain)}/wangcai/prompts${qs}`,
      { headers: { 'Accept-Language': props.visitorLanguage || 'en' } },
    );
    const body = await res.json();
    if (res.ok) {
      quickPrompts.value = body.data?.prompts || [];
    }
  } catch {
    quickPrompts.value = [];
  }
}

function scrollChatEnd() {
  if (!chatScroll.value) return;
  chatScroll.value.scrollTop = chatScroll.value.scrollHeight;
}

async function sendAsk(text: string) {
  const message = text.trim();
  if (!message || !props.tenantDomain || chatLoading.value) return;
  chatMessages.value.push({ role: 'user', text: message });
  askInput.value = '';
  chatLoading.value = true;
  scrollChatEnd();
  try {
    const res = await fetch(
      `${props.apiBase}/public/tenants/${encodeURIComponent(props.tenantDomain)}/wangcai/ask`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept-Language': props.visitorLanguage || 'en',
        },
        body: JSON.stringify({
          message,
          product_hint: props.productHint || null,
          language: props.visitorLanguage || null,
          country_code: props.visitorCountry || null,
        }),
      },
    );
    const body = await res.json();
    const data = body.data || body;
    if (res.ok && data.reply) {
      chatMessages.value.push({ role: 'assistant', text: String(data.reply).replace(/\*\*/g, '') });
      if (data.disclaimer) chatDisclaimer.value = String(data.disclaimer);
    } else {
      chatMessages.value.push({
        role: 'assistant',
        text: body.message || ui('error_retry'),
      });
    }
  } catch {
    chatMessages.value.push({
      role: 'assistant',
      text: ui('error_network'),
    });
  } finally {
    chatLoading.value = false;
    scrollChatEnd();
  }
}

function submitAsk() {
  sendAsk(askInput.value);
}

function closePanel() {
  panelOpen.value = false;
  bubbleVisible.value = true;
}

function togglePanel() {
  if (panelOpen.value) closePanel();
  else openPanel();
}

function copyContactValue(value: string, kind: 'wechat' | 'qq') {
  if (!value || !import.meta.client) return;
  navigator.clipboard?.writeText(value).then(() => {
    if (kind === 'wechat') {
      wechatCopied.value = true;
      window.setTimeout(() => { wechatCopied.value = false; }, 2000);
    } else {
      qqCopied.value = true;
      window.setTimeout(() => { qqCopied.value = false; }, 2000);
    }
  });
}

function copyWeChat() {
  copyContactValue(wechatId.value, 'wechat');
}

function onScroll() {
  if (!import.meta.client) return;
  const y = window.scrollY;
  showScrollNudge.value = y > 280 && y < document.body.scrollHeight - 800;
}

let sectionObserver: IntersectionObserver | null = null;

function observeSections() {
  if (!import.meta.client) return;
  const targets = ['#products', '#contact', '#applications'];
  sectionObserver = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        const id = e.target.id;
        if (id === 'products') messageIndex.value = messages.value.length - 2;
        else if (id === 'contact') messageIndex.value = 1;
        else if (id === 'applications') messageIndex.value = 0;
        bubbleVisible.value = !panelOpen.value;
      }
    },
    { threshold: 0.35 },
  );
  for (const sel of targets) {
    const el = document.querySelector(sel);
    if (el) sectionObserver.observe(el);
  }
}

watch(
  () => props.visitorLanguage,
  () => {
    messageIndex.value = 0;
    bubbleVisible.value = !panelOpen.value;
    chatMessages.value = [];
    chatDisclaimer.value = '';
    wechatCopied.value = false;
    qqCopied.value = false;
    if (panelTab.value === 'ask' && props.tenantDomain) {
      loadPrompts();
    }
  },
);

onMounted(() => {
  if (!import.meta.client) return;
  rotateTimer = setInterval(() => {
    if (!panelOpen.value) {
      messageIndex.value = (messageIndex.value + 1) % messages.value.length;
    }
  }, 6000);
  window.addEventListener('scroll', onScroll, { passive: true });
  nudgeTimer = setTimeout(() => {
    showScrollNudge.value = true;
    window.setTimeout(() => {
      showScrollNudge.value = false;
    }, 2400);
  }, 3500);
  observeSections();
});

onUnmounted(() => {
  if (rotateTimer) clearInterval(rotateTimer);
  if (nudgeTimer) clearTimeout(nudgeTimer);
  sectionObserver?.disconnect();
  if (import.meta.client) window.removeEventListener('scroll', onScroll);
});
</script>

<style scoped>
.site-companion {
  position: fixed;
  right: max(12px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  pointer-events: none;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}

.site-companion--rtl {
  right: auto;
  left: max(12px, env(safe-area-inset-left));
  align-items: flex-start;
}

.site-companion--rtl .site-companion-bubble {
  border-radius: 16px 16px 16px 4px;
}

.site-companion--rtl .site-companion-bubble-tail {
  right: auto;
  left: 18px;
}

.site-companion > * {
  pointer-events: auto;
}

.site-companion-bubble {
  position: relative;
  max-width: min(240px, calc(100vw - 100px));
  padding: 10px 14px;
  background: #fff;
  border-radius: 16px 16px 4px 16px;
  box-shadow: 0 8px 32px rgb(15 23 42 / 0.12), 0 0 0 1px rgb(15 23 42 / 0.06);
  cursor: pointer;
  animation: companion-float 3s ease-in-out infinite;
}

.site-companion-bubble p {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #334155;
}

.site-companion-bubble-tail {
  position: absolute;
  right: 18px;
  bottom: -6px;
  width: 12px;
  height: 12px;
  background: #fff;
  transform: rotate(45deg);
  box-shadow: 2px 2px 4px rgb(15 23 42 / 0.06);
}

.site-companion-mascot {
  position: relative;
  width: 72px;
  height: 72px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  animation: companion-bob 2.4s ease-in-out infinite;
  filter: drop-shadow(0 8px 20px rgb(99 102 241 / 0.35));
}

.site-companion--nudge .site-companion-mascot {
  animation: companion-wiggle 0.55s ease-in-out 2;
}

.site-companion-glow {
  position: absolute;
  inset: -8px;
  border-radius: 9999px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 35%, #a78bfa) 0%, transparent 70%);
  animation: companion-glow 2.8s ease-in-out infinite;
  z-index: -1;
}

.site-companion-cat {
  width: 100%;
  height: 100%;
  display: block;
}

.site-companion-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 10px;
  height: 10px;
  background: #22c55e;
  border: 2px solid #fff;
  border-radius: 9999px;
  animation: companion-pulse 1.5s ease infinite;
}

.site-companion-panel {
  width: min(300px, calc(100vw - 24px));
  max-height: min(70vh, 520px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 16px 48px rgb(15 23 42 / 0.18);
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.site-companion-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.site-companion-tabs button {
  flex: 1;
  padding: 8px 6px;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
}

.site-companion-tabs button.active {
  color: #0f172a;
  box-shadow: inset 0 -2px 0 var(--accent, #1e3a5f);
  background: #fff;
}

.site-companion-chat {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.site-companion-chat-log {
  flex: 1;
  overflow-y: auto;
  padding: 10px 12px;
  max-height: 220px;
}

.site-companion-chat-hint {
  margin: 0 0 8px;
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.45;
}

.site-companion-chat-row {
  margin-bottom: 8px;
}

.site-companion-chat-row p {
  margin: 0;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 0.875rem;
  line-height: 1.45;
  white-space: pre-wrap;
}

.site-companion-chat-row.is-user p {
  background: #e0e7ff;
  color: #1e1b4b;
  margin-left: 12px;
}

.site-companion-chat-row.is-bot p {
  background: #f1f5f9;
  color: #334155;
  margin-right: 8px;
}

.site-companion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 10px 6px;
}

.site-companion-chip {
  padding: 4px 8px;
  font-size: 0.65rem;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.site-companion-chip:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.site-companion-ask-form {
  display: flex;
  gap: 6px;
  padding: 8px 10px 10px;
  border-top: 1px solid #e2e8f0;
}

.site-companion-ask-form input {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.875rem;
}

.site-companion-ask-form button {
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: var(--accent, #1e3a5f);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.site-companion-ask-form button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.site-companion-disclaimer {
  margin: 0;
  padding: 0 10px 8px;
  font-size: 0.6rem;
  color: #94a3b8;
  line-height: 1.35;
}

.site-companion-panel-head {
  position: relative;
  padding: 14px 36px 10px 14px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--accent, #1e3a5f) 85%, #0f172a), var(--accent, #1e3a5f));
  color: #fff;
}

.site-companion-panel-head strong {
  display: block;
  font-size: 0.9rem;
}

.site-companion-panel-sub {
  font-size: 0.7rem;
  opacity: 0.8;
}

.site-companion-close {
  position: absolute;
  top: 8px;
  right: 10px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgb(255 255 255 / 0.15);
  color: #fff;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  line-height: 1;
}

.site-companion-panel-tip {
  margin: 0;
  padding: 10px 14px;
  font-size: 0.75rem;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.site-companion-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
}

.site-companion-action {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  text-decoration: none;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: transform 0.15s, box-shadow 0.15s;
}

.site-companion-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgb(15 23 42 / 0.08);
}

.site-companion-action em {
  display: block;
  font-style: normal;
  font-weight: 600;
  font-size: 0.82rem;
  color: #0f172a;
}

.site-companion-action small {
  display: block;
  font-size: 0.68rem;
  color: #64748b;
  word-break: break-all;
}

.site-companion-action--wa {
  background: #ecfdf5;
  border-color: #a7f3d0;
}

.site-companion-action--wechat {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.site-companion-action--ghost {
  background: #fff;
}

.site-companion-action-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.companion-bubble-enter-active,
.companion-bubble-leave-active,
.companion-panel-enter-active,
.companion-panel-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.companion-bubble-enter-from,
.companion-bubble-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
}

.companion-panel-enter-from,
.companion-panel-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}

@keyframes companion-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes companion-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

@keyframes companion-glow {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.08); }
}

@keyframes companion-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.85; }
}

@keyframes companion-wiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-8deg); }
  75% { transform: rotate(8deg); }
}

@media (max-width: 640px) {
  .site-companion {
    bottom: calc(max(12px, env(safe-area-inset-bottom)) + var(--tenant-mobile-bar-height, 4.35rem));
  }
  .site-companion-mascot {
    width: 56px;
    height: 56px;
  }
  .site-companion-bubble {
    max-width: min(220px, calc(100vw - 88px));
  }
  .site-companion-panel {
    width: min(320px, calc(100vw - 20px));
    max-height: min(65vh, 480px);
  }
}
</style>
