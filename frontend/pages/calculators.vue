/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="calc-page">
    <section class="calc-hero">
      <div class="calc-hero-inner">
        <h1 class="calc-title">
          工程计算器
        </h1>
        <p class="calc-sub">
          热工、防火、数量估算工具。计算结果为估算参考值，正式设计需由专业工程师验证。
        </p>
      </div>
    </section>

    <section class="calc-body">
      <a-card
        :bordered="false"
        class="calc-card"
      >
        <a-tabs v-model:active-key="activeTab">
          <!-- 热工计算 -->
          <a-tab-pane
            key="thermal"
            tab="热工计算"
          >
            <a-form
              layout="vertical"
              @submit.prevent="runThermal"
            >
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="保温层厚度 (mm)">
                    <a-input-number
                      v-model:value="thermal.thickness_mm"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="导热系数 λ (W/m·K)">
                    <a-input-number
                      v-model:value="thermal.thermal_conductivity"
                      :min="0"
                      :step="0.001"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="面积 (m²)">
                    <a-input-number
                      v-model:value="thermal.area_m2"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="温差 ΔT (°C)">
                    <a-input-number
                      v-model:value="thermal.delta_t"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="目标 U 值 (W/m²·K)">
                    <a-input-number
                      v-model:value="thermal.target_u"
                      :min="0"
                      :step="0.01"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
              >
                计算
              </a-button>
            </a-form>
            <div
              v-if="thermalResult"
              class="calc-result"
            >
              <a-descriptions
                bordered
                size="small"
                :column="2"
              >
                <a-descriptions-item label="U 值">
                  {{ thermalResult.output.u_value }} {{ thermalResult.output.u_value_unit }}
                </a-descriptions-item>
                <a-descriptions-item label="热阻">
                  {{ thermalResult.output.thermal_resistance }} {{ thermalResult.output.thermal_resistance_unit }}
                </a-descriptions-item>
                <a-descriptions-item
                  v-if="thermalResult.output.heat_loss"
                  label="热损失"
                >
                  {{ thermalResult.output.heat_loss_label }}
                </a-descriptions-item>
                <a-descriptions-item
                  v-if="thermalResult.output.required_thickness_approx"
                  label="目标厚度"
                >
                  {{ thermalResult.output.required_thickness_note }}
                </a-descriptions-item>
              </a-descriptions>
              <div
                v-for="a in thermalResult.assumptions"
                :key="a"
                class="assumption"
              >
                • {{ a }}
              </div>
            </div>
          </a-tab-pane>

          <!-- 防火计算 -->
          <a-tab-pane
            key="fire"
            tab="防火计算"
          >
            <a-form
              layout="vertical"
              @submit.prevent="runFire"
            >
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="截面系数 Hp/A (m⁻¹)">
                    <a-input-number
                      v-model:value="fire.section_factor"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="耐火等级 (分钟)">
                    <a-select
                      v-model:value="fire.fire_rating"
                      style="width:100%"
                    >
                      <a-select-option :value="30">
                        30
                      </a-select-option><a-select-option :value="60">
                        60
                      </a-select-option><a-select-option :value="90">
                        90
                      </a-select-option><a-select-option :value="120">
                        120
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="钢构件临界温度 (°C)">
                    <a-input-number
                      v-model:value="fire.steel_temp_limit"
                      :min="300"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
              >
                计算
              </a-button>
            </a-form>
            <div
              v-if="fireResult"
              class="calc-result"
            >
              <a-alert
                type="warning"
                message="候选厚度（估算参考值）"
                :description="fireResult.output.candidate_thickness + ' — ' + fireResult.output.candidate_thickness_note"
                show-icon
              />
              <div
                v-for="a in fireResult.assumptions"
                :key="a"
                class="assumption"
              >
                • {{ a }}
              </div>
            </div>
          </a-tab-pane>

          <!-- 数量估算 -->
          <a-tab-pane
            key="quantity"
            tab="数量估算"
          >
            <a-form
              layout="vertical"
              @submit.prevent="runQuantity"
            >
              <a-row :gutter="16">
                <a-col :span="6">
                  <a-form-item label="面积 (m²)">
                    <a-input-number
                      v-model:value="quantity.area_m2"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="厚度 (mm)">
                    <a-input-number
                      v-model:value="quantity.thickness_mm"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="密度 (kg/m³)">
                    <a-input-number
                      v-model:value="quantity.density_kg_m3"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="损耗率 (%)">
                    <a-input-number
                      v-model:value="quantity.wastage_pct"
                      :min="0"
                      style="width:100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
              >
                计算
              </a-button>
            </a-form>
            <div
              v-if="quantityResult"
              class="calc-result"
            >
              <a-descriptions
                bordered
                size="small"
                :column="2"
              >
                <a-descriptions-item label="体积">
                  {{ quantityResult.output.volume }} {{ quantityResult.output.volume_unit }}
                </a-descriptions-item>
                <a-descriptions-item label="重量">
                  {{ quantityResult.output.weight_label || '—' }}
                </a-descriptions-item>
                <a-descriptions-item label="含损耗体积">
                  {{ quantityResult.output.volume_with_wastage }} {{ quantityResult.output.volume_with_wastage_unit }} (损耗 {{ quantityResult.output.wastage_applied }})
                </a-descriptions-item>
                <a-descriptions-item label="包装数">
                  {{ quantityResult.output.packages_label || '—' }}
                </a-descriptions-item>
              </a-descriptions>
              <div
                v-for="a in quantityResult.assumptions"
                :key="a"
                class="assumption"
              >
                • {{ a }}
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  Alert as AAlert, Button as AButton, Card as ACard, Col as ACol,
  Descriptions as ADescriptions, DescriptionsItem as ADescriptionsItem,
  Form as AForm, FormItem as AFormItem, InputNumber as AInputNumber,
  Row as ARow, Select as ASelect, SelectOption as ASelectOption,
  TabPane as ATabPane, Tabs as ATabs,
} from 'ant-design-vue'
import { useApi } from '~/composables/useApi'
import { useSeoMeta } from '#imports'

