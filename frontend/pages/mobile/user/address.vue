/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <template #default>
        <h1 class="text-base font-semibold text-gray-900">{{ t('mobile.user.address') }}</h1>
      </template>
      <template #right>
        <button
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="openAddForm"
        >
          <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </template>
    </MobileNavbar>

    <!-- Loading State -->
    <div v-if="loading" class="px-4 py-4 space-y-3">
      <div v-for="i in 3" :key="i" class="bg-white rounded-2xl p-4 animate-pulse">
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center">
        <div class="text-6xl mb-4">😞</div>
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ t('mobile.address.loadFailed') }}
        </h2>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <button class="mobile-btn-primary inline-block px-6 py-3 rounded-full" @click="fetchAddresses">
          {{ t('mobile.address.retry') }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="addresses.length === 0" class="px-4 py-20 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">{{ t('mobile.address.noAddress') }}</h3>
      <p class="text-sm text-gray-500 mb-6">{{ t('mobile.address.noAddressDesc') }}</p>
      <button class="mobile-btn-primary px-6 py-3 rounded-full" @click="openAddForm">
        {{ t('mobile.address.add') }}
      </button>
    </div>

    <!-- Address List -->
    <div v-else class="px-4 py-2 space-y-3 pb-20">
      <div
        v-for="addr in addresses"
        :key="addr.id"
        :class="[
          'bg-white rounded-2xl p-4 relative',
          addr.is_default ? 'border-2 border-blue-500' : 'border-2 border-transparent'
        ]"
      >
        <!-- Default Badge -->
        <div v-if="addr.is_default" class="absolute top-3 right-3 px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded-full">
          {{ t('mobile.address.default') }}
        </div>

        <!-- Address Info -->
        <div class="pr-16">
          <h3 class="text-sm font-semibold text-gray-900">{{ addr.recipient_name }}</h3>
          <p class="text-sm text-gray-600 mt-1">{{ addr.phone }}</p>
          <p class="text-xs text-gray-500 mt-1">
            {{ addr.country }} {{ addr.province }} {{ addr.city }} {{ addr.district }}
          </p>
          <p class="text-xs text-gray-500">{{ addr.street_address }}</p>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
          <button
            v-if="!addr.is_default"
            @click="setDefault(addr.id)"
            class="flex-1 text-center text-sm text-blue-600 py-2"
          >
            {{ t('mobile.address.setDefault') }}
          </button>
          <button
            @click="openEditForm(addr)"
            class="flex-1 text-center text-sm text-gray-500 py-2"
          >
            {{ t('mobile.common.edit') }}
          </button>
          <button
            @click="deleteAddress(addr.id)"
            class="flex-1 text-center text-sm text-red-500 py-2"
          >
            {{ t('mobile.common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Address Form Modal -->
    <div v-if="showForm" class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-end justify-center">
      <div class="bg-white w-full max-h-[90vh] rounded-t-2xl overflow-y-auto">
        <div class="p-5">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold text-gray-900">{{ isEditing ? t('mobile.address.edit') : t('mobile.address.add') }}</h2>
            <button @click="showForm = false" class="p-1">
              <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form @submit.prevent="saveAddress" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.recipient') }}</label>
              <input
                v-model="form.recipient_name"
                type="text"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :placeholder="t('mobile.address.recipientPlaceholder')"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.phone') }}</label>
              <input
                v-model="form.phone"
                type="tel"
                required
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :placeholder="t('mobile.address.phonePlaceholder')"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.country') }}</label>
                <input
                  v-model="form.country"
                  type="text"
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="中国"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.province') }}</label>
                <input
                  v-model="form.province"
                  type="text"
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  :placeholder="t('mobile.address.provincePlaceholder')"
                />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.city') }}</label>
                <input
                  v-model="form.city"
                  type="text"
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  :placeholder="t('mobile.address.cityPlaceholder')"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.district') }}</label>
                <input
                  v-model="form.district"
                  type="text"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  :placeholder="t('mobile.address.districtPlaceholder')"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.street') }}</label>
              <textarea
                v-model="form.street_address"
                required
                rows="2"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                :placeholder="t('mobile.address.streetPlaceholder')"
              ></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('mobile.address.postalCode') }}</label>
              <input
                v-model="form.postal_code"
                type="text"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                :placeholder="t('mobile.address.postalCodePlaceholder')"
              />
            </div>
            <div class="flex items-center">
              <input
                v-model="form.is_default"
                type="checkbox"
                class="w-5 h-5 text-blue-600 rounded"
              />
              <label class="ml-2 text-sm text-gray-700">{{ t('mobile.address.setDefault') }}</label>
            </div>

            <!-- Submit Button -->
            <div class="flex gap-3 pt-4">
              <button
                type="submit"
                :disabled="saving"
                class="flex-1 mobile-btn-primary py-3.5 rounded-xl font-semibold"
              >
                {{ saving ? t('mobile.common.saving') : t('mobile.common.save') }}
              </button>
              <button
                type="button"
                @click="showForm = false"
                class="flex-1 mobile-btn-outline py-3.5 rounded-xl font-semibold"
              >
                {{ t('mobile.common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const router = useRouter();
const { t } = useI18n();

const addresses = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showForm = ref(false);
const isEditing = ref(false);
const saving = ref(false);
const editingId = ref('');

const form = ref({
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

// Fetch addresses
const fetchAddresses = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch('/api/v1/addresses', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      addresses.value = data.items || data || [];
    } else {
      throw new Error(`Failed to fetch: ${response.status}`);
    }
  } catch (err: any) {
    error.value = err.message || t('mobile.address.loadFailed');
    console.error('Failed to fetch addresses:', err);
  } finally {
    loading.value = false;
  }
};

// Open add form
const openAddForm = () => {
  isEditing.value = false;
  editingId.value = '';
  form.value = {
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
  showForm.value = true;
};

// Open edit form
const openEditForm = (addr: any) => {
  isEditing.value = true;
  editingId.value = addr.id;
  form.value = { ...addr };
  showForm.value = true;
};

// Save address
const saveAddress = async () => {
  saving.value = true;
  try {
    const url = isEditing.value
      ? `/api/v1/addresses/${editingId.value}`
      : '/api/v1/addresses';
    const method = isEditing.value ? 'PATCH' : 'POST';
    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(form.value),
    });
    if (response.ok) {
      showForm.value = false;
      await fetchAddresses();
    } else {
      throw new Error(`Failed to save: ${response.status}`);
    }
  } catch (err: any) {
    alert(err.message || t('mobile.address.saveFailed'));
    console.error('Failed to save address:', err);
  } finally {
    saving.value = false;
  }
};

// Set default
const setDefault = async (id: string) => {
  try {
    await fetch(`/api/v1/addresses/${id}/set-default`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    await fetchAddresses();
  } catch (err) {
    console.error('Failed to set default:', err);
  }
};

// Delete address
const deleteAddress = async (id: string) => {
  if (!confirm(t('mobile.address.confirmDelete'))) return;
  try {
    await fetch(`/api/v1/addresses/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    await fetchAddresses();
  } catch (err) {
    console.error('Failed to delete address:', err);
  }
};

// Page meta
useHead({
  title: t('mobile.user.address'),
});

onMounted(() => {
  fetchAddresses();
});
</script>
