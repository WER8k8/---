/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="运费精算" subtitle="建材物流费用智能计算" surface="elevated">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="运费计算器">
        <a-form layout="vertical">
          <a-form-item label="产品类型" required>
            <a-select v-model:value="product">
              <a-select-option value="lightweight">轻集料混凝土 (0.85 元/吨·公里)</a-select-option>
              <a-select-option value="ceramsite">陶粒混凝土 (1.10 元/吨·公里)</a-select-option>
              <a-select-option value="insulation">保温砂浆 (0.65 元/吨·公里)</a-select-option>
            </a-select>
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="货物重量(吨)">
                <a-input-number v-model:value="weight" :min="1" :max="100" class="w-full" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="运输距离(公里)">
                <a-input-number v-model:value="distance" :min="10" :max="5000" class="w-full" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="出发地">
                <a-input v-model:value="from" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="目的地">
                <a-input v-model:value="to" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-button type="primary" @click="calcFreight"><CalculatorOutlined /> 计算运费</a-button>
        </a-form>
      </a-card>
      <a-card title="费用明细" v-if="fee">
        <a-descriptions bordered size="small" :column="1">
          <a-descriptions-item label="产品类型">{{ productLabel }}</a-descriptions-item>
          <a-descriptions-item label="吨公里单价">¥{{ unitPrice.toFixed(2) }}</a-descriptions-item>
          <a-descriptions-item label="货物重量">{{ weight }} 吨</a-descriptions-item>
          <a-descriptions-item label="运输距离">{{ distance }} 公里</a-descriptions-item>
          <a-descriptions-item label="基础运费">¥{{ fee.base.toLocaleString() }}</a-descriptions-item>
          <a-descriptions-item label="燃油附加费 (12%)">¥{{ fee.fuel.toLocaleString() }}</a-descriptions-item>
          <a-descriptions-item label="保险费 (3%)">¥{{ fee.insurance.toLocaleString() }}</a-descriptions-item>
          <a-descriptions-item label="装卸费">¥{{ fee.loading }}</a-descriptions-item>
          <a-descriptions-item label="总费用">
            <span class="text-xl font-bold text-blue-600">¥{{ fee.total.toLocaleString() }}</span>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, Form, FormItem, InputNumber, Input, Row, Col, Select, SelectOption, Button, Descriptions, DescriptionsItem, message } from 'ant-design-vue'
import { CalculatorOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const product = ref('lightweight')
const weight = ref(20)
const distance = ref(450)
const from = ref('上海')
const to = ref('杭州')
const fee = ref<any>(null)

const priceMap: Record<string, number> = { lightweight: 0.85, ceramsite: 1.10, insulation: 0.65 }
const labelMap: Record<string, string> = { lightweight: '轻集料混凝土', ceramsite: '陶粒混凝土', insulation: '保温砂浆' }

const unitPrice = computed(() => priceMap[product.value])
const productLabel = computed(() => labelMap[product.value])

async function calcFreight() {
  try {
    const res = await fetch('/api/v1/logistics/freight-calc', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
      body: JSON.stringify({ product: product.value, weight: weight.value, distance: distance.value, from: from.value, to: to.value }),
    })
    const body = await res.json()
    const data = body.data || body
    if (data.total || data.base) {
      fee.value = data
      return
    }
  } catch { /* fallback */ }
  // fallback: local calculation
  const base = weight.value * distance.value * unitPrice.value
  fee.value = {
    base: Math.round(base),
    fuel: Math.round(base * 0.12),
    insurance: Math.round(base * 0.03),
    loading: 350,
    total: Math.round(base * 1.15 + 350),
  }
}
</script>
