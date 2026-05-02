<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-900">
        用户管理
      </h1>
      <button
        class="px-4 py-2 bg-brand-blue text-white rounded hover:bg-blue-700 transition-colors text-sm"
        @click="openCreate"
      >
        + 新建用户
      </button>
    </div>

    <div
      v-if="loading"
      class="text-center py-12 text-gray-500"
    >
      加载中...
    </div>
    <div
      v-else-if="error"
      class="text-center py-12 text-red-500"
    >
      {{ error }}
    </div>

    <div
      v-else
      class="bg-white rounded-xl shadow-sm overflow-hidden"
    >
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-200">
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">
              用户名
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">
              姓名
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">
              角色
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">
              状态
            </th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            class="border-b border-gray-100 hover:bg-gray-50"
          >
            <td class="px-4 py-3 text-sm font-medium text-gray-900">
              {{ user.username }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">
              {{ user.display_name || '-' }}
            </td>
            <td class="px-4 py-3">
              <span
                class="text-xs px-2 py-1 rounded"
                :class="roleBadge(user.role)"
              >{{ user.role_label }}</span>
            </td>
            <td class="px-4 py-3">
              <button
                class="text-xs px-2 py-1 rounded"
                :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                @click="toggleStatus(user)"
              >
                {{ user.is_active ? '启用' : '禁用' }}
              </button>
            </td>
            <td class="px-4 py-3">
              <button
                class="text-sm text-brand-blue hover:underline mr-3"
                @click="openEdit(user)"
              >
                编辑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showModal=false"
    >
      <div class="bg-white rounded-lg w-full max-w-md p-6">
        <h2 class="text-lg font-bold mb-4">
          {{ isEdit ? '编辑用户' : '新建用户' }}
        </h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              v-model="form.username"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded"
              :disabled="isEdit"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              class="w-full px-3 py-2 border border-gray-300 rounded"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
            <input
              v-model="form.display_name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <select
              v-model="form.role"
              class="w-full px-3 py-2 border border-gray-300 rounded"
            >
              <option
                v-for="r in roles"
                :key="r.value"
                :value="r.value"
              >
                {{ r.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ isEdit ? '新密码（留空不修改）' : '密码' }}</label>
            <input
              v-model="form.password"
              type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded"
              :placeholder="isEdit ? '留空不修改' : ''"
            >
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
            @click="showModal=false"
          >
            取消
          </button>
          <button
            class="px-4 py-2 bg-brand-blue text-white rounded hover:bg-blue-700"
            @click="saveUser"
          >
            {{ isEdit ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({ layout: "admin" });

interface UserItem {
  id: string; username: string; email: string; display_name: string | null;
  role: string; role_label: string; is_active: boolean;
}

const users = ref<UserItem[]>([]);
const loading = ref(false);
const error = ref("");
const showModal = ref(false);
const isEdit = ref(false);
const editingId = ref("");
const roles = ref<{value: string; label: string}[]>([]);
const form = ref({ username: "", email: "", display_name: "", role: "editor", password: "" });

function roleBadge(r: string) {
  const m: Record<string, string> = { admin: "bg-primary/10 text-primary", editor: "bg-secondary/10 text-secondary", sales: "bg-accent/10 text-accent", viewer: "bg-surface-hover text-text-muted" };
  return m[r] || "bg-surface-hover text-text-muted";
}

async function loadUsers() {
  loading.value = true; error.value = "";
  try {
    users.value = await $fetch("/api/v1/users");
  } catch (e: any) { error.value = e?.data?.detail || "加载失败"; }
  finally { loading.value = false; }
}

async function loadRoles() {
  roles.value = await $fetch("/api/v1/roles");
}

function openCreate() { isEdit.value = false; editingId.value = ""; form.value = { username: "", email: "", display_name: "", role: "editor", password: "" }; showModal.value = true; }
function openEdit(u: UserItem) { isEdit.value = true; editingId.value = u.id; form.value = { username: u.username, email: u.email, display_name: u.display_name || "", role: u.role, password: "" }; showModal.value = true; }

async function saveUser() {
  try {
    if (isEdit.value) {
      await $fetch(`/api/v1/users/${editingId.value}`, { method: "PUT", body: { email: form.value.email, display_name: form.value.display_name, role: form.value.role, password: form.value.password || undefined } });
    } else {
      await $fetch("/api/v1/users", { method: "POST", body: form.value });
    }
    showModal.value = false;
    await loadUsers();
  } catch (e: any) { alert(e?.data?.detail || "保存失败"); }
}

async function toggleStatus(u: UserItem) {
  try {
    await $fetch(`/api/v1/users/${u.id}`, { method: "PUT", body: { is_active: !u.is_active } });
    await loadUsers();
  } catch (e: any) { alert(e?.data?.detail || "更新失败"); }
}

onMounted(() => { loadUsers(); loadRoles(); });
</script>
