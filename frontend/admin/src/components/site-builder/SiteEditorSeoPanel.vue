<template>
  <aside class="site-editor-seo-panel uj-glass-panel">
    <header class="site-editor-seo-panel__head">
      <h3>SEO 与全球搜索</h3>
      <p>
        英文 → Google/Bing；中文 → 百度；俄语 → Yandex。保存后按语言输出 meta，URL 带
        <code>?language=</code>
      </p>
      <p v-if="webmasterHint" class="site-editor-seo-panel__hint">
        推荐提交：
        <a :href="webmasterHint.url" target="_blank" rel="noopener noreferrer">{{ webmasterHint.label }}</a>
        · 示例页
        <span class="site-editor-seo-panel__sample">{{ sampleIndexedUrl }}</span>
      </p>
    </header>
    <YdFormilyForm v-model="localSeo" :schema="siteEditorSeoSchema" />
    <div class="site-editor-seo-panel__preview">
      <div class="site-editor-seo-panel__preview-label">Google 预览（英文）</div>
      <div class="seo-serp-mock">
        <div class="seo-serp-mock__title">{{ googleSerpTitle }}</div>
        <div class="seo-serp-mock__url">{{ serpUrl }}</div>
        <div class="seo-serp-mock__desc">{{ googleSerpDesc }}</div>
      </div>
      <div class="site-editor-seo-panel__preview-label mt-3">百度预览（中文）</div>
      <div class="seo-serp-mock seo-serp-mock--baidu">
        <div class="seo-serp-mock__title">{{ baiduSerpTitle }}</div>
        <div class="seo-serp-mock__url">{{ serpUrl }}</div>
        <div class="seo-serp-mock__desc">{{ baiduSerpDesc }}</div>
      </div>
      <div class="site-editor-seo-panel__preview-label mt-3">Yandex 预览（俄语）</div>
      <div class="seo-serp-mock seo-serp-mock--yandex">
        <div class="seo-serp-mock__title">{{ yandexSerpTitle }}</div>
        <div class="seo-serp-mock__url">{{ serpUrl }}</div>
        <div class="seo-serp-mock__desc">{{ yandexSerpDesc }}</div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue';

import { YdFormilyForm } from '@/components/youding';
import { siteEditorSeoSchema } from '@/components/youding/formily/siteEditorSeoSchema';
import type { SiteSeoFields } from '@/templates/site-builder';

const WEBMASTER_HINTS: Record<
  SiteSeoFields['seoPrimaryMarket'],
  { label: string; url: string; langParam: string }
> = {
  export: {
    label: 'Google Search Console',
    url: 'https://search.google.com/search-console',
    langParam: 'en',
  },
  domestic: {
    label: '百度站长平台',
    url: 'https://ziyuan.baidu.com/',
    langParam: 'zh',
  },
  russia: {
    label: 'Yandex Webmaster',
    url: 'https://webmaster.yandex.ru/',
    langParam: 'ru',
  },
};

const props = defineProps<{
  modelValue: SiteSeoFields;
  siteUrl?: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: SiteSeoFields];
}>();

let localSeo = reactive<SiteSeoFields>({ ...props.modelValue });

watch(
  () => props.modelValue,
  (v) => {
    Object.assign(localSeo, v);
  },
  { deep: true },
);

watch(
  localSeo,
  () => {
    emit('update:modelValue', { ...localSeo });
  },
  { deep: true },
);

const serpUrl = computed(() => props.siteUrl || 'www.your-domain.com');
const webmasterHint = computed(() => WEBMASTER_HINTS[localSeo.seoPrimaryMarket]);
const sampleIndexedUrl = computed(() => {
  const base = serpUrl.value.replace(/^https?:\/\//, '');
  const lang = webmasterHint.value?.langParam || 'en';
  return `${base}?language=${lang}`;
});

const googleSerpTitle = computed(() => localSeo.pageTitle || 'Your Company · Export Manufacturer');
const googleSerpDesc = computed(() =>
  (localSeo.seoDescription || 'Professional manufacturer, OEM/ODM, inquiry welcome.').slice(0, 160),
);
const baiduSerpTitle = computed(() => localSeo.domesticPageTitle || localSeo.pageTitle || '公司名称 · 建材制造商');
const baiduSerpDesc = computed(() =>
  (localSeo.domesticSeoDescription || localSeo.seoDescription || '专业建材制造商，支持 OEM/ODM，欢迎询盘。').slice(
    0,
    160,
  ),
);
const yandexSerpTitle = computed(
  () => localSeo.russianPageTitle || 'Производитель теплоизоляции · поставщик',
);
const yandexSerpDesc = computed(() =>
  (
    localSeo.russianSeoDescription ||
    localSeo.seoDescription ||
    'Производитель из Китая, OEM/ODM, экспорт.'
  ).slice(0, 160),
);
</script>

<style scoped lang="scss">
.site-editor-seo-panel {
  padding: 14px 16px;
  border-radius: 12px;
  height: fit-content;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.site-editor-seo-panel__head {
  margin-bottom: 12px;
  h3 {
    margin: 0 0 4px;
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
  }
  p {
    margin: 0;
    font-size: 12px;
    color: #64748b;
    line-height: 1.45;
  }
  code {
    font-size: 11px;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 4px;
  }
}

.site-editor-seo-panel__hint {
  margin-top: 6px;
  a {
    color: var(--uj-brand, #4a9b8c);
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
}

.site-editor-seo-panel__sample {
  color: #475569;
  font-size: 11px;
}

.site-editor-seo-panel__preview {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.site-editor-seo-panel__preview-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 6px;
}

.seo-serp-mock {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.seo-serp-mock--baidu {
  background: #fff;
}

.seo-serp-mock--yandex {
  background: #fff;
  border-color: #fcd34d;
}

.seo-serp-mock__title {
  font-size: 14px;
  color: #1a0dab;
  line-height: 1.35;
  margin-bottom: 2px;
}

.seo-serp-mock--baidu .seo-serp-mock__title {
  color: #2440b3;
}

.seo-serp-mock--yandex .seo-serp-mock__title {
  color: #0066ff;
}

.seo-serp-mock__url {
  font-size: 12px;
  color: #006621;
  margin-bottom: 4px;
}

.seo-serp-mock__desc {
  font-size: 12px;
  color: #545454;
  line-height: 1.45;
}
</style>
