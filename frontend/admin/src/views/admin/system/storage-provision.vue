/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="存储开通"
    subtitle="平台一次性配置七牛（国内）/ R2（海外）；客户开户无需自注册七牛"
    surface="elevated"
  >
    <template #actions>
      <a-space>
        <a-button :loading="loading" @click="loadAll">刷新</a-button>
        <a-button type="primary" :loading="verifying" @click="verifyCurrent">验收当前配置</a-button>
      </a-space>
    </template>

    <a-alert
      v-if="status?.readiness?.production_risk"
      type="error"
      show-icon
      class="mb-4"
      message="生产环境风险：默认分区云存储未就绪，产品图将落本地磁盘"
    />

    <a-row :gutter="16" class="mb-4">
      <a-col :span="12">
        <a-card title="七牛云（国内）" size="small">
          <a-descriptions v-if="status?.qiniu" bordered size="small" :column="1">
            <a-descriptions-item label="状态">
              <a-tag :color="status.qiniu.configured ? 'green' : 'orange'">
                {{ status.qiniu.configured ? '已配置' : '未配置' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="AK">{{ status.qiniu.access_key_masked || '—' }}</a-descriptions-item>
            <a-descriptions-item label="Bucket">{{ status.qiniu.bucket || '—' }}</a-descriptions-item>
            <a-descriptions-item label="CDN 域名">{{ status.qiniu.public_base_url || '—' }}</a-descriptions-item>
          </a-descriptions>
          <p class="text-xs text-gray-500 mt-2">{{ status?.readiness?.cn_product_images === 'ready' ? '国内租户产品图已就绪' : '未配 QINIU_* 时走本地 fallback' }}</p>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="Cloudflare R2（海外）" size="small">
          <a-descriptions v-if="status?.r2" bordered size="small" :column="1">
            <a-descriptions-item label="状态">
              <a-tag :color="status.r2.configured ? 'green' : 'default'">
                {{ status.r2.configured ? '已配置' : '可选' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="Account">{{ status.r2.account_id_masked || '—' }}</a-descriptions-item>
            <a-descriptions-item label="Bucket">{{ status.r2.bucket || '—' }}</a-descriptions-item>
            <a-descriptions-item label="公开域名">{{ status.r2.public_base_url || '—' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <a-card title="运维清单" class="mb-4" size="small">
      <a-list size="small" :data-source="checklist">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <a-tag v-if="item.done" color="green">完成</a-tag>
                <a-tag v-else-if="item.automatable" color="blue">待验收</a-tag>
                <a-tag v-else color="gold">人工</a-tag>
                {{ item.title }}
              </template>
              <template #description>{{ item.detail }}</template>
            </a-list-item-meta>
            <a v-if="item.url" :href="item.url" target="_blank" rel="noopener">打开</a>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card v-if="verifyReport" title="最近探测结果" class="mb-4" size="small">
      <a-tag :color="overallColor">{{ verifyReport.overall }}</a-tag>
      <ul class="mt-2 text-sm">
        <li v-for="(r, i) in verifyReport.results" :key="i">
          [{{ r.status }}] {{ r.target }}: {{ r.message }}
          <span v-if="r.hint" class="text-gray-500"> — {{ r.hint }}</span>
        </li>
      </ul>
    </a-card>

    <a-card title="配服务器前先验密钥（不落库）" size="small" class="mb-4">
      <a-form layout="vertical">
        <a-divider orientation="left">七牛</a-divider>
        <a-row :gutter="12">
          <a-col :span="12"><a-form-item label="QINIU_ACCESS_KEY"><a-input v-model:value="trialQiniu.access_key" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="QINIU_SECRET_KEY"><a-input-password v-model:value="trialQiniu.secret_key" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="QINIU_BUCKET"><a-input v-model:value="trialQiniu.bucket" /></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="QINIU_PUBLIC_BASE_URL"><a-input v-model:value="trialQiniu.public_base_url" placeholder="https://img.example.com" /></a-form-item></a-col>
        </a-row>
        <a-button type="primary" :loading="trialLoading" @click="verifyTrial('qiniu')">试填并探测七牛</a-button>
      </a-form>
    </a-card>

    <a-card title="运维文档与 env 片段" size="small">
      <p class="text-sm text-gray-600 mb-2">
        完整步骤见仓库 <code>docs/PLATFORM-STORAGE-SETUP.md</code>；本地一键向导：
        <code>powershell -File scripts/setup-platform-storage.ps1</code>
      </p>
      <a-button :loading="snippetLoading" @click="loadSnippet">复制当前 env 片段</a-button>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost } from '@/utils/api'

const loading = ref(false)
const verifying = ref(false)
const trialLoading = ref(false)
const snippetLoading = ref(false)
const status = ref<any>(null)
const checklist = ref<any[]>([])
const verifyReport = ref<any>(null)

const trialQiniu = reactive({
  access_key: '',
  secret_key: '',
  bucket: '',
  public_base_url: '',
  upload_host: 'https://upload.qiniup.com',
})

const overallColor = computed(() => {
  const o = verifyReport.value?.overall
  if (o === 'pass') return 'green'
  if (o === 'warn') return 'orange'
  if (o === 'fail') return 'red'
  return 'default'
})

async function loadAll() {
  loading.value = true
  try {
    const [st, cl] = await Promise.all([
      apiGet('/super-admin/storage-provision/status'),
      apiGet('/super-admin/storage-provision/checklist'),
    ])
    status.value = st?.data ?? st
    checklist.value = (cl?.data ?? cl)?.items ?? []
  } catch (e: any) {
    message.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function verifyCurrent() {
  verifying.value = true
  try {
    const res = await apiPost('/super-admin/storage-provision/verify-current', {})
    verifyReport.value = res?.data ?? res
    const ok = verifyReport.value?.overall === 'pass'
    message[ok ? 'success' : 'warning'](ok ? '验收通过' : '验收未完全通过，见下方详情')
    await loadAll()
  } catch (e: any) {
    message.error(e?.message || '验收失败')
  } finally {
    verifying.value = false
  }
}

async function verifyTrial(target: 'qiniu' | 'r2') {
  trialLoading.value = true
  try {
    const body: any = { target, qiniu: trialQiniu }
    const res = await apiPost('/super-admin/storage-provision/verify', body)
    verifyReport.value = res?.data ?? res
    const r = verifyReport.value?.results?.[0]
    if (r?.status === 'pass') message.success('七牛探测通过，可写入服务器 .env')
    else message.error(r?.message || '探测失败')
  } catch (e: any) {
    message.error(e?.message || '探测失败')
  } finally {
    trialLoading.value = false
  }
}

async function loadSnippet() {
  snippetLoading.value = true
  try {
    const res = await apiGet('/super-admin/storage-provision/env-snippet')
    const snippet = (res?.data ?? res)?.snippet || ''
    await navigator.clipboard.writeText(snippet)
    message.success('已复制 env 片段（含密钥，勿外发）')
  } catch (e: any) {
    message.error(e?.message || '复制失败')
  } finally {
    snippetLoading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.mt-2 { margin-top: 8px; }
</style>
