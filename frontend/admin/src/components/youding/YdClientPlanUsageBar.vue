/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-client-plan-bar" :class="{ 'yd-client-plan-bar--warn': showUpgrade }">
    <div class="yd-client-plan-bar__left">
      <a-tag :color="planTagColor(snapshot.planName)">{{ snapshot.planName }}</a-tag>
      <span v-if="snapshot.planExpiry" class="yd-client-plan-bar__expiry">{{ snapshot.planExpiry }}</span>
      <span v-if="snapshot.pendingInquiries > 0" class="yd-client-plan-bar__pill yd-client-plan-bar__pill--urgent">
        待回询盘 {{ snapshot.pendingInquiries }}
      </span>
      <span v-if="snapshot.publishInProgress > 0" class="yd-client-plan-bar__pill">
        发布中 {{ snapshot.publishInProgress }}
      </span>
    </div>
    <div class="yd-client-plan-bar__meters">
      <YdUsageMeter
        class="yd-client-plan-bar__meter"
        label="AI 算力点数（本月）"
        :used="snapshot.aiUsed"
        :max="Math.max(snapshot.aiMax, 1)"
        :hint="usageHint"
      />
    </div>

    <div class="yd-client-plan-bar__actions">
      <a-button v-if="showUpgrade" type="primary" size="small" @click="goBilling">升级套餐</a-button>
      <a-button v-else type="link" size="small" @click="goBilling">套餐与用量</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import YdUsageMeter from './YdUsageMeter.vue';
import { useClientPlanSnapshot } from '@/composables/useClientPlanSnapshot';

const router = useRouter();
const { snapshot, showUpgrade, planTagColor, refresh } = useClientPlanSnapshot();

const usageHint = computed(() => {
  if (showUpgrade.value) return '额度即将用尽，升级后可继续发品与 AI 辅助';
  return '';
});

function goBilling() {
  router.push('/client/billing');
}

onMounted(() => refresh());
</script>

<style scoped lang="scss">
.yd-client-plan-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  padding: 8px 20px;
  background: #f8fafc;
  border-bottom: 1px solid var(--uj-border);
  &--warn {
    background: #fffbeb;
    border-bottom-color: #fde68a;
  }
  &__left {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }
  &__expiry {
    font-size: 12px;
    color: var(--uj-text-muted);
  }
  &__pill {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    background: #e2e8f0;
    color: #475569;
    &--urgent {
      background: #fee2e2;
      color: #b91c1c;
    }
  }
  &__meters {
    flex: 1;
    min-width: 160px;
    max-width: 280px;
  }
  &__meter :deep(.yd-usage-meter__track) {
    height: 5px;
  }
  &__actions {
    margin-left: auto;
  }
}
@media (max-width: 768px) {
  .yd-client-plan-bar {
    padding: 8px 16px;
  }
  .yd-client-plan-bar__meters {
    width: 100%;
    max-width: none;
  }
  .yd-client-plan-bar__actions {
    width: 100%;
    margin-left: 0;
  }
}
</style>
