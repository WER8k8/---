/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="user-address-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          地址管理
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          管理您的收货地址，用于外贸物流配送
        </p>
      </div>
    </section>

    <!-- Address List -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-3xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6 sm:mb-8">
          <h2 class="text-xl sm:text-2xl font-bold text-text-primary">
            我的地址
          </h2>
          <button
            @click="openAddDialog"
            class="btn-primary text-sm sm:text-base"
          >
            <svg
              class="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            添加地址
          </button>
        </div>

        <!-- Loading State -->
        <div
          v-if="loading"
          class="space-y-4"
        >
          <div
            v-for="i in 3"
            :key="i"
            class="animate-pulse bg-surface rounded-2xl p-6"
          >
            <div class="h-6 bg-gray-200 rounded w-1/4 mb-4" />
            <div class="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div class="h-4 bg-gray-200 rounded w-3/4" />
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="addresses.length === 0"
          class="text-center py-10 sm:py-16"
        >
          <svg
            class="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-text-secondary mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">
            暂无地址
          </h3>
          <p class="text-sm text-text-secondary mb-6">
            您还没有添加收货地址，请点击上方按钮添加
          </p>
        </div>

        <!-- Address Cards -->
        <div
          v-else
          class="space-y-4"
        >
          <div
            v-for="addr in addresses"
            :key="addr.id"
            :class="[
              'bg-surface rounded-2xl shadow-card p-6 sm:p-8 hover:shadow-card-hover transition-all duration-300',
              addr.is_default ? 'border-2 border-primary' : 'border-2 border-transparent'
            ]"
          >
            <div class="flex flex-col sm:flex-row sm:items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <h3 class="text-lg font-semibold text-text-primary">
                    {{ addr.recipient_name }}
                  </h3>
                  <span class="text-sm text-text-secondary">{{ addr.phone }}</span>
                  <span
                    v-if="addr.is_default"
                    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary"
                  >
                    默认地址
                  </span>
                </div>
                <p class="text-sm text-text-secondary mb-1">
                  {{ addr.country }} {{ addr.province }} {{ addr.city }} {{ addr.district }}
                </p>
                <p class="text-sm text-text-secondary">
                  {{ addr.street_address }}
                </p>
                <p
                  v-if="addr.postal_code"
                  class="text-sm text-text-secondary mt-1"
                >
                  邮编: {{ addr.postal_code }}
                </p>
              </div>

              <div class="flex items-center gap-2 mt-4 sm:mt-0 sm:ml-4">
                <button
                  v-if="!addr.is_default"
                  @click="setDefault(addr.id)"
                  class="p-2 text-text-secondary hover:text-primary transition-colors"
                  title="设为默认"
                >
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </button>
                <button
                  @click="openEditDialog(addr)"
                  class="p-2 text-text-secondary hover:text-blue-600 transition-colors"
                  title="编辑"
                >
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </button>
                <button
                  @click="deleteAddress(addr.id)"
                  class="p-2 text-text-secondary hover:text-red-600 transition-colors"
                  title="删除"
                >
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Add/Edit Address Dialog -->
    <div
      v-if="showDialog"
      class="fixed inset-0 z-50 overflow-y-auto"
    >
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          class="fixed inset-0 transition-opacity"
          @click="closeDialog"
        >
          <div class="absolute inset-0 bg-gray-500 opacity-75" />
        </div>

        <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <h3 class="text-lg font-bold text-text-primary mb-4">
              {{ isEditing ? '编辑地址' : '添加地址' }}
            </h3>
            <form
              @submit.prevent="saveAddress"
              class="space-y-4"
            >
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">收件人姓名</label>
                <input
                  v-model="addressForm.recipient_name"
                  type="text"
                  required
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="请输入收件人姓名"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">联系电话</label>
                <input
                  v-model="addressForm.phone"
                  type="tel"
                  required
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="请输入联系电话"
                >
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">国家</label>
                  <input
                    v-model="addressForm.country"
                    type="text"
                    required
                    class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="如：中国"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">省份/州</label>
                  <input
                    v-model="addressForm.province"
                    type="text"
                    required
                    class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="如：广东省"
                  >
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">城市</label>
                  <input
                    v-model="addressForm.city"
                    type="text"
                    required
                    class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="如：深圳市"
                  >
                </div>
                <div>
                  <label class="block text-sm font-medium text-text-primary mb-1">区/县</label>
                  <input
                    v-model="addressForm.district"
                    type="text"
                    class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="如：南山区"
                  >
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">详细地址</label>
                <textarea
                  v-model="addressForm.street_address"
                  required
                  rows="2"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                  placeholder="请输入详细地址"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-1">邮政编码</label>
                <input
                  v-model="addressForm.postal_code"
                  type="text"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="请输入邮政编码"
                >
              </div>
              <div class="flex items-center">
                <input
                  v-model="addressForm.is_default"
                  type="checkbox"
                  class="w-4 h-4 text-primary focus:ring-primary/20 rounded"
                >
                <label class="ml-2 text-sm text-text-primary">设为默认地址</label>
              </div>
            </form>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="saveAddress"
              :disabled="saving"
              class="btn-primary w-full sm:w-auto sm:ml-3"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button
              @click="closeDialog"
              class="mt-3 sm:mt-0 w-full sm:w-auto btn-outline"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const addresses = ref<any[]>([]);
