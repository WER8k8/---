/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
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
 <a-tabs v-model:active-key="activeTab" type="card">
 <a-tab-pane key="roles" tab="角色管理">
 <div class="roles-section">
 <a-table
 :columns="roleColumns"
 :data-source="roles"
 :loading="loading"
 row-key="id"
 size="small"
 :pagination="false"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'name'">
 <div class="role-name-cell">
 <component :is="record.icon" class="role-mini-icon" />
 <span>{{ record.name }}</span>
 </div>
 </template>
 <template v-else-if="column.key === 'actions'">
 <a-space>
 <a-button size="small" @click="selectRole(record as Role)">
 选择
 </a-button>
 <a-popconfirm
 title="确认删除该角色？"
 :disabled="record.is_system"
 @confirm="deleteRole(record as Role)"
 >
 <a-button size="small" danger :disabled="record.is_system">
 删除
 </a-button>
 </a-popconfirm>
 </a-space>
 </template>
 </template>
 </a-table>
 </div>
 </a-tab-pane>
 <a-tab-pane key="menus" tab="菜单权限">
 <div class="menus-section">
 <a-alert
 v-if="!selectedRole"
 type="info"
 show-icon
 message="请先在「角色管理」选择角色后再配置菜单权限"
 style="margin-bottom: 12px"
 />
 <a-tree
 v-else
 :tree-data="menuTree"
 :default-expand-all="true"
 checkable
 :checked-keys="checkedMenuKeys"
 @check="onMenuCheck"
 />
 <div v-if="selectedRole" class="save-bar">
 <a-button type="primary" :loading="saving" @click="saveMenuPermissions">
 保存菜单权限
 </a-button>
 </div>
 </div>
 </a-tab-pane>
 <a-tab-pane key="actions" tab="操作权限">
 <div class="actions-section">
 <a-alert
 v-if="!selectedRole"
 type="info"
 show-icon
 message="请先在「角色管理」选择角色后再配置操作权限"
 style="margin-bottom: 12px"
 />
 <a-table
 :columns="actionColumns"
 :data-source="actions"
 :pagination="false"
 :loading="loading"
 row-key="id"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'permission'">
 <a-switch
 :checked="record.permission"
 :disabled="!selectedRole"
 @change="toggleActionPermission(record as Action)"
 />
 </template>
 </template>
 </a-table>
 <div v-if="selectedRole" class="save-bar">
 <a-button type="primary" :loading="saving" @click="saveActionPermissions">
 保存操作权限
 </a-button>
 </div>
 </div>
 </a-tab-pane>
 </a-tabs>
 </div>

 <a-modal v-model:open="showRoleModal" title="添加角色" :footer="null">
 <a-form :model="roleForm" :rules="roleRules" ref="roleFormRef">
 <a-form-item label="角色名称" name="name">
 <a-input v-model:value="roleForm.name" placeholder="请输入角色名称" />
 </a-form-item>
 <a-form-item label="角色描述" name="description">
 <a-textarea v-model:value="roleForm.description" placeholder="请输入角色描述" :rows="3" />
 </a-form-item>
 <div class="modal-footer">
 <a-button @click="showRoleModal = false">取消</a-button>
 <a-button type="primary" :loading="saving" @click="submitRoleForm">确定</a-button>
 </div>
 </a-form>
 </a-modal>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue';
import { message } from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
 PlusOutlined,
 UserOutlined,
 CrownOutlined,
 FileTextOutlined,
} from '@ant-design/icons-vue';

interface Role {
 id: string;
 name: string;
 description: string;
 icon: any;
 userCount: number;
 is_system: boolean;
 permission_ids: string[];
}

interface Action {
 id: string;
 name: string;
 code: string;
 module: string;
 permission: boolean;
}

interface PermCode {
 id: string;
 code: string;
 name: string;
 group_name: string;
}

interface MenuNode {
 id: string;
 parent_id: string | null;
 title: string;
 path?: string | null;
 permission_code?: string | null;
 children?: MenuNode[];
}

