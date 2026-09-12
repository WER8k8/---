<template>
  <YdPage title="矩阵系统设置" subtitle="配置 SEO 矩阵系统的各项参数" surface="elevated">
    <template #actions>
      <a-button type="primary" class="gradient-primary" :loading="loading" @click="saveSettings">
        <SaveOutlined class="w-4 h-4 mr-2" />
        保存设置
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <SettingOutlined class="w-5 h-5 mr-2 text-primary-500" />
            AI生成配置
          </h3>
          <div class="space-y-6">
            <a-form-item
              label="生成模式"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-select
                v-model:value="settings.ai.generation_mode"
                placeholder="请选择生成模式"
                class="w-64"
              >
                <a-select-option value="fast">
                  快速生成
                </a-select-option>
                <a-select-option value="standard">
                  标准生成
                </a-select-option>
                <a-select-option value="advanced">
                  高级生成
                </a-select-option>
              </a-select>
            </a-form-item>

            <a-form-item
              label="生成数量"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-input-number
                v-model:value="settings.ai.batch_count"
                :min="1"
                :max="100"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">每次批量生成的关键词数量</span>
            </a-form-item>

            <a-form-item
              label="内容长度"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-input-number
                v-model:value="settings.ai.content_length"
                :min="200"
                :max="3000"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">生成文案的字符数</span>
            </a-form-item>

            <a-form-item
              label="去重模式"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-switch
                v-model:checked="settings.ai.deduplicate"
                checked-children="开启"
                un-checked-children="关闭"
              />
              <span class="ml-3 text-gray-500">自动去除重复内容</span>
            </a-form-item>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-card p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <SendOutlined class="w-5 h-5 mr-2 text-primary-500" />
            发布配置
          </h3>
          <div class="space-y-6">
            <a-form-item
              label="发布间隔"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-input-number
                v-model:value="settings.publish.interval"
                :min="1"
                :max="60"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">每次发布间隔（秒）</span>
            </a-form-item>

            <a-form-item
              label="每日发布上限"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-input-number
                v-model:value="settings.publish.daily_limit"
                :min="1"
                :max="1000"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">每日最多发布数量</span>
            </a-form-item>

            <a-form-item
              label="自动重试"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-input-number
                v-model:value="settings.publish.max_retries"
                :min="0"
                :max="10"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">失败后自动重试次数</span>
            </a-form-item>

            <a-form-item
              label="启用反风控"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-switch
                v-model:checked="settings.publish.anti_risk"
                checked-children="开启"
                un-checked-children="关闭"
              />
              <span class="ml-3 text-gray-500">智能规避平台风控检测</span>
            </a-form-item>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-card p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <ClockCircleOutlined class="w-5 h-5 mr-2 text-primary-500" />
            定时任务配置
          </h3>
          <div class="space-y-6">
            <a-form-item
              label="自动生成时间"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-time-picker
                v-model:value="settings.schedule.generate_time"
                format="HH:mm"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">每天自动生成关键词的时间</span>
            </a-form-item>

            <a-form-item
              label="自动发布时间"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-time-picker
                v-model:value="settings.schedule.publish_time"
                format="HH:mm"
                class="w-40"
              />
              <span class="ml-3 text-gray-500">每天自动发布的时间</span>
            </a-form-item>

            <a-form-item
              label="自动收录检测"
              :label-col="{ span: 5 }"
              :wrapper-col="{ span: 19 }"
            >
              <a-switch
                v-model:checked="settings.schedule.auto_check_inclusion"
                checked-children="开启"
                un-checked-children="关闭"
              />
              <span class="ml-3 text-gray-500">自动检测已发布内容的收录状态</span>
            </a-form-item>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            快速操作
          </h3>
          <div class="space-y-3">
            <a-button
              block
              type="primary"
              class="gradient-primary"
              @click="resetSettings"
            >
              <UndoOutlined class="w-4 h-4 mr-2" />
              重置为默认
            </a-button>
            <a-button
              block
              @click="exportSettings"
            >
              <ExportOutlined class="w-4 h-4 mr-2" />
              导出配置
            </a-button>
            <a-button
              block
              @click="importSettings"
            >
              <ImportOutlined class="w-4 h-4 mr-2" />
              导入配置
            </a-button>
          </div>
        </div>

        <div class="bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl p-6 text-white">
          <h3 class="text-lg font-semibold mb-4">
            系统状态
          </h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-white/80">AI引擎状态</span>
              <span class="flex items-center">
                <span class="w-2 h-2 bg-green-400 rounded-full mr-2" />
                运行中
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-white/80">发布队列</span>
              <span>{{ settings.system.queue_count }} 任务等待</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-white/80">上次更新</span>
              <span class="text-white/80">{{ settings.system.last_update }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-white/80">系统版本</span>
              <span>{{ settings.system.version }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import {
  SettingOutlined,
  SaveOutlined,
  SendOutlined,
  ClockCircleOutlined,
  UndoOutlined,
  ExportOutlined,
  ImportOutlined,
} from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import { seoMatrixAPI, unwrapApiData } from '@/api';

const settings = reactive({
  ai: {
    generation_mode: 'standard',
    batch_count: 20,
    content_length: 800,
    deduplicate: true,
  },
  publish: {
    interval: 30,
    daily_limit: 100,
    max_retries: 3,
    anti_risk: true,
  },
  schedule: {
    generate_time: '09:00',
    publish_time: '10:00',
    auto_check_inclusion: true,
  },
  system: {
    queue_count: 0,
    last_update: '刚刚',
    version: '1.0.0',
  },
});

const loading = ref(false);

async function saveSettings() {
  loading.value = true;
  try {
    await seoMatrixAPI.updateSettings(settings);
    alert('设置保存成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to save settings:', e);
    alert('保存失败');
  } finally {
    loading.value = false;
  }
}

function resetSettings() {
  settings.ai = {
    generation_mode: 'standard',
    batch_count: 20,
    content_length: 800,
    deduplicate: true,
  };
  settings.publish = {
    interval: 30,
    daily_limit: 100,
    max_retries: 3,
    anti_risk: true,
  };
  settings.schedule = {
    generate_time: '09:00',
    publish_time: '10:00',
    auto_check_inclusion: true,
  };
}

function exportSettings() {
  const dataStr = JSON.stringify(settings, null, 2);
  const blob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'seo-matrix-settings.json';
  link.click();
  URL.revokeObjectURL(url);
}

function importSettings() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    const text = await file.text();
    try {
      const imported = JSON.parse(text);
      Object.assign(settings, imported);
      alert('配置导入成功');
    } catch {
      alert('无效的配置文件');
    }
  };
  input.click();
}

async function fetchSettings() {
  try {
    const res = await seoMatrixAPI.getSettings();
    const d = unwrapApiData<Record<string, unknown>>(res);
    if (d && typeof d === 'object') Object.assign(settings as any, d);
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch settings:', e);
  }
}

onMounted(() => {
  fetchSettings();
});
</script>