const loading = ref(true);
const showDialog = ref(false);
const isEditing = ref(false);
const saving = ref(false);
const editingId = ref('');

const addressForm = ref({
  recipient_name: '',
  phone: '',
  country: '',
  province: '',
  city: '',
  district: '',
  street_address: '',
  postal_code: '',
  is_default: false,
});

// 获取地址列表
const fetchAddresses = async () => {
  loading.value = true;
  try {
    const response = await fetch(useApiV1Url('/addresses'), {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      addresses.value = data.items || data || [];
    }
  } catch (err) {
    console.error('Failed to fetch addresses:', err);
  } finally {
    loading.value = false;
  }
};

// 打开添加对话框
const openAddDialog = () => {
  isEditing.value = false;
  editingId.value = '';
  addressForm.value = {
    recipient_name: '',
    phone: '',
    country: '',
    province: '',
    city: '',
    district: '',
    street_address: '',
    postal_code: '',
    is_default: false,
  };
  showDialog.value = true;
};

// 打开编辑对话框
const openEditDialog = (addr: any) => {
  isEditing.value = true;
  editingId.value = addr.id;
  addressForm.value = { ...addr };
  showDialog.value = true;
};

// 关闭对话框
const closeDialog = () => {
  showDialog.value = false;
};

// 保存地址
const saveAddress = async () => {
  saving.value = true;
  try {
    const url = isEditing.value
      ? useApiV1Url(`/addresses/${editingId.value}`)
      : useApiV1Url('/addresses');
    const method = isEditing.value ? 'PATCH' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(addressForm.value),
    });

    if (response.ok) {
      showDialog.value = false;
      await fetchAddresses();
    }
  } catch (err) {
    console.error('Failed to save address:', err);
  } finally {
    saving.value = false;
  }
};

// 设为默认地址
const setDefault = async (addressId: string) => {
  try {
    const response = await fetch(useApiV1Url(`/addresses/${addressId}/set-default`), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      await fetchAddresses();
    }
  } catch (err) {
    console.error('Failed to set default address:', err);
  }
};

// 删除地址
const deleteAddress = async (addressId: string) => {
  if (!confirm('确定要删除这个地址吗？')) return;

  try {
    const response = await fetch(useApiV1Url(`/addresses/${addressId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      await fetchAddresses();
    }
  } catch (err) {
    console.error('Failed to delete address:', err);
  }
};

// SEO元数据
useHead({
  title: '地址管理 - 建材B2B外贸平台',
  meta: [
    { name: 'description', content: '管理您的收货地址，用于外贸物流配送' },
  ],
});

onMounted(() => {
  fetchAddresses();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-4 py-2.5 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-outline {
  @apply inline-flex items-center justify-center px-4 py-2.5 border-2 border-gray-300 text-text-secondary font-medium rounded-lg hover:bg-gray-50 transition-all duration-300;
}
</style>
