<template>
  <aside class="site-editor-right-panel">
    <a-segmented
      v-model:value="activeTab"
      block
      class="site-editor-right-panel__tabs"
      :options="tabOptions"
    />
    <SiteEditorSeoPanel
      v-show="activeTab === 'seo'"
      v-model="seoModel"
      :site-url="siteUrl"
    />
    <SiteEditorGapPanel
      v-show="activeTab === 'gap'"
      embedded
      :site-content="siteContent"
      @apply="emit('gap-apply', $event)"
    />
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import SiteEditorSeoPanel from './SiteEditorSeoPanel.vue';
import SiteEditorGapPanel from './SiteEditorGapPanel.vue';
import type { SiteSeoFields } from '@/templates/site-builder';

const props = defineProps<{
  siteContent: Record<string, unknown>;
  siteUrl?: string;
  initialTab?: 'seo' | 'gap';
}>();

const emit = defineEmits<{
  'gap-apply': [merged: Record<string, unknown>];
}>();

const seoModel = defineModel<SiteSeoFields>('seoModel', { required: true });

const tabOptions = [
  { label: 'SEO', value: 'seo' },
  { label: '发布补齐', value: 'gap' },
];

const activeTab = ref<'seo' | 'gap'>(props.initialTab || 'seo');

watch(
  () => props.initialTab,
  (tab) => {
    if (tab) activeTab.value = tab;
  },
);
</script>

<style scoped lang="scss">
.site-editor-right-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.site-editor-right-panel__tabs {
  margin-bottom: 2px;
}
</style>
