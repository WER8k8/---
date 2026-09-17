/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <div class="flex items-center justify-between h-14">
        <h1 class="text-base font-semibold text-gray-900">{{ $t('mobile.leads.title') }}</h1>
        <button
          class="mobile-btn-primary px-4 py-2 rounded-lg text-sm font-medium"
          @click="showAddModal = true"
        >
          {{ $t('mobile.leads.add') }}
        </button>
      </div>
    </MobileNavbar>

    <!-- Loading State -->
    <div v-if="pending" class="px-4 py-6 space-y-4">
      <div v-for="i in 3" :key="i" class="animate-pulse bg-white rounded-2xl p-4">
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="leads.length === 0" class="px-4 py-20 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656.126-1.283.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">{{ $t('mobile.leads.noLeads') }}</h3>
      <p class="text-sm text-gray-500 mb-6">{{ $t('mobile.leads.noLeadsDesc') }}</p>
      <button class="mobile-btn-primary px-6 py-3 rounded-full" @click="showAddModal = true">
        {{ $t('mobile.leads.addFirst') }}
      </button>
    </div>

    <!-- Leads List -->
    <div v-else class="px-4 py-4 space-y-4">
      <!-- Filter Tabs -->
      <div class="flex gap-2 overflow-x-auto no-scrollbar pb-2">
        <button
          v-for="tab in filterTabs"
          :key="tab.value"
          class="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors"
          :class="activeFilter === tab.value ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'"
          @click="activeFilter = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Lead Cards -->
      <div
        v-for="lead in filteredLeads"
        :key="lead.id"
        class="bg-white rounded-2xl p-4 shadow-sm"
        @click="router.push(`/mobile/leads/${lead.id}`)"
      >
        <!-- Lead Header -->
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-900 truncate flex-1">{{ lead.name }}</h3>
          <span
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium ml-2 flex-shrink-0',
              lead.status === 'new' ? 'bg-blue-100 text-blue-800' :
              lead.status === 'contacted' ? 'bg-yellow-100 text-yellow-800' :
              lead.status === 'converted' ? 'bg-green-100 text-green-800' :
              'bg-gray-100 text-gray-800'
            ]"
          >
            {{ $t(`mobile.leads.status.${lead.status}`) }}
          </span>
        </div>

        <!-- Lead Info -->
        <div class="space-y-1.5 mb-3">
          <div class="flex items-center gap-2 text-sm text-gray-600">
            <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span class="truncate">{{ lead.email }}</span>
          </div>
          <div v-if="lead.phone" class="flex items-center gap-2 text-sm text-gray-600">
            <svg class="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span>{{ lead.phone }}</span>
          </div>
        </div>

        <!-- Lead Source & Date -->
        <div class="flex items-center justify-between pt-3 border-t border-gray-100">
          <span class="text-xs text-gray-500">{{ lead.source || $t('mobile.leads.unknownSource') }}</span>
          <span class="text-xs text-gray-500">{{ new Date(lead.created_at).toLocaleDateString() }}</span>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />

    <!-- Add Lead Modal (simplified) -->
    <Teleport to="body">
      <div v-if="showAddModal" class="fixed inset-0 z-[100] bg-black/50 flex items-end justify-center" @click.self="showAddModal = false">
        <div class="w-full max-w-lg bg-white rounded-t-2xl p-6 max-h-[80vh] overflow-y-auto">
          <h2 class="text-lg font-bold text-gray-900 mb-4">{{ $t('mobile.leads.addTitle') }}</h2>
          <form @submit.prevent="addLead" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.leads.name') }}</label>
              <input v-model="newLead.name" type="text" required class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.leads.email') }}</label>
              <input v-model="newLead.email" type="email" required class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ $t('mobile.leads.phone') }}</label>
              <input v-model="newLead.phone" type="tel" class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div class="flex gap-3 pt-4">
              <button type="button" class="flex-1 mobile-btn-outline py-3 rounded-xl font-medium" @click="showAddModal = false">
                {{ $t('common.cancel') }}
              </button>
              <button type="submit" class="flex-1 mobile-btn-primary py-3 rounded-xl font-medium">
                {{ $t('common.save') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const router = useRouter();
const { $t } = useI18n();

// Data
const { data: leads, pending, error } = await useFetch('/api/leads', {
  key: 'mobile-leads',
  lazy: true,
});

// Filter
const activeFilter = ref('all');
const filterTabs = [
  { label: $t('mobile.leads.all'), value: 'all' },
  { label: $t('mobile.leads.new'), value: 'new' },
  { label: $t('mobile.leads.contacted'), value: 'contacted' },
  { label: $t('mobile.leads.converted'), value: 'converted' },
];

const filteredLeads = computed(() => {
  if (activeFilter.value === 'all') return leads.value || [];
  return (leads.value || []).filter(l => l.status === activeFilter.value);
});

// Add modal
const showAddModal = ref(false);
const newLead = ref({ name: '', email: '', phone: '' });

const addLead = async () => {
  try {
    await $fetch('/api/leads', {
      method: 'POST',
      body: newLead.value,
    });
    showAddModal.value = false;
    newLead.value = { name: '', email: '', phone: '' };
    // Refresh
    await refreshNuxtData('mobile-leads');
  } catch (err) {
    alert($t('mobile.leads.addError'));
  }
};

// Page meta
useHead({
  title: $t('mobile.leads.title'),
});
</script>
