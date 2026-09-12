<template>
  <YdPage
    class="settings-glass"
    title="系统设置"
    subtitle="与 API §10 对齐：站点、SEO、系统参数（维护模式等）"
    surface="elevated"
  >
    <template #actions>
      <a-button
        type="primary"
        ghost
        :loading="loading"
        @click="loadSettings"
      >
        重新加载
      </a-button>
    </template>

    <a-alert
      v-if="loadError"
      type="warning"
      show-icon
      class="mb-4 rounded-2xl"
      :message="loadError"
    />

    <a-card class="mb-6 panel-card border-0 shadow-lg">
      <template #title>
        <span class="font-semibold">模型与 AI 调用</span>
      </template>
      <p class="text-gray-600 text-sm mb-3">
        提供商开关、调用统计等请在「集成与治理 → AI配置」中维护。
      </p>
      <a-button
        type="link"
        class="px-0"
        @click="router.push('/ai-config')"
      >
        前往 AI 配置
      </a-button>
    </a-card>

    <a-card
      title="站点信息"
      class="mb-6 panel-card border-0 shadow-lg"
    >
      <a-form
        :model="site"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="站点名称"
              required
            >
              <a-input
                v-model:value="site.name"
                placeholder="优丁建材"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="域名">
              <a-input
                v-model:value="site.domain"
                placeholder="www.example.com"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="站点描述">
          <a-textarea
            v-model:value="site.description"
            :rows="3"
          />
        </a-form-item>
        <a-form-item label="关键词（逗号分隔）">
          <a-input
            v-model:value="site.keywords"
            placeholder="轻集料,保温材料"
          />
        </a-form-item>
        <div class="flex justify-end">
          <a-button
            type="primary"
            :loading="savingSite"
            @click="saveSite"
          >
            保存站点
          </a-button>
        </div>
      </a-form>
    </a-card>

    <a-card
      title="SEO 设置"
      class="mb-6 panel-card border-0 shadow-lg"
    >
      <a-form
        :model="seo"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="标题前缀">
              <a-input v-model:value="seo.title_prefix" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Google Analytics ID">
              <a-input
                v-model:value="seo.google_analytics_id"
                placeholder="G-XXXX"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="默认 Meta 描述">
          <a-textarea
            v-model:value="seo.meta_description"
            :rows="2"
          />
        </a-form-item>
        <div class="flex justify-end">
          <a-button
            type="primary"
            :loading="savingSeo"
            @click="saveSeo"
          >
            保存 SEO
          </a-button>
        </div>
      </a-form>
    </a-card>

    <a-card
      title="系统参数"
      class="panel-card border-0 shadow-lg"
    >
      <a-form
        :model="system"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大上传大小 (MB)">
              <a-input-number
                v-model:value="system.max_upload_size"
                :min="1"
                :max="500"
                class="w-full"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="允许的文件类型（逗号分隔）">
              <a-input
                v-model:value="allowedTypesText"
                placeholder="jpg, png, pdf"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="维护模式">
          <a-switch v-model:checked="system.maintenance_mode" />
          <span class="ml-2 text-sm text-gray-500">仅超级管理员可更新系统块；维护模式将限制前台访问策略（依后端为准）</span>
        </a-form-item>
        <div class="flex justify-end">
          <a-button
            type="primary"
            :loading="savingSystem"
            @click="saveSystem"
          >
            保存系统参数
          </a-button>
        </div>
      </a-form>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'
import { YdPage } from '@/components/youding';

onMounted(async () => {
  try { await apiGet('/settings') } catch { /* 空状态 */ }
})
import { reactive, ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputNumber as AInputNumber,
  Textarea as ATextarea,
  Button as AButton,
  Row as ARow,
  Col as ACol,
  Switch as ASwitch,
  Alert as AAlert,
} from 'ant-design-vue';
import { siteSettingsAPI } from '@/api';

const router = useRouter();

const loading = ref(false);
const loadError = ref('');
const savingSite = ref(false);
const savingSeo = ref(false);
const savingSystem = ref(false);

const site = reactive({
  name: '',
  domain: '',
  description: '',
  keywords: '',
});

const seo = reactive({
  title_prefix: '',
  meta_description: '',
  google_analytics_id: '',
});

const system = reactive({
  maintenance_mode: false,
  max_upload_size: 10,
  allowed_file_types: [] as string[],
});

const allowedTypesText = computed({
  get: () => system.allowed_file_types.join(', '),
  set: (v: string) => {
    system.allowed_file_types = v
      .split(/[,，]/)
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

function applyPayload(data: Record<string, unknown>) {
  const s = data.site as Record<string, unknown> | undefined;
  const se = data.seo as Record<string, unknown> | undefined;
  const sy = data.system as Record<string, unknown> | undefined;
  if (s) {
    site.name = String(s.name ?? '');
    site.domain = String(s.domain ?? '');
    site.description = String(s.description ?? '');
    site.keywords = String(s.keywords ?? '');
  }
  if (se) {
    seo.title_prefix = String(se.title_prefix ?? '');
    seo.meta_description = String(se.meta_description ?? '');
    seo.google_analytics_id = String(se.google_analytics_id ?? '');
  }
  if (sy) {
    system.maintenance_mode = Boolean(sy.maintenance_mode);
    system.max_upload_size =
      typeof sy.max_upload_size === 'number'
        ? sy.max_upload_size
        : Number(sy.max_upload_size) || 10;
    const types = sy.allowed_file_types;
    system.allowed_file_types = Array.isArray(types) ? types.map((x) => String(x)) : [];
  }
}

async function loadSettings() {
  loading.value = true;
  loadError.value = '';
  try {
    const res = await siteSettingsAPI.get();
    const data = res.data as Record<string, unknown>;
    if (data && typeof data === 'object') {
      applyPayload(data);
    }
  } catch (e: any) {
    loadError.value =
      e?.response?.data?.message || e?.message || '加载设置失败（请检查登录与权限）';
  } finally {
    loading.value = false;
  }
}

async function saveSite() {
  savingSite.value = true;
  try {
    await siteSettingsAPI.updateSite({ ...site });
    message.success('站点设置已保存');
  } catch (e: any) {
    message.error(e?.response?.data?.message || e?.message || '保存失败');
  } finally {
    savingSite.value = false;
  }
}

async function saveSeo() {
  savingSeo.value = true;
  try {
    await siteSettingsAPI.updateSeo({ ...seo });
    message.success('SEO 设置已保存');
  } catch (e: any) {
    message.error(e?.response?.data?.message || e?.message || '保存失败');
  } finally {
    savingSeo.value = false;
  }
}

async function saveSystem() {
  savingSystem.value = true;
  try {
    await siteSettingsAPI.updateSystem({
      maintenance_mode: system.maintenance_mode,
      max_upload_size: system.max_upload_size,
      allowed_file_types: system.allowed_file_types,
    });
    message.success('系统参数已保存');
  } catch (e: any) {
    message.error(e?.response?.data?.message || e?.message || '保存失败（系统块需超级管理员）');
  } finally {
    savingSystem.value = false;
  }
}

onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.settings-glass {
  min-height: 100%;
}

.panel-card {
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
}
</style>
