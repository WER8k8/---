/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="插件市场" subtitle="扩展插件管理与安装" surface="elevated">
    <template #actions>
      <a-space>
        <a-input-search v-model:value="keyword" placeholder="搜索插件..." class="w-64" />
        <a-button type="primary" @click="showForm = true">安装新插件</a-button>
      </a-space>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-card title="已安装插件">
      <a-table :columns="cols" :data-source="filteredPlugins" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'enabled'">
            <a-switch v-model:checked="record.enabled" @change="togglePlugin(record)" :loading="record._toggling" />
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.enabled ? 'success' : 'default'">{{ record.enabled ? '已启用' : '已禁用' }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="configPlugin(record)">配置</a-button>
              <a-popconfirm title="确定卸载该插件？" @confirm="uninstallPlugin(record.id)">
                <a-button size="small" type="link" danger>卸载</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    <a-modal v-model:open="showForm" title="安装新插件" @ok="installPlugin" @cancel="resetInstallForm">
      <a-form :model="installForm" layout="vertical">
        <a-form-item label="插件名称"><a-input v-model:value="installForm.name" placeholder="如: SEO分析" /></a-form-item>
        <a-form-item label="插件标识"><a-input v-model:value="installForm.key" placeholder="如: seo-analyzer" /></a-form-item>
        <a-form-item label="版本号"><a-input v-model:value="installForm.version" placeholder="如: 1.0.0" /></a-form-item>
        <a-form-item label="描述"><a-textarea v-model:value="installForm.desc" :rows="2" placeholder="插件功能描述" /></a-form-item>
      </a-form>
    </a-modal>
    <a-modal v-model:open="configOpen" :title="`配置插件：${configTarget?.name || ''}`" @ok="savePluginConfig" @cancel="configOpen = false">
      <a-form v-if="configTarget" layout="vertical">
        <a-form-item label="插件名称"><a-input v-model:value="configForm.name" /></a-form-item>
        <a-form-item label="描述"><a-textarea v-model:value="configForm.desc" :rows="2" /></a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="configForm.enabled" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { getAuthToken } from '@/utils/api';

const keyword = ref('')

const cols = [
  { title: '插件名', dataIndex: 'name' },
  { title: '版本', dataIndex: 'version', width: 70 },
  { title: '作者', dataIndex: 'author', width: 100 },
  { title: '描述', dataIndex: 'desc', ellipsis: true },
  { title: '启用', key: 'enabled', width: 80 },
  { title: '状态', key: 'status', width: 70 },
  { title: '安装时间', dataIndex: 'installed', width: 110 },
  { title: '操作', key: 'action', width: 130 },
]

const plugins = ref([
  { id: 1, name: 'SEO 分析', version: '2.1.0', author: '优丁官方', desc: '关键词分析与排名追踪', enabled: true, installed: '2026-05-10' },
  { id: 2, name: '飞书通知', version: '1.3.2', author: '第三方', desc: '飞书群消息推送与提醒', enabled: true, installed: '2026-05-08' },
  { id: 3, name: '数据导出', version: '3.0.1', author: '优丁官方', desc: 'Excel/CSV/PDF 数据导出', enabled: true, installed: '2026-04-28' },
  { id: 4, name: 'AI 翻译', version: '1.0.5', author: '第三方', desc: '多语言 AI 翻译集成', enabled: false, installed: '2026-04-20' },
  { id: 5, name: '物流追踪', version: '0.9.2', author: '第三方', desc: '快递物流实时追踪查询', enabled: true, installed: '2026-04-15' },
  { id: 6, name: '权限管理', version: '2.4.0', author: '优丁官方', desc: 'RBAC 权限控制体系', enabled: true, installed: '2026-03-30' },
])

const filteredPlugins = computed(() =>
  plugins.value.filter(p =>
    !keyword.value || p.name.includes(keyword.value) || p.desc.includes(keyword.value) || p.author.includes(keyword.value)
  )
)

const showForm = ref(false)
const configOpen = ref(false)
const configTarget = ref<any>(null)
const configForm = reactive({ name: '', desc: '', enabled: true })
const installForm = reactive({ name: '', key: '', version: '1.0.0', desc: '' })

function togglePlugin(record: any) {
  message.success(`插件 "${record.name}" 已${record.enabled ? '启用' : '禁用'}`)
}
function configPlugin(record: any) {
  configTarget.value = record
  Object.assign(configForm, { name: record.name, desc: record.desc, enabled: record.enabled })
  configOpen.value = true
}
function savePluginConfig() {
  if (!configTarget.value) return
  Object.assign(configTarget.value, { name: configForm.name, desc: configForm.desc, enabled: configForm.enabled })
  configOpen.value = false
  message.success(`插件「${configForm.name}」配置已保存`)
}
function uninstallPlugin(id: number) { plugins.value = plugins.value.filter(p => p.id !== id); message.success('插件已卸载') }
function installPlugin() {
  if (!installForm.name.trim() || !installForm.key.trim()) { message.warning('请填写完整信息'); return }
  plugins.value.push({
    id: Date.now(),
    name: installForm.name,
    version: installForm.version || '1.0.0',
    author: '手动安装',
    desc: installForm.desc || '-',
    enabled: true,
    installed: new Date().toISOString().split('T')[0],
  })
  showForm.value = false; resetInstallForm(); message.success('插件安装成功')
}
function resetInstallForm() { Object.assign(installForm, { name: '', key: '', version: '1.0.0', desc: '' }) }

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/developer/plugins', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    if (Array.isArray(d.data?.items)) plugins.value = d.data.items
  } catch { message.warning('数据加载失败，请稍后重试') }
})
</script>