useSeoMeta({
  title: '工程计算器 - 热工/防火/数量估算',
  description: '优丁建材工程计算器：热工 U 值、钢构件防火厚度、材料数量估算工具。',
})

const api = useApi()
const activeTab = ref('thermal')
const loading = ref(false)

const thermal = reactive({ thickness_mm: undefined as number | undefined, thermal_conductivity: undefined as number | undefined, area_m2: undefined as number | undefined, delta_t: undefined as number | undefined, target_u: undefined as number | undefined })
const fire = reactive({ section_factor: undefined as number | undefined, fire_rating: 60 as number | undefined, steel_temp_limit: 550 })
const quantity = reactive({ area_m2: undefined as number | undefined, thickness_mm: undefined as number | undefined, density_kg_m3: undefined as number | undefined, wastage_pct: 5 })

const thermalResult = ref<any>(null)
const fireResult = ref<any>(null)
const quantityResult = ref<any>(null)

async function runThermal() {
  loading.value = true
  try { thermalResult.value = await api.post('/calculator/thermal', thermal, { skipAuth: true }) }
  catch (e: any) { thermalResult.value = { error: e.message } }
  finally { loading.value = false }
}
async function runFire() {
  loading.value = true
  try { fireResult.value = await api.post('/calculator/fire-protection', fire, { skipAuth: true }) }
  catch (e: any) { fireResult.value = { error: e.message } }
  finally { loading.value = false }
}
async function runQuantity() {
  loading.value = true
  try { quantityResult.value = await api.post('/calculator/quantity', quantity, { skipAuth: true }) }
  catch (e: any) { quantityResult.value = { error: e.message } }
  finally { loading.value = false }
}
</script>

<style scoped>
.calc-page { min-height: 100vh; background: var(--color-bg, #f5f7fa); padding-bottom: 64px; }
.calc-hero { padding: 32px 16px 8px; background: linear-gradient(135deg, #1a365d, #2563eb); }
.calc-hero-inner { max-width: 960px; margin: 0 auto; color: #fff; }
.calc-title { font-size: 28px; font-weight: 700; margin: 0 0 8px; }
.calc-sub { font-size: 14px; line-height: 1.7; opacity: 0.92; margin: 0; }
.calc-body { max-width: 960px; margin: 0 auto; padding: 16px; }
.calc-card { border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06); }
.calc-result { margin-top: 16px; }
.assumption { font-size: 12.5px; color: var(--color-text-secondary, #4b5563); margin-top: 6px; }
@media (max-width: 640px) { .calc-hero { padding: 24px 12px 8px; } }
</style>
