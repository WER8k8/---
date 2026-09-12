<template>
  <YdPage title="我的 AI 配置" subtitle="配置您自己的 API Key、模型和邮箱，数据完全属于您" surface="elevated">
    <template #actions>
      <a-button @click="showHelp = true">
        <QuestionCircleOutlined />
        帮助
      </a-button>
    </template>

    <div class="ai-config-page">
      <!-- 顶部提示 -->
      <a-alert type="info" show-icon class="mb-6">
        <template #message>
          <span>您配置的 API Key、模型和邮箱将独立保存在您的账号下，其他用户无法访问。</span>
        </template>
      </a-alert>

      <a-row :gutter="24">
        <!-- 左侧：模型配置 -->
        <a-col :span="16">
          <TenantAiConfig />
        </a-col>

        <!-- 右侧：帮助信息 -->
        <a-col :span="8">
          <a-card title="配置指南" size="small">
            <div class="guide-list">
              <div class="guide-item">
                <div class="guide-title">1. 选择供应商</div>
                <div class="guide-desc">选择您使用的AI模型平台，如 OpenAI、DeepSeek、Claude 等。</div>
              </div>
              <div class="guide-item">
                <div class="guide-title">2. 配置 API Key</div>
                <div class="guide-desc">填入您的 API Key，密钥仅保存在您账号下，不会泄露。</div>
              </div>
              <div class="guide-item">
                <div class="guide-title">3. 测试连接</div>
                <div class="guide-desc">配置完成后点击「测试」，确保连接正常。</div>
              </div>
              <div class="guide-item">
                <div class="guide-title">4. 启用配置</div>
                <div class="guide-desc">选择应用范围（如自动获客、开发信等），启用配置后即可使用。</div>
              </div>
            </div>
          </a-card>

          <a-card title="支持的供应商" size="small" class="mt-4">
            <div class="provider-list">
              <a-tag v-for="p in providers" :key="p" color="blue">{{ p }}</a-tag>
            </div>
          </a-card>

          <a-card title="需要帮助？" size="small" class="mt-4">
            <p class="help-text">如果您在配置过程中遇到问题，请联系管理员或查看帮助文档。</p>
            <a-button type="link" size="small" @click="showHelp = true">
              查看完整帮助文档
            </a-button>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 帮助弹窗 -->
    <a-modal v-model:open="showHelp" title="AI 配置帮助" width="700px" :footer="null">
      <div class="help-content">
        <h3>常见问题</h3>
        <dl>
          <dt>如何获取 API Key？</dt>
          <dd>访问各供应商官网注册账号，在控制台获取 API Key。</dd>

          <dt>Base URL 填什么？</dt>
          <dd>通常填写供应商提供的 API 端点，如 https://api.openai.com/v1</dd>

          <dt>密钥安全吗？</dt>
          <dd>您的密钥仅保存在您的账号下，其他用户无法访问，系统也不会泄露您的密钥。</dd>

          <dt>如何切换模型？</dt>
          <dd>在配置列表中找到对应配置，点击「编辑」修改模型名称即可。</dd>
        </dl>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import TenantAiConfig from '@/components/whatsfinds/TenantAiConfig.vue'

const showHelp = ref(false)

const providers = [
  'OpenAI',
  'DeepSeek',
  '通义千问',
  'Claude',
  'Google Gemini',
  'Moonshot Kimi',
  '智谱 GLM',
  '百度千帆',
  '火山豆包',
  'Ollama / 本地',
  '其他兼容接口'
]
</script>

<style scoped lang="scss">
.ai-config-page {
  .guide-list {
    .guide-item {
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }

      .guide-title {
        font-weight: 500;
        margin-bottom: 4px;
        color: #333;
      }

      .guide-desc {
        font-size: 13px;
        color: #666;
      }
    }
  }

  .provider-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .help-text {
    font-size: 13px;
    color: #666;
    margin-bottom: 12px;
  }
}
</style>
