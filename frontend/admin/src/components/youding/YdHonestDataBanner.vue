<template>
  <a-alert
    v-if="visible"
    class="yd-honest-banner"
    :type="alertType"
    show-icon
    :banner="banner"
    :closable="closable"
    @close="dismissed = true"
  >
    <template #message>
      <span class="yd-honest-banner__title">{{ title }}</span>
    </template>
    <template #description>
      <p class="yd-honest-banner__desc">{{ description }}</p>
      <a-button
        v-if="actionLabel && actionRoute"
        type="link"
        size="small"
        class="yd-honest-banner__action"
        @click="onAction"
      >
        {{ actionLabel }}
      </a-button>
    </template>
  </a-alert>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';

export type HonestLevel = 'mock' | 'dev-stub' | 'needs-config' | 'partial' | 'real';

const props = withDefaults(
  defineProps<{
    level: HonestLevel;
    title?: string;
    description?: string;
    actionLabel?: string;
    actionRoute?: string;
    banner?: boolean;
    closable?: boolean;
  }>(),
  {
    banner: true,
    closable: false,
  },
);

const router = useRouter();
const dismissed = ref(false);

const preset = computed(() => {
  switch (props.level) {
    case 'mock':
      return {
        type: 'warning' as const,
        title: props.title || '当前为演示数据，不能当排名业绩',
        description:
          props.description
          || '接口失败或未配置时页面可能显示示例数字。请以百度站长、真实询盘电话为准。',
      };
    case 'dev-stub':
      return {
        type: 'info' as const,
        title: props.title || '本地开发环境：未真实探测百度',
        description:
          props.description
          || '收录/排名在 dev 环境会跳过或降级。上生产环境并配置 Token 后再信这些数字。',
      };
    case 'needs-config':
      return {
        type: 'warning' as const,
        title: props.title || '尚未配置，数字不可信',
        description:
          props.description || '请先完成下方配置（如百度 site_token、AI Key），再查看监测结果。',
      };
    case 'partial':
      return {
        type: 'warning' as const,
        title: props.title || '部分为间接测量，仅供参考',
        description:
          props.description
          || '结果来自简化爬虫或模型探测，不等于真实搜索榜位。请结合站长后台与询盘验证。',
      };
    default:
      return {
        type: 'success' as const,
        title: props.title || '数据来自真实检测',
        description:
          props.description || '仍建议用独立域收录与询盘电话交叉验证推广效果。',
      };
  }
});

const alertType = computed(() => preset.value.type);
const title = computed(() => preset.value.title);
const description = computed(() => preset.value.description);

const visible = computed(() => props.level !== 'real' && !dismissed.value);

function onAction() {
  if (props.actionRoute) router.push(props.actionRoute);
}
</script>

<style scoped lang="scss">
.yd-honest-banner {
  margin-bottom: 16px;
  border-radius: 8px;
}
.yd-honest-banner__title {
  font-weight: 600;
}
.yd-honest-banner__desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}
.yd-honest-banner__action {
  padding-left: 0;
  margin-top: 4px;
  height: auto;
}
</style>
