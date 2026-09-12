<template>
  <YdPage title="系统配置" subtitle="配置系统参数和运行环境设置" surface="elevated">
    <template #actions>
      <a-button @click="resetConfig">重置</a-button>
      <a-button type="primary" @click="saveConfig">保存配置</a-button>
    </template>
  <div class="config-page">
    <div class="config-sections">
      <div
        class="config-section"
        v-for="section in configSections"
        :key="section.name"
      >
        <div class="section-header">
          <component
            :is="section.icon"
            class="section-icon"
          />
          <h2 class="section-title">
            {{ section.name }}
          </h2>
        </div>
        <a-form
          :model="section.form"
          :layout="'vertical'"
          class="config-form"
        >
          <a-form-item
            v-for="item in section.items"
            :key="item.key"
            :label="item.label"
            :tooltip="item.description"
          >
            <template v-if="item.type === 'switch'">
              <a-switch
                v-model:checked="section.form[item.key]"
                @change="handleConfigChange(section.name, item.key, $event)"
              />
            </template>
            <template v-else-if="item.type === 'select'">
              <a-select
                v-model:value="section.form[item.key]"
                class="config-select"
                @change="handleConfigChange(section.name, item.key, $event)"
              >
                <a-select-option
                  v-for="option in item.options"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </a-select-option>
              </a-select>
            </template>
            <template v-else-if="item.type === 'textarea'">
              <a-textarea
                v-model:value="section.form[item.key]"
                :rows="3"
                class="config-textarea"
                @change="handleConfigChange(section.name, item.key, $event)"
              />
            </template>
            <template v-else>
              <a-input
                v-model:value="section.form[item.key]"
                class="config-input"
                @change="handleConfigChange(section.name, item.key, $event)"
              />
            </template>
          </a-form-item>
        </a-form>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
  ToolOutlined,
  GlobalOutlined,
  SafetyOutlined,
  CloudOutlined,
  BellOutlined,
} from '@ant-design/icons-vue';

interface ConfigItem {
  key: string;
  label: string;
  description: string;
  type: string;
  options?: { value: string; label: string }[];
}

interface ConfigSection {
  name: string;
  icon: any;
  form: Record<string, any>;
  items: ConfigItem[];
}

const configSections = ref<ConfigSection[]>([
  {
    name: '基本设置',
    icon: GlobalOutlined,
    form: reactive({
      siteName: 'Trae智能开发平台',
      siteDesc: 'AI驱动的智能开发工具',
      defaultLanguage: 'zh-CN',
    }),
    items: [
      { key: 'siteName', label: '站点名称', description: '系统显示的站点名称', type: 'input' },
      { key: 'siteDesc', label: '站点描述', description: '站点的简短描述', type: 'textarea' },
      {
        key: 'defaultLanguage',
        label: '默认语言',
        description: '系统默认显示语言',
        type: 'select',
        options: [
          { value: 'zh-CN', label: '中文' },
          { value: 'en-US', label: 'English' },
        ],
      },
    ],
  },
  {
    name: '安全设置',
    icon: SafetyOutlined,
    form: reactive({
      enableCaptcha: true,
      sessionTimeout: 30,
      enableRateLimit: true,
    }),
    items: [
      {
        key: 'enableCaptcha',
        label: '启用验证码',
        description: '登录时启用图形验证码',
        type: 'switch',
      },
      {
        key: 'sessionTimeout',
        label: '会话超时时间',
        description: '用户会话超时时间（分钟）',
        type: 'input',
      },
      {
        key: 'enableRateLimit',
        label: '启用限流',
        description: '启用API请求限流保护',
        type: 'switch',
      },
    ],
  },
  {
    name: '存储设置',
    icon: CloudOutlined,
    form: reactive({
      storageType: 'local',
      maxUploadSize: 100,
      enableCompression: true,
    }),
    items: [
      {
        key: 'storageType',
        label: '存储类型',
        description: '文件存储方式',
        type: 'select',
        options: [
          { value: 'local', label: '本地存储' },
          { value: 'oss', label: '阿里云OSS' },
          { value: 'cos', label: '腾讯云COS' },
        ],
      },
      {
        key: 'maxUploadSize',
        label: '最大上传大小',
        description: '单个文件最大上传大小（MB）',
        type: 'input',
      },
      {
        key: 'enableCompression',
        label: '启用压缩',
        description: '上传文件自动压缩',
        type: 'switch',
      },
    ],
  },
  {
    name: '通知设置',
    icon: BellOutlined,
    form: reactive({
      enableEmailNotify: true,
      enableSmsNotify: false,
      enablePushNotify: true,
    }),
    items: [
      {
        key: 'enableEmailNotify',
        label: '启用邮件通知',
        description: '发送邮件通知',
        type: 'switch',
      },
      {
        key: 'enableSmsNotify',
        label: '启用短信通知',
        description: '发送短信通知',
        type: 'switch',
      },
      {
        key: 'enablePushNotify',
        label: '启用推送通知',
        description: '发送系统推送通知',
        type: 'switch',
      },
    ],
  },
]);

