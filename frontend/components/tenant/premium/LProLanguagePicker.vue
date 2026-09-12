<template>
  <div class="lpro-lang" ref="rootRef" :class="{ 'lpro-lang--open': open }">
    <button
      type="button"
      class="lpro-lang-trigger"
      :aria-expanded="open"
      aria-haspopup="dialog"
      :aria-label="tSite('lang_picker_label')"
      @click="toggleOpen"
    >
      <span class="lpro-lang-trigger-text">{{ currentLanguageName }}</span>
      <span class="lpro-lang-chevron" aria-hidden="true">▾</span>
    </button>

    <div v-if="open" class="lpro-lang-panel" role="dialog" :aria-label="tSite('lang_picker_label')">
      <p class="lpro-lang-panel-title">{{ tSite('lang_picker_label') }}</p>
      <ul class="lpro-lang-tier1" role="listbox">
        <li v-for="opt in tier1Languages" :key="opt.code">
          <button
            type="button"
            class="lpro-lang-tier1-btn"
            role="option"
            :aria-selected="opt.code === currentLanguage"
            :class="{ 'is-active': opt.code === currentLanguage }"
            @click="pickTier1(opt.code)"
          >
            {{ opt.name }}
            <CheckIcon v-if="opt.code === currentLanguage" />
          </button>
        </li>
      </ul>
      <div class="lpro-lang-tier2-block">
        <p class="lpro-lang-tier2-heading">{{ tSite('lang_more') }}</p>
        <p class="lpro-lang-disclaimer">{{ tSite('lang_tier2_disclaimer') }}</p>
        <div class="lpro-lang-tier2-grid">
          <a
            v-for="opt in tier2Languages"
            :key="opt.code"
            class="lpro-lang-tier2-link"
            :href="googleTranslatePageUrl(opt.code)"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ opt.name }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, ref } from 'vue';
import {
  googleTranslatePageUrl,
  TIER1_LANGUAGES,
  TIER2_LANGUAGES,
  writeStoredTenantLanguage,
} from '../../../composables/useTenantLanguagePicker';

const CheckIcon = () =>
  h(
    'svg',
    {
      width: 14,
      height: 14,
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': 2.5,
      'aria-hidden': 'true',
    },
    [h('path', { d: 'M5 13l4 4L19 7' })],
  );

const props = defineProps<{
  domain: string;
  currentLanguage: string;
  tSite: (key: string, vars?: Record<string, string>) => string;
  onLanguageChange: (code: string) => void | Promise<void>;
  tier1Options?: Array<{ code: string; name: string }>;
}>();

const open = ref(false);
const rootRef = ref<HTMLElement | null>(null);

const tier1Languages = computed(() => {
  const fromApi = props.tier1Options?.filter((o) => o?.code && o?.name);
  if (fromApi?.length) return fromApi;
  return TIER1_LANGUAGES;
});
const tier2Languages = TIER2_LANGUAGES;

const currentLanguageName = computed(() => {
  const hit = tier1Languages.value.find((l) => l.code === props.currentLanguage);
  return hit?.name ?? props.currentLanguage;
});

function toggleOpen() {
  open.value = !open.value;
}

function closePanel() {
  open.value = false;
}

async function pickTier1(code: string) {
  if (code === props.currentLanguage) {
    closePanel();
    return;
  }
  writeStoredTenantLanguage(props.domain, code);
  closePanel();
  void props.onLanguageChange(code);
}

function onDocumentPointerDown(event: MouseEvent) {
  const root = rootRef.value;
  if (!root || !open.value) return;
  if (!root.contains(event.target as Node)) {
    closePanel();
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onDocumentPointerDown);
});

onUnmounted(() => {
  document.removeEventListener('mousedown', onDocumentPointerDown);
});
</script>

<style scoped>
.lpro-lang {
  position: relative;
}

.lpro-lang-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border: 1px solid var(--lpro-border, #e2e8f0);
  background: #fff;
  border-radius: 8px;
  padding: 0.4rem 0.65rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--lpro-text, #1a2332);
  cursor: pointer;
  line-height: 1.2;
  max-width: 11rem;
}

.lpro-lang-trigger:hover {
  border-color: #cbd5e1;
}

.lpro-lang--open .lpro-lang-trigger {
  border-color: var(--lpro-primary, #0f2942);
  box-shadow: 0 0 0 2px rgb(15 41 66 / 0.08);
}

.lpro-lang-trigger-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lpro-lang-chevron {
  font-size: 0.7rem;
  opacity: 0.65;
  transition: transform 0.15s ease;
}

.lpro-lang--open .lpro-lang-chevron {
  transform: rotate(180deg);
}

.lpro-lang-panel {
  position: absolute;
  top: calc(100% + 0.4rem);
  right: 0;
  z-index: 60;
  width: min(300px, 92vw);
  background: #fff;
  border: 1px solid var(--lpro-border, #e2e8f0);
  border-radius: 10px;
  padding: 0.65rem 0.75rem 0.75rem;
  box-shadow: 0 12px 32px rgba(15, 41, 66, 0.14);
}

.lpro-lang-panel-title {
  margin: 0 0 0.4rem;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--lpro-muted, #5c6b7f);
}

.lpro-lang-tier1 {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.15rem;
}

.lpro-lang-tier1-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border: none;
  background: transparent;
  border-radius: 6px;
  padding: 0.45rem 0.5rem;
  font-size: 0.875rem;
  color: var(--lpro-text, #1a2332);
  cursor: pointer;
  text-align: left;
}

.lpro-lang-tier1-btn:hover {
  background: #f1f5f9;
}

.lpro-lang-tier1-btn.is-active {
  background: #f1f5f9;
  font-weight: 600;
  color: var(--lpro-primary, #0f2942);
}

.lpro-lang-tier2-block {
  margin-top: 0.55rem;
  padding-top: 0.55rem;
  border-top: 1px solid var(--lpro-border, #e2e8f0);
}

.lpro-lang-tier2-heading {
  margin: 0 0 0.35rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--lpro-text, #1a2332);
}

.lpro-lang-disclaimer {
  font-size: 0.6875rem;
  color: var(--lpro-muted, #5c6b7f);
  margin: 0 0 0.45rem;
  line-height: 1.45;
}

.lpro-lang-tier2-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.25rem 0.5rem;
}

.lpro-lang-tier2-link {
  font-size: 0.8125rem;
  color: var(--lpro-primary, #0f2942);
  text-decoration: none;
  padding: 0.2rem 0;
}

.lpro-lang-tier2-link:hover {
  text-decoration: underline;
}
</style>
