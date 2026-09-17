/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="用户管理" subtitle="管理系统用户、角色和权限分配" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAddModal = true">
        <PlusOutlined />
        添加用户
      </a-button>
    </template>
  <div class="users-page">
    <div class="search-bar">
      <a-input
        v-model:value="searchKeyword"
        placeholder="搜索用户名或邮箱"
        class="search-input"
        :prefix-icon="SearchOutlined"
      />
      <a-select
        v-model:value="roleFilter"
        placeholder="筛选角色"
        class="role-select"
      >
        <a-select-option value="">
          全部角色
        </a-select-option>
        <a-select-option value="admin">
          管理员
        </a-select-option>
        <a-select-option value="user">
          普通用户
        </a-select-option>
      </a-select>
      <button
        class="search-btn"
        @click="handleSearch"
      >
        <SearchOutlined />
        搜索
      </button>
    </div>

    <div class="table-container">
      <a-table
        :columns="columns"
        :data-source="users"
        :pagination="pagination"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.is_active ? 'success' : 'warning'"
              :text="record.is_active ? '启用' : '禁用'"
            />
          </template>
          <template v-else-if="column.key === 'role'">
            <a-tag :color="record.role === 'admin' ? 'red' : 'blue'">
              {{
                record.role === 'admin' ? '管理员' : '普通用户'
              }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                size="small"
                @click="editUser(record)"
              >
                编辑
              </a-button>
              <a-button
                size="small"
                @click="toggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>
              <a-button
                size="small"
                danger
                @click="deleteUser(record)"
              >
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="showAddModal"
      title="添加用户"
      :footer="null"
    >
      <a-form
        :model="formData"
        :rules="formRules"
        ref="formRef"
      >
        <a-form-item
          label="用户名"
          name="username"
        >
          <a-input
            v-model:value="formData.username"
            placeholder="请输入用户名"
          />
        </a-form-item>
        <a-form-item
          label="邮箱"
          name="email"
        >
          <a-input
            v-model:value="formData.email"
            placeholder="请输入邮箱"
          />
        </a-form-item>
        <a-form-item
          label="密码"
          name="password"
        >
          <a-input-password
            v-model:value="formData.password"
            placeholder="请输入密码"
          />
        </a-form-item>
        <a-form-item
          label="角色"
          name="role"
        >
          <a-select v-model:value="formData.role">
            <a-select-option value="admin">
              管理员
            </a-select-option>
            <a-select-option value="user">
              普通用户
            </a-select-option>
          </a-select>
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showAddModal = false">
            取消
          </a-button>
          <a-button
            type="primary"
            @click="submitForm"
          >
            确定
          </a-button>
        </div>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { UserOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';
import type { Rule } from 'ant-design-vue/es/form';
import { usersAPI } from '@/api';

interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

const searchKeyword = ref('');
const roleFilter = ref('');
const showAddModal = ref(false);
const showEditModal = ref(false);
const formRef = ref();
const loading = ref(false);
const currentEditUser = ref<User | null>(null);

const formData = reactive({
  username: '',
  email: '',
  password: '',
  display_name: '',
  role: 'user',
});

const formRules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名' }],
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email' as const, message: '请输入有效的邮箱' },
  ],
  password: [{ required: true, message: '请输入密码' }],
};

const columns: TableColumnsType<User> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 120, ellipsis: true },
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '显示名', dataIndex: 'display_name', key: 'display_name' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '角色', dataIndex: 'role', key: 'role' },
  { title: '状态', dataIndex: 'is_active', key: 'status' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'actions', width: 220 },
];

const users = ref<User[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
  onChange: (page: number, size: number) => {
    currentPage.value = page;
    pageSize.value = size;
    fetchUsers();
  },
});

async function fetchUsers() {
  loading.value = true;
  try {
    const res = await usersAPI.list({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      role: roleFilter.value || undefined,
    });
    const data = res.data as any;
    const items = data?.items || data || [];
    users.value = Array.isArray(items) ? items : [];
    total.value = data?.total || items.length;
    pagination.value.total = total.value;
    pagination.value.current = currentPage.value;
  } catch (err: any) {
    message.error('获取用户列表失败: ' + (err?.message || '未知错误'));
  } finally {
    loading.value = false;
  }
}

const handleSearch = () => {
  currentPage.value = 1;
  fetchUsers();
};

const editUser = (record: any) => {
  currentEditUser.value = record;
  formData.username = record.username;
  formData.email = record.email || '';
  formData.display_name = record.display_name || '';
  formData.role = record.role;
  formData.password = '';
  showEditModal.value = true;
};

async function toggleStatus(record: any) {
  try {
    const u = record as User;
    const newStatus = !u.is_active;
    await usersAPI.update(u.id, { is_active: newStatus });
    record.is_active = newStatus;
    message.success(newStatus ? '用户已启用' : '用户已禁用');
  } catch (err: any) {
    message.error('状态更新失败: ' + (err?.message || '未知错误'));
  }
}

async function deleteUser(record: any) {
  try {
    await usersAPI.delete((record as User).id);
    message.success('用户已删除');
    fetchUsers();
  } catch (err: any) {
    message.error('删除失败: ' + (err?.message || '未知错误'));
  }
}

async function submitForm() {
  try {
    if (showEditModal.value && currentEditUser.value) {
      const updateData: any = {
        username: formData.username,
        email: formData.email,
        display_name: formData.display_name,
        role: formData.role,
      };
      if (formData.password) {
        updateData.password = formData.password;
      }
      await usersAPI.update(currentEditUser.value.id, updateData);
      message.success('用户更新成功');
      showEditModal.value = false;
    } else {
      await usersAPI.create({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        display_name: formData.display_name,
        role: formData.role,
      });
      message.success('用户创建成功');
      showAddModal.value = false;
    }
    resetForm();
    fetchUsers();
  } catch (err: any) {
    message.error('操作失败: ' + (err?.message || '未知错误'));
  }
}

function resetForm() {
  formData.username = '';
  formData.email = '';
  formData.password = '';
  formData.display_name = '';
  formData.role = 'user';
  currentEditUser.value = null;
}

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped lang="scss">
.users-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
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

  .add-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-2px);
    }
  }
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;

  .search-input {
    width: 300px;
  }

  .role-select {
    width: 150px;
  }

  .search-btn {
    padding: 0 20px;
  }
}

.table-container {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
