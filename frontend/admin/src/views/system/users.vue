<template>
  <YdPage title="用户管理" subtitle="管理系统用户和权限" surface="elevated">
    <template #actions>
      <a-button
        type="primary"
        @click="showAddModal = true"
      >
        <PlusOutlined />
        添加用户
      </a-button>
    </template>

    <a-card>
      <div ref="tablePanelRef" class="yd-table-panel">
        <div class="table-toolbar-row mb-3">
          <YdTableToolbar
            :loading="loading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="() => fetchUsers()"
          />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="users"
          :pagination="tablePagination"
          :loading="loading"
          :table-props="{ rowKey: 'id', size: tableSize }"
          @page-change="onPageChange"
        >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ getRoleText(record.role) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at ? formatDate(record.created_at) : '-' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="text"
                @click="handleEdit(record)"
              >
                <EditOutlined />
              </a-button>
              <a-button
                type="text"
                :danger="record.is_active"
                @click="handleToggleActive(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>
              <a-button
                type="text"
                danger
                @click="handleDelete(record)"
              >
                <DeleteOutlined />
              </a-button>
            </a-space>
          </template>
        </template>
        </YdDataTable>
      </div>
    </a-card>

    <a-modal
      v-model:open="showAddModal"
      :title="isEdit ? '编辑用户' : '添加用户'"
      @ok="handleSave"
    >
      <a-form
        :model="form"
        layout="vertical"
      >
        <a-form-item
          label="用户名"
          :required="true"
        >
          <a-input
            v-model="form.username"
            placeholder="请输入用户名"
          />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input
            v-model="form.email"
            placeholder="请输入邮箱"
          />
        </a-form-item>
        <a-form-item
          label="密码"
          :required="!isEdit"
        >
          <a-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
          />
        </a-form-item>
        <a-form-item
          label="角色"
          :required="true"
        >
          <a-select v-model="form.role">
            <a-select-option value="admin">
              管理员
            </a-select-option>
            <a-select-option value="editor">
              编辑
            </a-select-option>
            <a-select-option value="viewer">
              查看者
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model="form.is_active">
            启用用户
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { ref, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import {
  Card as ACard,
  Tag as ATag,
  Space as ASpace,
  Button as AButton,
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Checkbox as ACheckbox,
} from 'ant-design-vue';
import { ydConfirm } from '@/utils/ydModal';
import { usersAPI } from '@/api';

const users = ref<any[]>([]);
const loading = ref(false);
const tablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const showAddModal = ref(false);

const form = ref({
  id: '',
  username: '',
  email: '',
  password: '',
  role: 'editor',
  is_active: true,
});

const isEdit = computed(() => !!form.value.id);

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const tablePagination = computed(() => ({
  current: pagination.value.current,
  pageSize: pagination.value.pageSize,
  total: pagination.value.total,
}));

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.pageSize = p.pageSize;
  void fetchUsers(p.current);
}

const columns = [
  { title: '用户名', key: 'username', width: 150 },
  { title: '邮箱', key: 'email', width: 200 },
  { title: '角色', key: 'role', width: 120 },
  { title: '状态', key: 'is_active', width: 100 },
  { title: '创建时间', key: 'created_at', width: 150 },
  { title: '操作', key: 'actions', width: 180 },
];

function getRoleColor(role: string) {
  if (role === 'admin') return 'red';
  if (role === 'editor') return 'blue';
  if (role === 'viewer') return 'default';
  return 'default';
}

function getRoleText(role: string) {
  if (role === 'admin') return '管理员';
  if (role === 'editor') return '编辑';
  if (role === 'viewer') return '查看者';
  return role;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN');
}

async function fetchUsers(page = 1) {
  loading.value = true;
  pagination.value.current = page;
  try {
    const res = await usersAPI.list({ page, page_size: pagination.value.pageSize });
    users.value = res.data.items || [];
    pagination.value.total = res.data.total || 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch users:', e);
  } finally {
    loading.value = false;
  }
}

function handleEdit(record: any) {
  form.value = {
    id: record.id,
    username: record.username,
    email: record.email || '',
    password: '',
    role: record.role,
    is_active: record.is_active,
  };
  showAddModal.value = true;
}

async function handleToggleActive(record: any) {
  try {
    await usersAPI.update(record.id, { is_active: !record.is_active });
    await fetchUsers();
    AModal.success({ title: '操作成功' });
  } catch (e: any) {
    AModal.error({ title: '操作失败', content: e.message });
  }
}

async function handleSave() {
  if (!form.value.username) {
    AModal.warning({ title: '提示', content: '请填写用户名' });
    return;
  }
  if (!isEdit.value && !form.value.password) {
    AModal.warning({ title: '提示', content: '请填写密码' });
    return;
  }

  try {
    const data = {
      username: form.value.username,
      email: form.value.email,
      role: form.value.role,
      is_active: form.value.is_active,
    };
    if (form.value.password) {
      (data as any).password = form.value.password;
    }

    if (isEdit.value) {
      await usersAPI.update(form.value.id, data);
      AModal.success({ title: '修改成功' });
    } else {
      await usersAPI.create(data);
      AModal.success({ title: '创建成功' });
    }

    showAddModal.value = false;
    form.value = {
      id: '',
      username: '',
      email: '',
      password: '',
      role: 'editor',
      is_active: true,
    };
    await fetchUsers();
  } catch (e: any) {
    AModal.error({ title: '操作失败', content: e.message });
  }
}

function handleDelete(record: any) {
  ydConfirm({
    title: '确认删除',
    content: `确定要删除用户 "${record.username}" 吗？`,
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await usersAPI.delete(record.id);
          await fetchUsers();
          AModal.success({ title: '删除成功' });
        } catch (e: any) {
          AModal.error({ title: '删除失败', content: e.message });
        }
      })();
    },
  });
}

onMounted(async () => {
  try {
    await apiGet('/users');
  } catch {
    /* 空状态 */
  }
  await fetchUsers();
});
</script>