const activeTab = ref('roles');
const showRoleModal = ref(false);
const selectedRole = ref<Role | null>(null);
const loading = ref(false);
const saving = ref(false);

const roleForm = reactive({
 name: '',
 description: '',
});

const roleRules = {
 name: [{ required: true, message: '请输入角色名称' }],
};

const roles = ref<Role[]>([]);
const menuTree = ref<any[]>([]);
const checkedMenuKeys = ref<string[]>([]);
const permCodes = ref<PermCode[]>([]);
const actions = ref<Action[]>([]);

const roleColumns: TableColumnsType<Role> = [
 { title: '角色', dataIndex: 'name', key: 'name' },
 { title: '描述', dataIndex: 'description', key: 'description' },
 { title: '用户数', dataIndex: 'userCount', key: 'userCount', width: 90 },
 { title: '操作', key: 'actions', width: 160 },
];

const actionColumns: TableColumnsType<Action> = [
 { title: '权限名称', dataIndex: 'name', key: 'name' },
 { title: '权限代码', dataIndex: 'code', key: 'code' },
 { title: '所属模块', dataIndex: 'module', key: 'module' },
 { title: '权限状态', key: 'permission' },
];

function pickRoleIcon(name: string, isSystem: boolean) {
 if (isSystem || /超|admin/i.test(name)) return CrownOutlined;
 if (/管理|manager/i.test(name)) return UserOutlined;
 return FileTextOutlined;
}

function mapRole(raw: any): Role {
 return {
 id: String(raw.id),
 name: raw.name ?? '',
 description: raw.description ?? '',
 icon: pickRoleIcon(raw.name ?? '', !!raw.is_system),
 userCount: raw.user_count ?? 0,
 is_system: !!raw.is_system,
 permission_ids: Array.isArray(raw.permission_ids) ? raw.permission_ids.map(String) : [],
 };
}

function buildMenuTree(menus: MenuNode[]): any[] {
 const byId = new Map<string, any>();
 const roots: any[] = [];
 for (const m of menus) {
 byId.set(m.id, {
 key: m.id,
 title: m.title,
 permission_code: m.permission_code,
 children: [],
 });
 }
 for (const m of menus) {
 const node = byId.get(m.id);
 if (m.parent_id && byId.has(m.parent_id)) {
 byId.get(m.parent_id).children.push(node);
 } else {
 roots.push(node);
 }
 }
 const prune = (nodes: any[]): any[] =>
 nodes.map((n) => ({ ...n, children: n.children?.length ? prune(n.children) : undefined }));
 return prune(roots);
}

async function loadRoles() {
 loading.value = true;
 try {
 const res = await apiGet<any>('/super-admin/permissions/roles');
 const list = Array.isArray(res) ? res : res?.data ?? res?.items ?? [];
 roles.value = list.map(mapRole);
 const currentId = selectedRole.value?.id;
 if (currentId) {
 selectedRole.value = roles.value.find((r) => r.id === currentId) ?? null;
 if (selectedRole.value) applyRoleSelection(selectedRole.value);
 }
 } catch (e: any) {
 message.error(e?.message || '角色列表加载失败');
 } finally {
 loading.value = false;
 }
}

async function loadPermCodes() {
 try {
 const res = await apiGet<any>('/super-admin/permissions/codes');
 const list = Array.isArray(res) ? res : res?.data ?? [];
 permCodes.value = list.map((p: any) => ({
 id: String(p.id),
 code: p.code,
 name: p.name,
 group_name: p.group_name || '未分组',
 }));
 } catch {
 permCodes.value = [];
 }
}

async function loadMenus() {
 try {
 const res = await apiGet<any>('/super-admin/permissions/menus/all');
 const list = Array.isArray(res) ? res : res?.data ?? [];
 menuTree.value = buildMenuTree(list);
 } catch {
 menuTree.value = [];
 }
}

