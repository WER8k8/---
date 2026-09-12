<template>
  <YdPage title="套餐配置" subtitle="SaaS订阅套餐定义与管理" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="openCreate">+ 新建套餐</a-button>
    </template>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="cols"
        :data-source="planList"
        :loading="loading"
        :pagination="false"
        :table-props="{ rowKey: 'id', size: 'small' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <span class="font-medium">{{ record.name }}</span>
            <br />
            <span class="text-xs text-gray-400">{{ record.code }}</span>
          </template>
          <template v-else-if="column.key === 'price'">
            <div class="text-right">
              <div>¥{{ (record.price_monthly / 100).toFixed(0) }}<span class="text-xs text-gray-400">/月</span></div>
              <div class="text-xs text-gray-400">¥{{ (record.price_yearly / 100).toFixed(0) }}<span>/年</span></div>
            </div>
          </template>
          <template v-else-if="column.key === 'quotas'">
            <div class="text-center text-sm">
              用户 {{ record.max_users }} · 站点 {{ record.max_sites }} · 产品 {{ record.max_products }}
            </div>
          </template>
          <template v-else-if="column.key === 'ai_quota'">
            <span class="text-sm">{{ record.max_ai_quota > 0 ? record.max_ai_quota.toLocaleString() : '无' }}</span>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" type="link" @click="openEdit(record)">编辑</a-button>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <!-- ==================== 创建/编辑 Modal ==================== -->
    <a-modal
      v-model:open="modalOpen"
      :title="isEdit ? '编辑套餐' : '新建套餐'"
      :confirm-loading="saving"
      @ok="handleSave"
      width="600px"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="套餐名称" required>
              <a-input v-model:value="form.name" placeholder="如 基础版" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="编码" required>
              <a-input v-model:value="form.code" placeholder="如 basic" :disabled="isEdit" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider orientation="left">定价（单位：分，100分=¥1）</a-divider>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="月付价格(分)">
              <a-input-number v-model:value="form.price_monthly" :min="0" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="年付价格(分)">
              <a-input-number v-model:value="form.price_yearly" :min="0" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider orientation="left">资源配额</a-divider>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="最大用户数">
              <a-input-number v-model:value="form.max_users" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大站点数">
              <a-input-number v-model:value="form.max_sites" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大产品数">
              <a-input-number v-model:value="form.max_products" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="AI调用配额(次/月)">
          <a-input-number v-model:value="form.max_ai_quota" :min="0" style="width:200px" />
        </a-form-item>

        <a-divider orientation="left">功能与状态</a-divider>
        <a-form-item label="功能列表(JSON数组)">
          <a-textarea v-model:value="form.features" :rows="3" placeholder='["seo","analytics","ai","white_label"]' />
        </a-form-item>
        <a-form-item label="启用状态">
          <a-switch v-model:checked="form.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdDataTable, YdPage } from '@/components/youding';
import { apiGet, apiPost, apiPut } from '@/utils/api';

// ============================================================================
// 类型定义
// ============================================================================
interface PlanRecord {
  id: string;
  name: string;
  code: string;
  price_monthly: number;
  price_yearly: number;
  max_users: number;
  max_sites: number;
  max_products: number;
  max_ai_quota: number;
  features: string;
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// 表格列
// ============================================================================
const cols = [
  { key: 'name', title: '名称/编码', dataIndex: 'name', width: 160 },
  { key: 'price', title: '定价', dataIndex: 'price_monthly', width: 130, align: 'center' as const },
  { key: 'quotas', title: '资源配额', dataIndex: 'max_users', width: 200, align: 'center' as const },
  { key: 'ai_quota', title: 'AI配额', dataIndex: 'max_ai_quota', width: 100, align: 'center' as const },
  { key: 'is_active', title: '状态', dataIndex: 'is_active', width: 80, align: 'center' as const },
  { key: 'actions', title: '操作', width: 80, align: 'center' as const },
];

// ============================================================================
// 数据加载
// ============================================================================
const loading = ref(false);
const planList = ref<PlanRecord[]>([]);
const tablePanelRef = ref<HTMLElement | null>(null);

async function loadPlans() {
  loading.value = true;
  try {
    const data = await apiGet<PlanRecord[]>('/tenants/plans');
    planList.value = Array.isArray(data) ? data : [];
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载套餐失败');
  } finally {
    loading.value = false;
  }
}

// ============================================================================
// 创建/编辑
// ============================================================================
const modalOpen = ref(false);
const isEdit = ref(false);
const saving = ref(false);
const editingId = ref('');

interface PlanForm {
  name: string;
  code: string;
  price_monthly: number;
  price_yearly: number;
  max_users: number;
  max_sites: number;
  max_products: number;
  max_ai_quota: number;
  features: string;
  is_active: boolean;
}

const defaultForm = (): PlanForm => ({
  name: '',
  code: '',
  price_monthly: 0,
  price_yearly: 0,
  max_users: 1,
  max_sites: 1,
  max_products: 10,
  max_ai_quota: 0,
  features: '[]',
  is_active: true,
});

const form = reactive<PlanForm>(defaultForm());

function openCreate() {
  Object.assign(form, defaultForm());
  isEdit.value = false;
  editingId.value = '';
  modalOpen.value = true;
}

function openEdit(record: PlanRecord) {
  form.name = record.name;
  form.code = record.code;
  form.price_monthly = record.price_monthly;
  form.price_yearly = record.price_yearly;
  form.max_users = record.max_users;
  form.max_sites = record.max_sites;
  form.max_products = record.max_products;
  form.max_ai_quota = record.max_ai_quota;
  form.features = record.features;
  form.is_active = record.is_active;
  isEdit.value = true;
  editingId.value = record.id;
  modalOpen.value = true;
}

async function handleSave() {
  if (!form.name || !form.code) {
    message.warning('请填写套餐名称和编码');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      name: form.name,
      code: form.code,
      price_monthly: form.price_monthly,
      price_yearly: form.price_yearly,
      max_users: form.max_users,
      max_sites: form.max_sites,
      max_products: form.max_products,
      max_ai_quota: form.max_ai_quota,
      features: form.features,
      is_active: form.is_active,
    };

    if (isEdit.value) {
      await apiPut(`/tenants/plans/${editingId.value}`, payload);
      message.success('套餐已更新');
    } else {
      await apiPost('/tenants/plans', payload);
      message.success('套餐已创建');
    }
    modalOpen.value = false;
    await loadPlans();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadPlans();
});
</script>

<style scoped>
.font-medium {
  font-weight: 500;
}
.text-xs {
  font-size: 12px;
}
.text-sm {
  font-size: 13px;
}
.text-right {
  text-align: right;
}
.text-center {
  text-align: center;
}
.text-gray-400 {
  color: #9ca3af;
}
</style>
