<template>
  <span class="yd-check-mark" :class="`yd-check-mark--${kind}`" aria-hidden="true">
    <CheckCircleOutlined v-if="kind === 'pass'" />
    <CloseCircleOutlined v-else-if="kind === 'fail'" />
    <WarningOutlined v-else-if="kind === 'warn'" />
    <ClockCircleOutlined v-else />
  </span>
</template>

<script setup lang="ts">
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue';

withDefaults(
  defineProps<{
    kind?: 'pass' | 'fail' | 'warn' | 'pending';
  }>(),
  { kind: 'pass' },
);
</script>

<style scoped>
.yd-check-mark {
  display: inline-flex;
  font-size: 1rem;
  line-height: 1;
}
.yd-check-mark--pass {
  color: #16a34a;
}
.yd-check-mark--fail {
  color: #dc2626;
}
.yd-check-mark--warn {
  color: #d97706;
}
.yd-check-mark--pending {
  color: #94a3b8;
}
</style>
