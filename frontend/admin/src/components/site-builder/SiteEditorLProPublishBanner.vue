/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-alert
    v-if="visible"
    class="site-editor-publish-gate mb-4"
    :type="gate.publish_ready ? 'success' : 'warning'"
    show-icon
  >
    <template #message>
      <span class="site-editor-publish-gate__title">{{ summary.title }}</span>
      <a-tag v-if="!gate.publish_ready" color="orange" class="ml-2">P0 {{ gate.p0 }}</a-tag>
      <a-tag v-else color="green" class="ml-2">可发布</a-tag>
    </template>
    <template #description>
      <p class="site-editor-publish-gate__desc">{{ summary.detail }}</p>
      <ul v-if="p0Issues.length" class="site-editor-publish-gate__list">
        <li v-for="(item, i) in p0Issues" :key="`${item.check}-${i}`">{{ item.detail }}</li>
      </ul>
      <p v-if="!isLProTemplate" class="site-editor-publish-gate__hint">
        请在上方选择「L-Pro 外贸专业站」模板，或使用一键生成（默认 L-Pro）。
      </p>
    </template>
  </a-alert>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  evaluateLProPublishGate,
  publishGateSummary,
  type LProPublishGate,
} from '@/utils/l-pro-publish-gate';

const props = defineProps<{
  siteContent: Record<string, unknown> | null;
  templateId: string;
  visible?: boolean;
}>();

const gate = computed<LProPublishGate>(() => {
  const base = props.siteContent ? { ...props.siteContent } : {};
  base.templateId = props.templateId;
  if (props.templateId === 'premium-b2b-v1') {
    base.templateTier = 'L-Pro';
  }
  const visual = (base.visualEditor as Record<string, unknown>) || {};
  base.visualEditor = { ...visual, templateId: props.templateId };
  return evaluateLProPublishGate(base);
});

const summary = computed(() => publishGateSummary(gate.value));
const p0Issues = computed(() => gate.value.issues.filter((i) => i.severity === 'P0'));
const isLProTemplate = computed(() => props.templateId === 'premium-b2b-v1');
const visible = computed(() => props.visible !== false);
</script>

<style scoped>
.site-editor-publish-gate__title {
  font-weight: 600;
}

.site-editor-publish-gate__desc {
  margin: 0.25rem 0 0;
}

.site-editor-publish-gate__list {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  color: rgba(0, 0, 0, 0.65);
}

.site-editor-publish-gate__hint {
  margin: 0.5rem 0 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.55);
}
</style>