const handleConfigChange = (_section: string, _key: string, _value: any) => {
  /* 演示页：变更仅保存在内存，保存时统一提示 */
};

const resetConfig = () => {
  configSections.value = [
    {
      name: '基本设置',
      icon: GlobalOutlined,
      form: reactive({
        siteName: 'Trae智能开发平台',
        siteDesc: 'AI驱动的智能开发工具',
        defaultLanguage: 'zh-CN',
      }),
      items: [
        { key: 'siteName', label: '站点名称', description: '系统显示的站点名称', type: 'input' },
        { key: 'siteDesc', label: '站点描述', description: '站点的简短描述', type: 'textarea' },
        {
          key: 'defaultLanguage',
          label: '默认语言',
          description: '系统默认显示语言',
          type: 'select',
          options: [
            { value: 'zh-CN', label: '中文' },
            { value: 'en-US', label: 'English' },
          ],
        },
      ],
    },
    {
      name: '安全设置',
      icon: SafetyOutlined,
      form: reactive({
        enableCaptcha: true,
        sessionTimeout: 30,
        enableRateLimit: true,
      }),
      items: [
        {
          key: 'enableCaptcha',
          label: '启用验证码',
          description: '登录时启用图形验证码',
          type: 'switch',
        },
        {
          key: 'sessionTimeout',
          label: '会话超时时间',
          description: '用户会话超时时间（分钟）',
          type: 'input',
        },
        {
          key: 'enableRateLimit',
          label: '启用限流',
          description: '启用API请求限流保护',
          type: 'switch',
        },
      ],
    },
    {
      name: '存储设置',
      icon: CloudOutlined,
      form: reactive({
        storageType: 'local',
        maxUploadSize: 100,
        enableCompression: true,
      }),
      items: [
        {
          key: 'storageType',
          label: '存储类型',
          description: '文件存储方式',
          type: 'select',
          options: [
            { value: 'local', label: '本地存储' },
            { value: 'oss', label: '阿里云OSS' },
            { value: 'cos', label: '腾讯云COS' },
          ],
        },
        {
          key: 'maxUploadSize',
          label: '最大上传大小',
          description: '单个文件最大上传大小（MB）',
          type: 'input',
        },
        {
          key: 'enableCompression',
          label: '启用压缩',
          description: '上传文件自动压缩',
          type: 'switch',
        },
      ],
    },
    {
      name: '通知设置',
      icon: BellOutlined,
      form: reactive({
        enableEmailNotify: true,
        enableSmsNotify: false,
        enablePushNotify: true,
      }),
      items: [
        {
          key: 'enableEmailNotify',
          label: '启用邮件通知',
          description: '发送邮件通知',
          type: 'switch',
        },
        {
          key: 'enableSmsNotify',
          label: '启用短信通知',
          description: '发送短信通知',
          type: 'switch',
        },
        {
          key: 'enablePushNotify',
          label: '启用推送通知',
          description: '发送系统推送通知',
          type: 'switch',
        },
      ],
    },
  ];
};

const saveConfig = () => {
  message.success('配置已保存（演示，可对接后端持久化）');
};

onMounted(async () => {
  try { await apiGet('/system-config'); } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.config-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .page-desc {
    font-size: 14px;
    color: #6b7280;
    margin-top: 4px;
  }
}

.config-sections {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 24px;

  .config-section {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .section-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid #f3f4f6;

      .section-icon {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: #fff;
      }

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
      }
    }

    .config-form {
      .config-select,
      .config-input,
      .config-textarea {
        width: 100%;
      }
    }
  }
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

@media (max-width: 1024px) {
  .config-sections {
    grid-template-columns: 1fr;
  }
}
</style>
