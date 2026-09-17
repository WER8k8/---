/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="许可证管理" subtitle="管理系统许可证和授权状态" surface="elevated">
    <template #actions>
      <a-button @click="showGenerateModal = true">生成许可证</a-button>
    </template>

    <a-row :gutter="24">
      <a-col :span="8">
        <a-card title="许可证状态" :bordered="false">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="当前状态">
              <a-tag :color="statusColor">{{ statusText }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="许可证密钥">
              {{ currentLicense?.license_key || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="套餐类型">
              {{ currentLicense?.plan_code || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="有效期至">
              {{ formatDate(currentLicense?.expires_at) || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="剩余天数">
              <span :class="daysClass">{{ currentLicense?.days_remaining || 0 }} 天</span>
            </a-descriptions-item>
            <a-descriptions-item label="AI 额度">
              {{ currentLicense?.ai_quota || 0 }} 次
            </a-descriptions-item>
          </a-descriptions>
          <div style="margin-top: 16px;">
            <a-input
              v-model:value="activateKey"
              placeholder="输入许可证密钥激活"
              style="margin-bottom: 8px;"
            />
            <a-button type="primary" block @click="handleActivate">激活许可证</a-button>
          </div>
        </a-card>
      </a-col>

      <a-col :span="16">
        <a-card title="许可证列表" :bordered="false">
          <a-table
            :columns="columns"
            :data-source="licenseList"
            :pagination="pagination"
            :loading="loading"
            row-key="id"
            @change="(pagination) => handleTableChange({ current: pagination.current as number, pageSize: pagination.pageSize as number })"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ getStatusText(record.status) }}</a-tag>
              </template>
              <template v-if="column.key === 'actions'">
                <a-button size="small" @click="handleView(record)">查看</a-button>
                <a-button size="small" type="primary" @click="handleUpdate(record)">编辑</a-button>
                <a-popconfirm
                  title="确定吊销此许可证吗？"
                  @confirm="handleRevoke(record.id)"
                >
                  <a-button size="small" danger>吊销</a-button>
                </a-popconfirm>
              </template>
              <template v-if="column.key === 'expires_at'">
                {{ formatDate(record.expires_at) || '-' }}
              </template>
              <template v-if="column.key === 'activated_at'">
                {{ formatDate(record.activated_at) || '-' }}
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="showGenerateModal"
      title="生成许可证"
      :footer="null"
    >
      <a-form :model="generateForm" :layout="'vertical'">
        <a-form-item label="生成数量">
          <a-input-number
            v-model:value="generateForm.count"
            :min="1"
            :max="100"
          />
        </a-form-item>
        <a-form-item label="套餐类型">
          <a-select v-model:value="generateForm.plan_code">
            <a-select-option value="free">免费版</a-select-option>
            <a-select-option value="basic">基础版</a-select-option>
            <a-select-option value="pro">专业版</a-select-option>
            <a-select-option value="enterprise">企业版</a-select-option>
            <a-select-option value="flagship">旗舰版</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="有效期（天）">
          <a-input-number
            v-model:value="generateForm.duration_days"
            :min="1"
            :max="3650"
          />
        </a-form-item>
        <a-form-item label="最大设备数">
          <a-input-number
            v-model:value="generateForm.max_devices"
            :min="1"
            :max="10"
          />
        </a-form-item>
        <a-form-item label="AI 额度">
          <a-input-number
            v-model:value="generateForm.ai_quota"
            :min="0"
          />
        </a-form-item>
      </a-form>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px;">
        <a-button @click="showGenerateModal = false">取消</a-button>
        <a-button type="primary" @click="handleGenerate">生成</a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showViewModal"
      title="许可证详情"
      :footer="null"
    >
      <a-descriptions :column="2" bordered>
        <a-descriptions-item label="许可证密钥">{{ viewData?.license_key }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(viewData?.status)">{{ getStatusText(viewData?.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="套餐类型">{{ viewData?.plan_code }}</a-descriptions-item>
        <a-descriptions-item label="租户">
          {{ viewData?.tenant?.name || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="激活时间">{{ formatDate(viewData?.activated_at) || '-' }}</a-descriptions-item>
        <a-descriptions-item label="有效期至">{{ formatDate(viewData?.expires_at) || '-' }}</a-descriptions-item>
        <a-descriptions-item label="最大设备数">{{ viewData?.max_devices }}</a-descriptions-item>
        <a-descriptions-item label="AI 额度">{{ viewData?.ai_quota }}</a-descriptions-item>
        <a-descriptions-item label="硬件ID">{{ viewData?.hardware_id || '-' }}</a-descriptions-item>
        <a-descriptions-item label="备注">{{ viewData?.notes || '-' }}</a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ formatDate(viewData?.created_at) || '-' }}</a-descriptions-item>
        <a-descriptions-item label="更新时间">{{ formatDate(viewData?.updated_at) || '-' }}</a-descriptions-item>
      </a-descriptions>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <a-button @click="showViewModal = false">关闭</a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showUpdateModal"
      title="编辑许可证"
      :footer="null"
    >
      <a-form :model="updateForm" :layout="'vertical'">
        <a-form-item label="套餐类型">
          <a-select v-model:value="updateForm.plan_code">
            <a-select-option value="free">免费版</a-select-option>
            <a-select-option value="basic">基础版</a-select-option>
            <a-select-option value="pro">专业版</a-select-option>
            <a-select-option value="enterprise">企业版</a-select-option>
            <a-select-option value="flagship">旗舰版</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="有效期至">
          <a-date-picker
            v-model:value="updateForm.expires_at"
            show-time
            style="width: 100%;"
          />
        </a-form-item>
        <a-form-item label="最大设备数">
          <a-input-number
            v-model:value="updateForm.max_devices"
            :min="1"
            :max="10"
          />
        </a-form-item>
        <a-form-item label="AI 额度">
          <a-input-number
            v-model:value="updateForm.ai_quota"
            :min="0"
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="updateForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end; gap: 8px;">
        <a-button @click="showUpdateModal = false">取消</a-button>
        <a-button type="primary" @click="handleUpdateSubmit">保存</a-button>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import dayjs, { type Dayjs } from 'dayjs';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';

interface LicenseItem {
  id: string;
  license_key: string;
  plan_code: string;
  status: string;
  tenant_id: string | null;
  tenant?: { name: string };
  activated_at: string | null;
  expires_at: string | null;
  hardware_id: string | null;
  max_devices: number;
  ai_quota: number;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface LicenseStatus {
  has_license: boolean;
  status: string;
  license_key?: string;
  plan_code?: string;
  expires_at?: string;
  days_remaining?: number;
  ai_quota?: number;
  activated_at?: string;
}

const loading = ref(false);
const licenseList = ref<LicenseItem[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const currentLicense = ref<LicenseStatus | null>(null);
const activateKey = ref('');

const showGenerateModal = ref(false);
const generateForm = reactive({
  count: 1,
  plan_code: 'pro',
  duration_days: 365,
  max_devices: 1,
  ai_quota: 10000,
});

const showViewModal = ref(false);
const viewData = ref<LicenseItem | null>(null);

const showUpdateModal = ref(false);
const updateForm = reactive({
  plan_code: 'pro',
  expires_at: undefined as Dayjs | undefined,
  max_devices: 1,
  ai_quota: 10000,
  notes: '',
});
const updateId = ref('');

const columns = [
  {
    title: '许可证密钥',
    dataIndex: 'license_key',
    key: 'license_key',
    width: 200,
  },
  {
    title: '套餐类型',
    dataIndex: 'plan_code',
    key: 'plan_code',
    width: 100,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
  },
  {
    title: '激活时间',
    dataIndex: 'activated_at',
    key: 'activated_at',
    width: 170,
  },
  {
    title: '有效期至',
    dataIndex: 'expires_at',
    key: 'expires_at',
    width: 170,
  },
  {
    title: 'AI 额度',
    dataIndex: 'ai_quota',
    key: 'ai_quota',
    width: 80,
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
  },
];

const statusText = computed(() => {
  if (!currentLicense.value) return '未激活';
  if (currentLicense.value.status === 'expired') return '已过期';
  if (currentLicense.value.status === 'active') return '已激活';
  return currentLicense.value.status;
});

const statusColor = computed(() => {
  if (!currentLicense.value) return 'default';
  if (currentLicense.value.status === 'expired') return 'error';
  if (currentLicense.value.status === 'active') return 'success';
  return 'default';
});

const daysClass = computed(() => {
  if (!currentLicense.value) return '';
  if ((currentLicense.value.days_remaining || 0) < 7) return 'text-red-500';
  if ((currentLicense.value.days_remaining || 0) < 30) return 'text-yellow-500';
  return '';
});

function getStatusColor(status: string | undefined) {
  switch (status) {
    case 'active':
      return 'success';
    case 'expired':
      return 'error';
    case 'revoked':
      return 'default';
    case 'inactive':
      return 'warning';
    default:
      return 'default';
  }
}

function getStatusText(status: string | undefined) {
  switch (status) {
    case 'active':
      return '已激活';
    case 'expired':
      return '已过期';
    case 'revoked':
      return '已吊销';
    case 'inactive':
      return '未激活';
    default:
      return status || '-';
  }
}

function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

async function fetchLicenseList() {
  loading.value = true;
  try {
    const res = await apiGet('/license', {
      page: pagination.current,
      page_size: pagination.pageSize,
    });
    licenseList.value = res.data || [];
    pagination.total = res.total || 0;
  } catch (error) {
    message.error('获取许可证列表失败');
  } finally {
    loading.value = false;
  }
}

async function fetchLicenseStatus() {
  try {
    const res = await apiGet('/license/status');
    currentLicense.value = res.data || null;
  } catch (error) {
    currentLicense.value = null;
  }
}

function handleTableChange(pager: { current: number; pageSize: number }) {
  pagination.current = pager.current;
  pagination.pageSize = pager.pageSize;
  fetchLicenseList();
}

async function handleActivate() {
  if (!activateKey.value.trim()) {
    message.warning('请输入许可证密钥');
    return;
  }
  try {
    await apiPost('/license/activate', {
      license_key: activateKey.value.trim(),
    });
    message.success('许可证激活成功');
    activateKey.value = '';
    fetchLicenseStatus();
    fetchLicenseList();
  } catch (error: any) {
    message.error(error.message || '激活失败');
  }
}

async function handleGenerate() {
  try {
    await apiPost('/license/generate', generateForm);
    message.success('许可证生成成功');
    showGenerateModal.value = false;
    fetchLicenseList();
  } catch (error: any) {
    message.error(error.message || '生成失败');
  }
}

async function handleView(record: Record<string, any>) {
  try {
    const res = await apiGet(`/license/${record.id}`);
    viewData.value = res.data as LicenseItem;
    showViewModal.value = true;
  } catch (error) {
    message.error('获取详情失败');
  }
}

function handleUpdate(record: Record<string, any>) {
  updateId.value = record.id;
  updateForm.plan_code = record.plan_code;
  updateForm.expires_at = record.expires_at ? dayjs(record.expires_at) : undefined;
  updateForm.max_devices = record.max_devices;
  updateForm.ai_quota = record.ai_quota;
  updateForm.notes = record.notes || '';
  showUpdateModal.value = true;
}

async function handleUpdateSubmit() {
  try {
    await apiPut(`/license/${updateId.value}`, {
      plan_code: updateForm.plan_code,
      expires_at: updateForm.expires_at,
      max_devices: updateForm.max_devices,
      ai_quota: updateForm.ai_quota,
      notes: updateForm.notes,
    });
    message.success('许可证更新成功');
    showUpdateModal.value = false;
    fetchLicenseList();
  } catch (error: any) {
    message.error(error.message || '更新失败');
  }
}

async function handleRevoke(id: string) {
  try {
    await apiPost(`/license/${id}/revoke`);
    message.success('许可证已吊销');
    fetchLicenseList();
    fetchLicenseStatus();
  } catch (error: any) {
    message.error(error.message || '吊销失败');
  }
}

onMounted(() => {
  fetchLicenseList();
  fetchLicenseStatus();
});
</script>
