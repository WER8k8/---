/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="白标品牌" subtitle="按租户配置独立的品牌外观" surface="elevated">
    <!-- 租户选择 -->
    <div class="mb-4">
      <a-card size="small">
        <a-form layout="inline" :model="selectForm">
          <a-form-item label="选择租户">
            <a-select
              v-model:value="selectForm.tenantId"
              show-search
              placeholder="搜索并选择租户"
              style="width: 360px"
              :filter-option="false"
              :options="tenantOptions"
              @search="searchTenants"
              @change="(v) => onTenantSelect(v as string)"
            />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="loadingConfig" @click="loadConfig">加载配置</a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 白标配置表单 -->
    <template v-if="selectedTenantId">
      <a-card title="品牌配置" size="small">
        <template #extra>
          <a-tag v-if="selectedTenantName">{{ selectedTenantName }}</a-tag>
        </template>
        <a-form layout="vertical" :model="form">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="品牌名称">
                <a-input v-model:value="form.brand_name" placeholder="优丁建材" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="定制域名">
                <a-input v-model:value="form.domain" placeholder="customer.yourdomain.com" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="Logo URL">
                <a-input v-model:value="form.logo_url" placeholder="https://cdn.example.com/logo.png" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="主色调">
                <div style="display:flex;align-items:center;gap:8px">
                  <a-input v-model:value="form.primary_color" type="color" style="width:48px;padding:2px" />
                  <a-input v-model:value="form.primary_color" style="flex:1" />
                </div>
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="页脚信息">
            <a-input v-model:value="form.footer_text" placeholder="© 2024 Your Company. All rights reserved." />
          </a-form-item>
          <a-form-item label="自定义CSS">
            <a-textarea v-model:value="form.custom_css" :rows="4" placeholder="body { font-family: 'YourFont', sans-serif; }" style="font-family:monospace;font-size:13px" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="saving" @click="handleSave">保存配置</a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </template>

    <a-empty v-else description="请选择租户后加载白标配置" />
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPut } from '@/utils/api';

// ============================================================================
// 类型
// ============================================================================
interface TenantOption {
  value: string;
  label: string;
}

// ============================================================================
// 租户选择
// ============================================================================
const selectForm = reactive({ tenantId: '' });
const tenantOptions = ref<TenantOption[]>([]);
const selectedTenantId = ref('');
const selectedTenantName = ref('');
const loadingConfig = ref(false);

async function searchTenants(keyword: string) {
  if (!keyword || keyword.length < 1) {
    tenantOptions.value = [];
    return;
  }
  try {
    const data = await apiGet<{ items: Array<{ id: string; name: string }> }>('/tenants/', {
      search: keyword,
      page: 1,
      page_size: 20,
    });
    const items = data?.items || [];
    tenantOptions.value = items.map((t) => ({
      value: t.id,
      label: t.name,
    }));
  } catch {
    tenantOptions.value = [];
  }
}

function onTenantSelect(value: string) {
  selectedTenantId.value = value;
  const opt = tenantOptions.value.find((o) => o.value === value);
  selectedTenantName.value = opt?.label || '';
}

// ============================================================================
// 白标表单
// ============================================================================
const form = reactive({
  brand_name: '',
  logo_url: '',
  domain: '',
  custom_css: '',
  primary_color: '#4a9b8c',
  footer_text: '',
});

const saving = ref(false);

async function loadConfig() {
  if (!selectedTenantId.value) {
    message.warning('请先选择租户');
    return;
  }
  loadingConfig.value = true;
  try {
    const data = await apiGet<{
      brand_name?: string;
      logo_url?: string;
      domain?: string;
      custom_css?: string;
      primary_color?: string;
      footer_text?: string;
    }>(`/tenants/${selectedTenantId.value}/white-label`);
    if (data) {
      form.brand_name = data.brand_name || '';
      form.logo_url = data.logo_url || '';
      form.domain = data.domain || '';
      form.custom_css = data.custom_css || '';
      form.primary_color = data.primary_color || '#4a9b8c';
      form.footer_text = data.footer_text || '';
    }
    message.success('配置已加载');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载配置失败');
  } finally {
    loadingConfig.value = false;
  }
}

async function handleSave() {
  if (!selectedTenantId.value) {
    message.warning('请先选择租户');
    return;
  }
  saving.value = true;
  try {
    await apiPut(`/tenants/${selectedTenantId.value}/white-label`, {
      brand_name: form.brand_name || undefined,
      logo_url: form.logo_url || undefined,
      domain: form.domain || undefined,
      custom_css: form.custom_css || undefined,
      primary_color: form.primary_color || undefined,
      footer_text: form.footer_text || undefined,
    });
    message.success('白标配置已保存');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  // 预加载租户列表
  searchTenants('');
});
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
