import fs from 'fs'
import path from 'path'

const fixes = [
  {
    file: 'src/views/sales/index.vue',
    content: `<template>
  <div class="sales-layout">
    <a-tabs v-model:activeKey="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="销售工作台" />
      <a-tab-pane key="customer-finder" tab="客户开发" />
      <a-tab-pane key="auto-negotiator" tab="自动谈单" />
      <a-tab-pane key="email-automation" tab="开发信管理" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/sales', [
  'dashboard',
  'customer-finder',
  'auto-negotiator',
  'email-automation',
])
</script>

<style scoped>
.sales-layout {
  padding: 0 4px;
}
</style>
`,
  },
  {
    file: 'src/views/seo-matrix/index.vue',
    content: `<template>
  <div class="seo-matrix-layout">
    <a-tabs v-model:activeKey="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="数据看板" />
      <a-tab-pane key="settings" tab="系统设置" />
      <a-tab-pane key="regions" tab="地域词库" />
      <a-tab-pane key="keywords" tab="关键词管理" />
      <a-tab-pane key="content" tab="文案生成" />
      <a-tab-pane key="publish" tab="多平台分发" />
      <a-tab-pane key="inclusion" tab="收录监控" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/seo-matrix', [
  'dashboard',
  'settings',
  'regions',
  'keywords',
  'content',
  'publish',
  'inclusion',
])
</script>

<style scoped>
.seo-matrix-layout {
  padding: 0 4px;
}
</style>
`,
  },
]

for (const { file, content } of fixes) {
  const p = path.resolve(file)
  fs.writeFileSync(p, content, 'utf8')
  console.log('fixed', p)
}
