/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-empty">
    <component :is="icon" class="yd-empty__icon" />
    <h3 class="yd-empty__title">{{ displayTitle }}</h3>
    <p v-if="displayDesc" class="yd-empty__desc">{{ displayDesc }}</p>
    <a-button v-if="displayCta" type="primary" @click="$emit('action')">{{ displayCta }}</a-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { InboxOutlined, RocketOutlined, ShoppingOutlined } from '@ant-design/icons-vue';

/** UX-06 · 空状态三变体（无 emoji） */
const props = withDefaults(
  defineProps<{
    variant?: 'inquiry' | 'product' | 'onboarding';
    title?: string;
    description?: string;
    ctaLabel?: string;
  }>(),
  { variant: 'inquiry' },
);

defineEmits<{ action: [] }>();

const presets = {
  inquiry: {
    icon: InboxOutlined,
    title: '还没有询盘',
    description: '配置询盘入口后，线索会出现在这里。',
    cta: '去配置询盘',
  },
  product: {
    icon: ShoppingOutlined,
    title: '还没有产品',
    description: '添加首个产品，才能开始多平台发布。',
    cta: '添加产品',
  },
  onboarding: {
    icon: RocketOutlined,
    title: '完成开户待办',
    description: '按步骤完成绑域与发品，30 秒看懂今日任务。',
    cta: '继续开户',
  },
} as const;

const preset = computed(() => presets[props.variant]);
const icon = computed(() => preset.value.icon);
const displayTitle = computed(() => props.title ?? preset.value.title);
const displayDesc = computed(() => props.description ?? preset.value.description);
const displayCta = computed(() => props.ctaLabel ?? preset.value.cta);
</script>

<style scoped lang="scss">
.yd-empty {
  text-align: center;
  padding: 32px 16px;
  &__icon {
    font-size: 32px;
    color: var(--uj-brand);
    margin-bottom: 12px;
  }
  &__title {
    font-size: 15px;
    font-weight: 600;
    margin: 0 0 8px;
  }
  &__desc {
    font-size: 13px;
    color: var(--uj-text-muted);
    margin: 0 0 16px;
  }
}
</style>