function applyRoleSelection(role: Role) {
 const idSet = new Set(role.permission_ids);
 actions.value = permCodes.value.map((p) => ({
 id: p.id,
 name: p.name,
 code: p.code,
 module: p.group_name,
 permission: idSet.has(p.id),
 }));
 const checked: string[] = [];
 const walk = (nodes: any[]) => {
 for (const n of nodes) {
 if (n.permission_code) {
 const hit = permCodes.value.find((p) => p.code === n.permission_code);
 if (hit && idSet.has(hit.id)) checked.push(n.key);
 }
 if (n.children?.length) walk(n.children);
 }
 };
 walk(menuTree.value);
 checkedMenuKeys.value = checked;
}

const selectRole = (role: Role) => {
 selectedRole.value = role;
 applyRoleSelection(role);
 activeTab.value = 'actions';
};

const onMenuCheck = (checked: unknown) => {
 const keys = Array.isArray(checked)
 ? (checked as unknown[])
 : (checked as { checked: unknown[] }).checked;
 checkedMenuKeys.value = keys.map((k) => String(k));
};

const toggleActionPermission = (record: Action) => {
 record.permission = !record.permission;
};

async function collectPermissionIds(): Promise<string[]> {
 const ids = new Set<string>();
 for (const a of actions.value) {
 if (a.permission) ids.add(a.id);
 }
 const walk = (nodes: any[]) => {
 for (const n of nodes) {
 if (n.permission_code && checkedMenuKeys.value.includes(String(n.key))) {
 const hit = permCodes.value.find((p) => p.code === n.permission_code);
 if (hit) ids.add(hit.id);
 }
 if (n.children?.length) walk(n.children);
 }
 };
 walk(menuTree.value);
 return [...ids];
}

async function persistRolePermissions(msg: string) {
 if (!selectedRole.value) return;
 saving.value = true;
 try {
 const permission_ids = await collectPermissionIds();
 await apiPut(`/super-admin/permissions/roles/${selectedRole.value.id}`, {
 name: selectedRole.value.name,
 description: selectedRole.value.description,
 permission_ids,
 });
 selectedRole.value.permission_ids = permission_ids;
 message.success(msg);
 await loadRoles();
 } catch (e: any) {
 message.error(e?.message || '权限保存失败');
 } finally {
 saving.value = false;
 }
}

const saveMenuPermissions = () => persistRolePermissions('菜单权限已保存');
const saveActionPermissions = () => persistRolePermissions('操作权限已保存');

const submitRoleForm = async () => {
 if (!roleForm.name.trim()) {
 message.warning('请输入角色名称');
 return;
 }
 saving.value = true;
 try {
 await apiPost('/super-admin/permissions/roles', {
 name: roleForm.name.trim(),
 description: roleForm.description,
 permission_ids: [],
 });
 message.success('角色创建成功');
 showRoleModal.value = false;
 roleForm.name = '';
 roleForm.description = '';
 await loadRoles();
 } catch (e: any) {
 message.error(e?.message || '角色创建失败');
 } finally {
 saving.value = false;
 }
};

async function deleteRole(record: Role) {
 try {
 await apiDelete(`/super-admin/permissions/roles/${record.id}`);
 message.success('角色已删除');
 if (selectedRole.value?.id === record.id) selectedRole.value = null;
 await loadRoles();
 } catch (e: any) {
 message.error(e?.message || '角色删除失败');
 }
}

onMounted(async () => {
 await Promise.all([loadPermCodes(), loadMenus()]);
 await loadRoles();
});
</script>

<style scoped lang="scss">
.permissions-page {
 padding: 24px;
}

.tabs-container {
 background: #fff;
 border-radius: 12px;
 box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.roles-section {
 padding: 16px;
}

.role-name-cell {
 display: flex;
 align-items: center;
 gap: 8px;

 .role-mini-icon {
 color: #4a9b8c;
 }
}

.menus-section,
.actions-section {
 padding: 24px;
}

.save-bar {
 margin-top: 16px;
 display: flex;
 justify-content: flex-end;
}

.modal-footer {
 display: flex;
 justify-content: flex-end;
 gap: 12px;
 margin-top: 24px;
}
</style>
