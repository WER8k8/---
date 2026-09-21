/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="rfq-page">
    <section class="rfq-hero">
      <div class="rfq-hero-inner">
        <h1 class="rfq-title">
          提交技术需求单
        </h1>
        <p class="rfq-sub">
          填写项目信息与技术参数，我们将根据您的需求提供产品方案与报价。
          带 <span class="req">*</span> 为必填项。
        </p>
      </div>
    </section>

    <section class="rfq-body">
      <a-card
        class="rfq-form-card"
        :bordered="false"
      >
        <a-alert
          v-if="success"
          type="success"
          :message="success"
          show-icon
          closable
          class="rfq-alert"
        />
        <a-alert
          v-if="apiError"
          type="error"
          :message="apiError"
          show-icon
          closable
          class="rfq-alert"
        />

        <a-form
          :model="form"
          layout="vertical"
          @submit.prevent="onSubmit"
        >
          <!-- 项目信息 -->
          <a-divider orientation="left">
            项目信息
          </a-divider>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item
                label="项目名称"
                name="project"
              >
                <a-input
                  v-model:value="form.project"
                  placeholder="如：汉堡工业仓库防火工程"
                  allow-clear
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item
                label="项目类型"
                name="project_type"
              >
                <a-select
                  v-model:value="form.project_type"
                  placeholder="选择项目类型"
                  allow-clear
                >
                  <a-select-option value="Factory">
                    Factory 工厂
                  </a-select-option>
                  <a-select-option value="Warehouse">
                    Warehouse 仓库
                  </a-select-option>
                  <a-select-option value="Data Center">
                    Data Center 数据中心
                  </a-select-option>
                  <a-select-option value="Commercial">
                    Commercial 商业建筑
                  </a-select-option>
                  <a-select-option value="Industrial">
                    Industrial 工业建筑
                  </a-select-option>
                  <a-select-option value="Residential">
                    Residential 住宅
                  </a-select-option>
                  <a-select-option value="Other">
                    Other 其他
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="公司名称"
                name="company"
                :rules="[{ required: true, message: '请输入公司名称' }]"
              >
                <a-input
                  v-model:value="form.company"
                  placeholder="如：Global Insulation GmbH"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="所在国家"
                name="country"
                :rules="[{ required: true, message: '请输入国家' }]"
              >
                <a-input
                  v-model:value="form.country"
                  placeholder="如：Germany"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="城市"
                name="city"
              >
                <a-input
                  v-model:value="form.city"
                  placeholder="如：Hamburg"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="项目阶段"
                name="project_stage"
              >
                <a-select
                  v-model:value="form.project_stage"
                  placeholder="选择阶段"
                  allow-clear
                >
                  <a-select-option value="Concept">
                    Concept 概念设计
                  </a-select-option>
                  <a-select-option value="Design">
                    Design 设计阶段
                  </a-select-option>
                  <a-select-option value="Tender">
                    Tender 招标阶段
                  </a-select-option>
                  <a-select-option value="Procurement">
                    Procurement 采购阶段
                  </a-select-option>
                  <a-select-option value="Construction">
                    Construction 施工阶段
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="应用场景"
                name="application"
                :rules="[{ required: true, message: '请输入应用场景' }]"
              >
                <a-input
                  v-model:value="form.application"
                  placeholder="如：钢结构防火、管道保温"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="期望交期"
                name="delivery_date"
              >
                <a-date-picker
                  v-model:value="form.delivery_date"
                  placeholder="选择日期"
                  style="width:100%"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <!-- 联系人信息 -->
          <a-divider orientation="left">
            联系人信息
          </a-divider>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="联系人"
                name="contact_name"
                :rules="[{ required: true, message: '请输入联系人' }]"
              >
                <a-input
                  v-model:value="form.contact_name"
                  placeholder="姓名"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="邮箱"
                name="email"
                :rules="[{ required: true, type: 'email', message: '请输入有效邮箱' }]"
              >
                <a-input
                  v-model:value="form.email"
                  placeholder="Email"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="电话"
                name="phone"
              >
                <a-input
                  v-model:value="form.phone"
                  placeholder="手机号/国际电话"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <!-- 技术需求 -->
          <a-divider orientation="left">
            技术要求
          </a-divider>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="防火等级"
                name="fire_rating"
              >
                <a-input
                  v-model:value="form.req_fire_rating"
                  placeholder="如 A2 / B1 / B2"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="执行标准"
                name="standard"
              >
                <a-input
                  v-model:value="form.req_standard"
                  placeholder="如 EN 13501 / GB/T 25975"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="导热系数上限"
                name="thermal"
              >
                <a-input-number
                  v-model:value="form.req_thermal"
                  :min="0"
                  :step="0.001"
                  placeholder="W/(m·K)"
                  style="width:100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="基材/系统"
                name="substrate"
              >
                <a-input
                  v-model:value="form.req_substrate"
                  placeholder="如：钢结构、混凝土"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="使用环境"
                name="environment"
              >
                <a-select
                  v-model:value="form.req_environment"
                  placeholder="选择环境"
                  allow-clear
                >
                  <a-select-option value="高温">
                    高温
                  </a-select-option>
                  <a-select-option value="防火">
                    防火
                  </a-select-option>
                  <a-select-option value="潮湿">
                    潮湿
                  </a-select-option>
                  <a-select-option value="腐蚀">
                    腐蚀
                  </a-select-option>
                  <a-select-option value="低温">
                    低温
                  </a-select-option>
                  <a-select-option value="户外">
                    户外
                  </a-select-option>
                  <a-select-option value="室内">
                    室内
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="安装方式"
                name="installation"
              >
                <a-select
                  v-model:value="form.req_installation"
                  placeholder="选择安装方式"
                  allow-clear
                >
                  <a-select-option value="粘贴">
                    粘贴
                  </a-select-option>
                  <a-select-option value="干挂">
                    干挂
                  </a-select-option>
                  <a-select-option value="装配式">
                    装配式
                  </a-select-option>
                  <a-select-option value="浇筑">
                    浇筑
                  </a-select-option>
                  <a-select-option value="喷涂">
                    喷涂
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <!-- 商业信息 -->
          <a-divider orientation="left">
            商业条款
          </a-divider>
          <a-row :gutter="16">
            <a-col :span="6">
              <a-form-item
                label="数量"
                name="quantity"
              >
                <a-input-number
                  v-model:value="form.quantity"
                  :min="0"
                  :step="1"
                  style="width:100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item
                label="单位"
                name="quantity_unit"
              >
                <a-select
                  v-model:value="form.quantity_unit"
                  placeholder="单位"
                  allow-clear
                >
                  <a-select-option value="m2">
                    m2 平方米
                  </a-select-option>
                  <a-select-option value="m3">
                    m3 立方米
                  </a-select-option>
                  <a-select-option value="kg">
                    kg 千克
                  </a-select-option>
                  <a-select-option value="pcs">
                    pcs 件
                  </a-select-option>
                  <a-select-option value="lm">
                    lm 延米
                  </a-select-option>
                  <a-select-option value="panel">
                    panel 张
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item
                label="贸易条款"
                name="incoterm"
              >
                <a-select
                  v-model:value="form.incoterm"
                  placeholder="Incoterm"
                  allow-clear
                >
                  <a-select-option value="EXW">
                    EXW 工厂交货
                  </a-select-option>
                  <a-select-option value="FOB">
                    FOB 船上交货
                  </a-select-option>
                  <a-select-option value="CIF">
                    CIF 成本+保险+运费
                  </a-select-option>
                  <a-select-option value="DAP">
                    DAP 目的地交货
                  </a-select-option>
                  <a-select-option value="DDP">
                    DDP 完税交货
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item
                label="货币"
                name="currency"
              >
                <a-select
                  v-model:value="form.currency"
                  placeholder="货币"
                >
                  <a-select-option value="USD">
                    USD 美元
                  </a-select-option>
                  <a-select-option value="EUR">
                    EUR 欧元
                  </a-select-option>
                  <a-select-option value="CNY">
                    CNY 人民币
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="24">
              <a-form-item
                label="补充说明"
                name="notes"
              >
                <a-textarea
                  v-model:value="form.notes"
                  :rows="3"
                  placeholder="技术参数、施工要求、特殊认证等补充信息"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              :loading="loading"
              block
              size="large"
            >
              提交技术需求单
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  Alert as AAlert,
  Button as AButton,
  Card as ACard,
  Col as ACol,
  DatePicker as ADatePicker,
  Divider as ADivider,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputNumber as AInputNumber,
  Row as ARow,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
} from 'ant-design-vue'
import { useApi } from '~/composables/useApi'
import { useSeoMeta } from '#imports'

