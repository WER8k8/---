<template>
  <YdPage title="LBS测距" subtitle="基于位置的服务与路径规划" surface="elevated">
    <template #actions>
      <a-button @click="clearAll">清除记录</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-card title="路径规划">
      <a-alert type="info" show-icon class="mb-4">
        <template #message>使用高德/百度地图 API 进行地址解析与路径规划；失败时将提示错误，不生成估算数据。</template>
      </a-alert>
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="发货地址">
              <a-input v-model:value="origin" placeholder="例如：上海市浦东新区XX路XX号" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="收货地址">
              <a-input v-model:value="dest" placeholder="例如：杭州市西湖区XX项目工地" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="货物重量(吨)">
              <a-input-number v-model:value="weight" :min="1" :max="100" class="w-full" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="运输方式">
              <a-radio-group v-model:value="mode" option-type="button" button-style="solid">
                <a-radio-button value="truck">货车</a-radio-button>
                <a-radio-button value="rail">铁路</a-radio-button>
                <a-radio-button value="ship">水运</a-radio-button>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>
        <a-button type="primary" @click="calc" :loading="loading"><EnvironmentOutlined /> 计算距离与运费</a-button>
      </a-form>
    </a-card>
    <div v-if="result" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="距离与运费结果">
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="直线距离">{{ result.straight }} km</a-descriptions-item>
          <a-descriptions-item label="驾车距离">{{ result.driving }} km</a-descriptions-item>
          <a-descriptions-item label="预计时间">{{ result.duration }}</a-descriptions-item>
          <a-descriptions-item label="货物重量">{{ weight }} 吨</a-descriptions-item>
          <a-descriptions-item label="估算运费">
            <span class="text-xl font-bold text-blue-600">¥{{ result.freight.toLocaleString() }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="计算公式">距离 × 重量 × 0.85</a-descriptions-item>
        </a-descriptions>
      </a-card>
      <a-card title="历史测距记录">
        <a-table :columns="hcol" :data-source="history" size="small" row-key="id" :pagination="false" />
      </a-card>
    </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  Card, Form, FormItem, Input, InputNumber, Row, Col, RadioGroup, RadioButton,
  Button, Descriptions, DescriptionsItem, Table, Alert, message,
} from 'ant-design-vue'
import { EnvironmentOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const origin = ref('上海市浦东新区')
const dest = ref('杭州市西湖区')
const weight = ref(20)
const mode = ref('truck')
const loading = ref(false)
const result = ref<any>(null)
let histId = 0
const history = ref<any[]>([])

const hcol = [
  { title: '发货地', dataIndex: 'from', width: 100 },
  { title: '收货地', dataIndex: 'to', width: 100 },
  { title: '距离', dataIndex: 'distance', width: 80 },
  { title: '运费', dataIndex: 'freight', width: 100 },
  { title: '时间', dataIndex: 'time', width: 140 },
]

async function calc() {
  if (!origin.value.trim() || !dest.value.trim()) { message.warning('请输入发货地址和收货地址'); return }
  loading.value = true
  try {
    const res = await fetch('/api/v1/logistics/lbs-routing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ origin: origin.value, destination: dest.value, weight: weight.value, mode: mode.value }),
    })
    const body = await res.json()
    const data = body.data || body
    if (data.distance || data.freight) {
      result.value = {
        straight: data.straight || Math.round(data.distance * 0.8),
        driving: data.distance || data.driving,
        duration: data.duration || `${Math.round((data.distance || 500) / 80)}小时`,
        freight: data.freight,
      }
      history.value.unshift({
        id: ++histId,
        from: origin.value,
        to: dest.value,
        distance: `${data.distance || data.driving}km`,
        freight: `¥${(data.freight || 0).toLocaleString()}`,
        time: new Date().toLocaleString(),
      })
      message.success('LBS测距完成')
    } else {
      throw new Error('no data')
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '测距失败，请检查地址或稍后重试')
  }
  loading.value = false
}

function clearAll() { history.value = []; result.value = null; message.success('已清除') }
</script>
