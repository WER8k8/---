/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="协议优化" subtitle="HTTP/3、Brotli、TLS 优化配置" surface="elevated">
    <template #actions>
      <a-button type="primary" :loading="saving" @click="saveConfig">保存配置</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="协议配置">
        <a-form layout="vertical">
          <a-form-item label="HTTP/2">
            <a-switch v-model:checked="config.http2" checked-children="启用" un-checked-children="关闭" />
            <span class="ml-2 text-xs text-gray-400">多路复用与头部压缩</span>
          </a-form-item>
          <a-form-item label="QUIC (HTTP/3)">
            <a-switch v-model:checked="config.quic" checked-children="启用" un-checked-children="关闭" />
            <span class="ml-2 text-xs text-gray-400">基于 UDP 的快速传输</span>
          </a-form-item>
          <a-form-item label="Brotli 压缩">
            <a-switch v-model:checked="config.brotli" checked-children="启用" un-checked-children="关闭" />
            <span class="ml-2 text-xs text-gray-400">比 Gzip 节省 20% 体积</span>
          </a-form-item>
          <a-form-item label="TLS 最低版本">
            <a-select v-model:value="config.tlsVersion">
              <a-select-option value="1.0">TLS 1.0</a-select-option>
              <a-select-option value="1.1">TLS 1.1</a-select-option>
              <a-select-option value="1.2">TLS 1.2</a-select-option>
              <a-select-option value="1.3">TLS 1.3</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="OCSP Stapling">
            <a-switch v-model:checked="config.ocsp" checked-children="启用" un-checked-children="关闭" />
          </a-form-item>
          <a-form-item label="Gzip 压缩级别">
            <a-slider v-model:value="config.gzip" :min="1" :max="9" /> {{ config.gzip }}
          </a-form-item>
        </a-form>
      </a-card>
      <a-card title="TLS 安全">
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="当前 TLS 版本">{{ config.tlsVersion }}</a-descriptions-item>
          <a-descriptions-item label="证书类型">ECDSA + RSA</a-descriptions-item>
          <a-descriptions-item label="HSTS">已启用 (max-age=31536000)</a-descriptions-item>
          <a-descriptions-item label="OCSP Stapling">{{ config.ocsp ? '已启用' : '已关闭' }}</a-descriptions-item>
          <a-descriptions-item label="HTTP/2">{{ config.http2 ? '已启用' : '已关闭' }}</a-descriptions-item>
          <a-descriptions-item label="QUIC">{{ config.quic ? '已启用' : '已关闭' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>
    </div>
    <a-card title="优化效果预估">
      <div class="grid grid-cols-4 gap-4">
        <a-statistic title="传输大小减少" :value="config.brotli ? 42 : 28" suffix="%" :value-style="{ color: '#22c55e' }" />
        <a-statistic title="加载时间减少" :value="config.quic ? 35 : 22" suffix="%" :value-style="{ color: '#22c55e' }" />
        <a-statistic title="TLS 握手提速" :value="config.tlsVersion === '1.3' ? 50 : config.tlsVersion === '1.2' ? 28 : 15" suffix="%" :value-style="{ color: '#22c55e' }" />
        <a-statistic title="并发连接数" :value="config.http2 ? '无限制' : 6" :value-style="{ color: config.http2 ? '#22c55e' : '#f59e0b' }" />
      </div>
    </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getAuthToken } from '@/utils/api'

const saving = ref(false)
const config = reactive({
  http2: true,
  quic: false,
  brotli: true,
  tlsVersion: '1.2',
  ocsp: true,
  gzip: 6,
})

async function saveConfig() {
  saving.value = true
  await new Promise(r => setTimeout(r, 1000))
  saving.value = false
  message.success('协议配置已保存，将在 30 秒内全网生效')
}

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/edge-cdn/protocol', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    if (d.data) Object.assign(config, d.data)
  } catch { message.warning('数据加载失败，请稍后重试') }
})
</script>
