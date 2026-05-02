<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          系统设置
        </h1>
        <p class="text-gray-500 mt-1">
          配置系统参数和AI设置
        </p>
      </div>
    </div>

    <a-card
      title="AI模型配置"
      class="mb-6"
    >
      <a-form
        :model="aiConfig"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="默认AI模型"
              :required="true"
            >
              <a-select v-model="aiConfig.default_model">
                <a-select-option
                  v-for="model in availableModels"
                  :key="model"
                  :value="model"
                >
                  {{ model }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="温度参数">
              <a-input-number
                v-model="aiConfig.temperature"
                :min="0"
                :max="1"
                :step="0.1"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大Token数">
              <a-input-number
                v-model="aiConfig.max_tokens"
                :min="100"
                :max="8000"
                :step="100"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="API超时时间(秒)">
              <a-input-number
                v-model="aiConfig.timeout"
                :min="10"
                :max="120"
                :step="5"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="flex justify-end">
          <a-button
            type="primary"
            @click="saveAIConfig"
          >
            保存配置
          </a-button>
        </div>
      </a-form>
    </a-card>

    <a-card title="系统参数">
      <a-form
        :model="systemConfig"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="网站标题">
              <a-input v-model="systemConfig.site_title" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="网站描述">
              <a-input v-model="systemConfig.site_description" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="默认语言">
              <a-select v-model="systemConfig.default_language">
                <a-select-option value="zh-CN">
                  中文
                </a-select-option>
                <a-select-option value="en">
                  English
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="时区">
              <a-select v-model="systemConfig.timezone">
                <a-select-option value="Asia/Shanghai">
                  中国标准时间
                </a-select-option>
                <a-select-option value="UTC">
                  UTC
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="系统维护模式">
          <a-switch v-model="systemConfig.maintenance_mode" />
          <span class="ml-2 text-sm text-gray-500">开启后网站将进入维护状态</span>
        </a-form-item>
        <div class="flex justify-end">
          <a-button
            type="primary"
            @click="saveSystemConfig"
          >
            保存配置
          </a-button>
        </div>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

const availableModels = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-sonnet', 'claude-3-opus']

const aiConfig = reactive({
  default_model: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 2000,
  timeout: 30,
})

const systemConfig = reactive({
  site_title: '优丁保温建材',
  site_description: '专业的保温建材供应商',
  default_language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  maintenance_mode: false,
})

const saveAIConfig = () => {
  message.success('AI配置已保存')
}

const saveSystemConfig = () => {
  message.success('系统配置已保存')
}

onMounted(() => {
  // Load config from API
})
</script>
