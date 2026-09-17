/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="SDK 管理" subtitle="多语言 SDK 版本管理与分发" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showForm = true">新建 SDK 版本</a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-card title="SDK 列表">
      <a-table :columns="cols" :data-source="sdks" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'lang'">
            <a-tag :color="langColor(record.lang)">{{ record.lang }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'stable' ? 'success' : 'warning'">{{ record.status === 'stable' ? '稳定版' : '测试版' }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="downloadSdk(record)">下载</a-button>
              <a-button size="small" type="link" @click="openDoc(record)">文档</a-button>
              <a-popconfirm title="确定删除？" @confirm="deleteSdk(record.id)">
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    <a-modal v-model:open="showForm" title="新建 SDK 版本" @ok="saveSdk" @cancel="resetForm">
      <a-form :model="form" layout="vertical">
        <a-form-item label="语言"><a-select v-model:value="form.lang">
          <a-select-option value="JavaScript">JavaScript</a-select-option>
          <a-select-option value="Python">Python</a-select-option>
          <a-select-option value="Go">Go</a-select-option>
          <a-select-option value="Java">Java</a-select-option>
          <a-select-option value="C#">C#</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="版本号"><a-input v-model:value="form.version" placeholder="如: 3.2.1" /></a-form-item>
        <a-form-item label="状态"><a-select v-model:value="form.status">
          <a-select-option value="stable">稳定版</a-select-option><a-select-option value="beta">测试版</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="文档链接"><a-input v-model:value="form.doc" placeholder="https://..." /></a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { getAuthToken } from '@/utils/api';

const cols = [
  { title: '语言', key: 'lang', width: 110 },
  { title: '版本', dataIndex: 'version', width: 80 },
  { title: '下载量', dataIndex: 'downloads', width: 80 },
  { title: '包大小', dataIndex: 'size', width: 70 },
  { title: '文档链接', dataIndex: 'doc', width: 160, ellipsis: true },
  { title: '状态', key: 'status', width: 70 },
  { title: '更新时间', dataIndex: 'updated', width: 110 },
  { title: '操作', key: 'action', width: 170 },
]

const sdks = ref([
  { id: 1, lang: 'JavaScript', version: '3.2.1', downloads: '12.5K', size: '245KB', doc: 'https://docs.youding.com/js', status: 'stable', updated: '2026-05-15' },
  { id: 2, lang: 'Python', version: '2.8.0', downloads: '8.2K', size: '180KB', doc: 'https://docs.youding.com/py', status: 'stable', updated: '2026-05-10' },
  { id: 3, lang: 'Go', version: '1.5.3', downloads: '3.1K', size: '320KB', doc: 'https://docs.youding.com/go', status: 'stable', updated: '2026-04-28' },
  { id: 4, lang: 'Java', version: '1.2.0-beta', downloads: '1.8K', size: '560KB', doc: 'https://docs.youding.com/java', status: 'beta', updated: '2026-05-01' },
])

const showForm = ref(false)
const form = reactive({ lang: 'JavaScript', version: '', status: 'stable', doc: '' })

function langColor(l: string) {
  const m: Record<string, string> = { JavaScript: 'orange', Python: 'blue', Go: 'cyan', Java: 'red' }
  return m[l] || 'default'
}

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/developer/sdk', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    if (d.data) sdks.value = d.data
  } catch { message.warning('数据加载失败，请稍后重试') }
})

function saveSdk() {
  if (!form.version.trim()) { message.warning('请输入版本号'); return }
  sdks.value.unshift({
    id: Date.now(),
    lang: form.lang,
    version: form.version,
    downloads: '0',
    size: '-',
    doc: form.doc || '-',
    status: form.status,
    updated: new Date().toISOString().split('T')[0],
  })
  showForm.value = false; resetForm(); message.success('SDK 版本已创建')
}
function downloadSdk(r: any) { message.success(`开始下载 ${r.lang} SDK v${r.version}`) }
function openDoc(r: any) {
  if (r.doc && r.doc.startsWith('http')) window.open(r.doc, '_blank')
  else message.warning('暂无文档链接')
}
function deleteSdk(id: number) { sdks.value = sdks.value.filter(s => s.id !== id); message.success('已删除') }
function resetForm() { Object.assign(form, { lang: 'JavaScript', version: '', status: 'stable', doc: '' }) }
</script>
