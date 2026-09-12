<template>
  <div class="tenants-layout">
    <a-tabs v-if="isTabManagedRoute" :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="租户管理" />
      <a-tab-pane key="plans" tab="套餐配置" />
      <a-tab-pane key="billing" tab="计费结算" />
      <a-tab-pane key="white-label" tab="白标品牌" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab, isTabManagedRoute } = useModuleTabSync('/tenants', [
  'dashboard',
  'plans',
  'billing',
  'white-label',
])
</script>

<style scoped>
.tenants-layout {
  padding: 0 4px;
}
</style>
