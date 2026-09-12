<template>
  <YdPage title="权限管理" subtitle="配置角色权限、菜单权限和操作权限" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showRoleModal = true">
        <PlusOutlined />
        添加角色
      </a-button>
    </template>
  <div class="permissions-page">
    <div class="tabs-container">
      <a-tabs
        v-model:active-key="activeTab"
        type="card"
      >
        <a-tab-pane
          key="roles"
          tab="角色管理"
        >
          <div class="roles-section">
            <div class="roles-list">
              <div
                class="role-card"
                v-for="role in roles"
                :key="role.id"
                :class="{ active: selectedRole?.id === role.id }"
                @click="selectRole(role)"
              >
                <div class="role-icon">
                  <component :is="role.icon" />
                </div>
                <div class="role-info">
                  <h3 class="role-name">
                    {{ role.name }}
                  </h3>
                  <p class="role-desc">
                    {{ role.description }}
                  </p>
                </div>
                <div class="role-users">
                  {{ role.userCount }} 用户
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>
        <a-tab-pane
          key="menus"
          tab="菜单权限"
        >
          <div class="menus-section">
            <a-tree
              :tree-data="menuTree"
              :default-expand-all="true"
              show-checkbox
              :checked-keys="checkedMenuKeys"
              @check="onMenuCheck"
            />
          </div>
        </a-tab-pane>
        <a-tab-pane
          key="actions"
          tab="操作权限"
        >
          <div class="actions-section">
            <a-table
              :columns="actionColumns"
              :data-source="actions"
              :pagination="false"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'permission'">
                  <a-switch
                    :checked="record.permission"
                    @change="toggleActionPermission(record)"
                  />
                </template>
              </template>
            </a-table>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <a-modal
      v-model:open="showRoleModal"
      title="添加角色"
      :footer="null"
    >
      <a-form
        :model="roleForm"
        :rules="roleRules"
        ref="roleFormRef"
      >
        <a-form-item
          label="角色名称"
          name="name"
        >
          <a-input
            v-model:value="roleForm.name"
            placeholder="请输入角色名称"
          />
        </a-form-item>
        <a-form-item
          label="角色描述"
          name="description"
        >
          <a-textarea
            v-model:value="roleForm.description"
            placeholder="请输入角色描述"
            :rows="3"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showRoleModal = false">
            取消
          </a-button>
          <a-button
            type="primary"
            @click="submitRoleForm"
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
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
  LockOutlined,
  PlusOutlined,
  UserOutlined,
  CrownOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';
interface Role {
  id: number;
  name: string;
  description: string;
  icon: any;
  userCount: number;
}

interface Action {
  id: number;
  name: string;
  code: string;
  module: string;
  permission: boolean;
}

const activeTab = ref('roles');
const showRoleModal = ref(false);
const selectedRole = ref<Role | null>(null);

const roleForm = reactive({
  name: '',
  description: '',
});

const roleRules = {
  name: [{ required: true, message: '请输入角色名称' }],
};

const roles = ref<Role[]>([
  { id: 1, name: '超级管理员', description: '拥有系统全部权限', icon: CrownOutlined, userCount: 2 },
  { id: 2, name: '管理员', description: '拥有大部分管理权限', icon: UserOutlined, userCount: 5 },
  { id: 3, name: '普通用户', description: '基础操作权限', icon: FileTextOutlined, userCount: 1230 },
]);

const menuTree = ref<any[]>([]);

const checkedMenuKeys = ref<any[]>([]);

const actionColumns: TableColumnsType<Action> = [
  { title: '权限名称', dataIndex: 'name', key: 'name' },
  { title: '权限代码', dataIndex: 'code', key: 'code' },
  { title: '所属模块', dataIndex: 'module', key: 'module' },
  { title: '权限状态', key: 'permission' },
];

const actions = ref<Action[]>([
  { id: 1, name: '用户管理', code: 'user.manage', module: '系统管理', permission: true },
  { id: 2, name: '权限管理', code: 'permission.manage', module: '系统管理', permission: true },
  { id: 3, name: '系统配置', code: 'config.manage', module: '系统管理', permission: false },
  { id: 4, name: 'AI模型管理', code: 'ai.model.manage', module: 'AI引擎', permission: true },
  { id: 5, name: '代码生成', code: 'code.generate', module: '代码工具', permission: true },
]);

const selectRole = (role: Role) => {
  selectedRole.value = role;
};

const onMenuCheck = (checked: unknown) => {
  const keys = Array.isArray(checked)
    ? (checked as unknown[])
    : (checked as { checked: unknown[] }).checked;
  checkedMenuKeys.value = keys.map((k) => String(k));
};

const toggleActionPermission = (record: any) => {
  record.permission = !record.permission;
};

const submitRoleForm = () => {
  showRoleModal.value = false;
  roles.value.push({
    id: Date.now(),
    name: roleForm.name,
    description: roleForm.description,
    icon: UserOutlined,
    userCount: 0,
  });
  roleForm.name = '';
  roleForm.description = '';
};

onMounted(async () => {
  try { await apiGet('/users'); } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.permissions-page {
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

.tabs-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.roles-section {
  padding: 24px;

  .roles-header {
    margin-bottom: 20px;

    .add-role-btn {
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
    }
  }

  .roles-list {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;

    .role-card {
      padding: 20px;
      border-radius: 12px;
      border: 2px solid #f3f4f6;
      cursor: pointer;
      transition: all 0.2s;

      &:hover,
      &.active {
        border-color: #4a9b8c;
        background: #f9fafb;
      }

      .role-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: #fff;
        margin-bottom: 12px;
      }

      .role-info {
        .role-name {
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
          margin-bottom: 4px;
        }

        .role-desc {
          font-size: 13px;
          color: #6b7280;
          margin: 0;
        }
      }

      .role-users {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 8px;
      }
    }
  }
}

.menus-section {
  padding: 24px;
}

.actions-section {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1024px) {
  .roles-list {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