useSeoMeta({
  title: '提交技术需求单 - 产品匹配与报价',
  description: '提交您的项目需求与技术参数，优丁为您匹配符合技术要求的建材产品并获得项目报价。',
})

interface RFQItem {
  product_name: string
  product_slug?: string
  quantity?: number
  unit?: string
}

interface RFQRequirement {
  req_key: string
  req_label?: string
  req_value?: string
  required: boolean
}

const api = useApi()

const form = reactive({
  company: '',
  country: '',
  city: '',
  project: '',
  project_type: undefined as string | undefined,
  project_stage: undefined as string | undefined,
  application: '',
  contact_name: '',
  email: '',
  phone: '',
  delivery_date: undefined as any,
  incoterm: undefined as string | undefined,
  currency: 'USD',
  quantity: undefined as number | undefined,
  quantity_unit: undefined as string | undefined,
  notes: '',
  req_fire_rating: '',
  req_standard: '',
  req_thermal: undefined as number | undefined,
  req_substrate: '',
  req_environment: undefined as string | undefined,
  req_installation: undefined as string | undefined,
})

const loading = ref(false)
const apiError = ref('')
const success = ref('')

async function onSubmit(): Promise<void> {
  if (!form.company.trim() || !form.country.trim() || !form.application.trim() || !form.email.trim() || !form.contact_name.trim()) {
    apiError.value = '请填写公司、国家、应用场景、联系人及邮箱（必填项）'
    return
  }
  loading.value = true
  apiError.value = ''
  success.value = ''

  const requirements: RFQRequirement[] = []
  if (form.req_fire_rating) requirements.push({ req_key: 'fire_rating', req_label: '防火等级', req_value: form.req_fire_rating, required: true })
  if (form.req_standard) requirements.push({ req_key: 'standard', req_label: '执行标准', req_value: form.req_standard, required: true })
  if (form.req_thermal) requirements.push({ req_key: 'thermal_conductivity', req_label: '导热系数上限', req_value: String(form.req_thermal), required: true })
  if (form.req_substrate) requirements.push({ req_key: 'substrate', req_label: '基材/系统', req_value: form.req_substrate, required: true })
  if (form.req_environment) requirements.push({ req_key: 'environment', req_label: '使用环境', req_value: form.req_environment, required: true })
  if (form.req_installation) requirements.push({ req_key: 'installation', req_label: '安装方式', req_value: form.req_installation, required: true })

  const deliveryStr = form.delivery_date ? (typeof form.delivery_date === 'object' ? form.delivery_date.format('YYYY-MM-DD') : String(form.delivery_date)) : undefined

  try {
    const payload = {
      company: form.company.trim(),
      company_domain: '',
      country: form.country.trim(),
      city: form.city.trim() || undefined,
      project: form.project.trim() || undefined,
      project_type: form.project_type || undefined,
      project_stage: form.project_stage || undefined,
      application: form.application.trim(),
      contact_name: form.contact_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || undefined,
      quantity: form.quantity || undefined,
      quantity_unit: form.quantity_unit || undefined,
      delivery_date: deliveryStr,
      incoterm: form.incoterm || undefined,
      currency: form.currency,
      notes: form.notes.trim() || undefined,
      source: 'rfq_form',
      source_channel: 'web_form',
      requirements: requirements.length > 0 ? requirements : undefined,
    }
    await api.post('/rfq', payload, { skipAuth: true })
    success.value = '技术需求单已提交成功！我们的技术团队将在 24 小时内与您联系。'
    // reset form
    form.company = ''; form.country = ''; form.city = ''; form.project = ''
    form.project_type = undefined; form.project_stage = undefined; form.application = ''
    form.contact_name = ''; form.email = ''; form.phone = ''
    form.delivery_date = undefined; form.incoterm = undefined; form.currency = 'USD'
    form.quantity = undefined; form.quantity_unit = undefined; form.notes = ''
    form.req_fire_rating = ''; form.req_standard = ''; form.req_thermal = undefined
    form.req_substrate = ''; form.req_environment = undefined; form.req_installation = undefined
  } catch (e: unknown) {
    apiError.value = e instanceof Error ? e.message : '提交失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.rfq-page {
  min-height: 100vh;
  background: var(--color-bg, #f5f7fa);
  padding-bottom: 64px;
}
.rfq-hero {
  padding: 32px 16px 8px;
  background: linear-gradient(135deg, #1a365d, #2563eb);
}
.rfq-hero-inner {
  max-width: 960px;
  margin: 0 auto;
  color: #fff;
}
.rfq-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px;
}
.rfq-sub {
  font-size: 14px;
  line-height: 1.7;
  opacity: 0.92;
  margin: 0;
}
.req { color: #ff4d4f; }
.rfq-body {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
}
.rfq-form-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.rfq-alert {
  margin-bottom: 16px;
  border-radius: 8px;
}
@media (max-width: 640px) {
  .rfq-hero { padding: 24px 12px 8px; }
}
</style>
