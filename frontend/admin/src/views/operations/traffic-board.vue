/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <TrafficBoardPanel
      :api-path="apiPath"
      :title="title"
      :subtitle="subtitle"
    />
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { YdPage } from '@/components/youding'
import TrafficBoardPanel from '@/components/traffic/TrafficBoardPanel.vue'
import { apiGet } from '@/utils/api'

const auth = useAuthStore()

const apiPath = computed(() => '/analytics/operations/traffic-board')

const title = computed(() => {
  const r = auth.currentRole
  if (r === 'tenant_admin') return '流量看板'
  if (r === 'super_admin' || r === 'admin') return '运营流量看板'
  if (r === 'l2' || r === 'l3' || r === 'agent') return '辖区流量看板'
  return '流量看板'
})

const subtitle = computed(
  () =>
    '每日访客 · 点击排行 · 哪条内容带来询盘与电话（按当前账号权限自动汇总）',
)

onMounted(async () => {
  try {
    await apiGet('/analytics/operations/traffic-board')
  } catch {
    /* 空状态 */
  }
})
</script>
