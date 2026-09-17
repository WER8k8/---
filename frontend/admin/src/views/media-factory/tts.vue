/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="TTS 配音工作室" subtitle="文本转语音与多音色合成" surface="elevated">
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="配音工作台">
        <a-form layout="vertical">
          <a-form-item label="输入文本">
            <a-textarea v-model:value="text" :rows="6" placeholder="请输入需要配音的文本内容..." />
          </a-form-item>
          <a-form-item label="音色选择">
            <a-radio-group v-model:value="voice" button-style="solid">
              <a-radio-button value="male">男声 · 沉稳</a-radio-button>
              <a-radio-button value="female">女声 · 柔和</a-radio-button>
              <a-radio-button value="loli">萝莉 · 可爱</a-radio-button>
              <a-radio-button value="uncle">大叔 · 厚重</a-radio-button>
            </a-radio-group>
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="语速调节">
                <a-slider v-model:value="speed" :min="0.5" :max="2" :step="0.1" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="音量">
                <a-slider v-model:value="volume" :min="0" :max="100" />
              </a-form-item>
            </a-col>
          </a-row>
          <div class="text-xs text-gray-400 mb-4">语速: {{ speed }}x | 音量: {{ volume }}% | 音色: {{ voiceLabel }}</div>
          <a-button type="primary" @click="synthesize" :loading="loading">合成配音</a-button>
        </a-form>
      </a-card>
      <a-card title="合成历史">
        <a-table :columns="hcol" :data-source="history" size="small" row-key="id">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'voiceTag'">
              <a-tag :color="voiceColor(record.voice)">{{ record.voice }}</a-tag>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button size="small" type="link" @click="play(record)">播放</a-button>
                <a-button size="small" type="link" @click="downloadAudio(record)">下载</a-button>
                <a-button size="small" type="link" danger @click="deleteRecord(record.id)">删除</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';

const text = ref('')
const voice = ref('female')
const speed = ref(1)
const volume = ref(80)
const loading = ref(false)

const voiceLabel = computed(() => {
  const m: Record<string, string> = { male: '男声·沉稳', female: '女声·柔和', loli: '萝莉·可爱', uncle: '大叔·厚重' }
  return m[voice.value] || voice.value
})
const voiceColor = (v: string) => v === '男声' ? '#4a9b8c' : v === '女声' ? '#ec4899' : v === '萝莉' ? '#f59e0b' : '#8b5cf6'

const hcol = [
  { title: '文本摘要', dataIndex: 'text', ellipsis: true },
  { title: '音色', key: 'voiceTag', width: 100 },
  { title: '时长', dataIndex: 'len', width: 80 },
  { title: '语速', dataIndex: 'speed', width: 70 },
  { title: '时间', dataIndex: 'time', width: 150 },
  { title: '操作', key: 'action', width: 180 },
]

import { getAuthToken } from '@/utils/api'

const history = ref<any[]>([])

async function fetchHistory() {
  try {
    const res = await fetch('/api/v1/media-factory/tts', { headers: { Authorization: `Bearer ${getAuthToken()}` } })
    const body = await res.json()
    const data = body.data || body
    if (data.list || Array.isArray(data)) history.value = data.list || data
  } catch { /* API not available, show empty state */ }
}

onMounted(() => { fetchHistory() })

async function synthesize() {
  if (!text.value.trim()) { message.warning('请输入文本内容'); return }
  loading.value = true
  try {
    const res = await fetch('/api/v1/media-factory/tts/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ text: text.value, voice: voice.value, speed: speed.value, volume: volume.value }),
    })
    if (!res.ok) throw new Error('Synthesize failed')
    const body = await res.json()
    const data = body.data || body
    if (data.id) {
      history.value.unshift(data)
    }
    const modeHint = data.mode === 'mock' ? '（开发 stub，无真实音频）' : ''
    message.success(`配音合成完成 · ${voiceLabel.value} · ${speed.value}x${modeHint}`)
  } catch {
    message.error('配音合成失败，请稍后重试')
  }
  loading.value = false
}

function play(r: any) {
  const url = r.audio_url || r.url
  if (url) {
    new Audio(url).play().then(() => message.success('正在播放')).catch(() => message.error('播放失败'))
  } else {
    message.warning('暂无音频文件，请重新合成')
  }
}
function downloadAudio(r: any) {
  const url = r.audio_url || r.url
  if (url) {
    const a = document.createElement('a')
    a.href = url
    a.download = `tts-${r.id || Date.now()}.mp3`
    a.click()
    message.success('已开始下载')
  } else {
    message.warning('暂无音频文件')
  }
}
function deleteRecord(id: number) { history.value = history.value.filter(h => h.id !== id); message.success('已删除') }
</script>
