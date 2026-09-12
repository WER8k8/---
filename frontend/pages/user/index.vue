<template>
  <div class="user-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          {{ t('user.title') }}
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          {{ t('user.subtitle') }}
        </p>
      </div>
    </section>

    <!-- User Dashboard -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 sm:gap-8">
          <!-- Sidebar -->
          <div class="lg:col-span-1">
            <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
              <div class="flex items-center gap-4 mb-6">
                <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-text-primary">{{ user?.name || t('user.guest') }}</h3>
                  <p class="text-sm text-text-secondary">{{ user?.email || '' }}</p>
                </div>
              </div>
              <nav class="space-y-2">
                <button
                  v-for="item in navItems"
                  :key="item.key"
                  @click="activeTab = item.key"
                  :class="[
                    'w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                    activeTab === item.key
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-secondary hover:bg-surface-elevated hover:text-text-primary'
                  ]"
                >
                  {{ item.label }}
                </button>
              </nav>
            </div>
          </div>

          <!-- Main Content -->
          <div class="lg:col-span-3">
            <!-- Profile Tab -->
            <div v-if="activeTab === 'profile'" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
              <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">{{ t('user.profileTitle') }}</h2>
              <form @submit.prevent="updateProfile" class="space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">{{ t('user.name') }}</label>
                    <input
                      v-model="profileForm.name"
                      type="text"
                      class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-text-primary mb-2">{{ t('user.email') }}</label>
                    <input
                      v-model="profileForm.email"
                      type="email"
                      disabled
                      class="w-full px-4 py-2.5 border border-border rounded-lg bg-surface-elevated text-text-secondary"
                    />
                  </div>
                </div>
                <div class="flex justify-end">
                  <button type="submit" class="btn-primary">{{ t('common.save') }}</button>
                </div>
              </form>
            </div>

            <!-- Orders Tab -->
            <div v-else-if="activeTab === 'orders'" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
              <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">{{ t('user.ordersTitle') }}</h2>
              <div v-if="userOrders.length === 0" class="text-center py-8 text-text-secondary">
                {{ t('user.noOrders') }}
              </div>
              <div v-else class="space-y-4">
                <div
                  v-for="order in userOrders"
                  :key="order.id"
                  class="border border-border rounded-lg p-4 hover:bg-surface-elevated transition-colors"
                >
                  <div class="flex justify-between items-center mb-2">
                    <span class="font-medium text-text-primary">#{{ order.order_number }}</span>
                    <span
                      :class="[
                        'px-2 py-1 rounded text-xs font-medium',
                        order.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ order.status }}
                    </span>
                  </div>
                  <p class="text-sm text-text-secondary">{{ t('user.orderDate') }}: {{ new Date(order.created_at).toLocaleDateString() }}</p>
                </div>
              </div>
            </div>

            <!-- Inquiries Tab -->
            <div v-else-if="activeTab === 'inquiries'" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
              <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-6">{{ t('user.inquiriesTitle') }}</h2>
              <div v-if="userInquiries.length === 0" class="text-center py-8 text-text-secondary">
                {{ t('user.noInquiries') }}
              </div>
              <div v-else class="space-y-4">
                <div
                  v-for="inquiry in userInquiries"
                  :key="inquiry.id"
                  class="border border-border rounded-lg p-4 hover:bg-surface-elevated transition-colors"
                >
                  <div class="flex justify-between items-center mb-2">
                    <span class="font-medium text-text-primary">{{ inquiry.subject }}</span>
                    <span
                      :class="[
                        'px-2 py-1 rounded text-xs font-medium',
                        inquiry.status === 'replied' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      ]"
                    >
                      {{ inquiry.status }}
                    </span>
                  </div>
                  <p class="text-sm text-text-secondary truncate">{{ inquiry.message }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const router = useRouter();

const user = ref(null);
const activeTab = ref('profile');
const profileForm = ref({ name: '', email: '' });
const userOrders = ref([]);
const userInquiries = ref([]);

const navItems = [
  { key: 'profile', label: t('user.profile') },
  { key: 'orders', label: t('user.orders') },
  { key: 'inquiries', label: t('user.inquiries') },
];

// 获取用户信息
const fetchUser = async () => {
  try {
    const response = await fetch('/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      user.value = data;
      profileForm.value = { name: data.name, email: data.email };
    }
  } catch (err) {
    console.error('Failed to fetch user:', err);
  }
};

// 获取用户订单
const fetchUserOrders = async () => {
  try {
    const response = await fetch('/api/v1/orders/?user_id=me', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      userOrders.value = data;
    }
  } catch (err) {
    console.error('Failed to fetch orders:', err);
  }
};

// 获取用户询盘
const fetchUserInquiries = async () => {
  try {
    const response = await fetch('/api/v1/inquiries/unified?page_size=50', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const payload = await response.json();
      const data = payload.data ?? payload;
      userInquiries.value = data.items ?? data;
    }
  } catch (err) {
    console.error('Failed to fetch inquiries:', err);
  }
};

// 更新个人资料
const updateProfile = async () => {
  try {
    const response = await fetch('/api/v1/users/me', {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileForm.value),
    });
    if (response.ok) {
      alert(t('user.profileUpdated'));
    }
  } catch (err) {
    console.error('Failed to update profile:', err);
  }
};

// 监听tab变化
watch(activeTab, (newTab) => {
  if (newTab === 'orders') {
    fetchUserOrders();
  } else if (newTab === 'inquiries') {
    fetchUserInquiries();
  }
});

// SEO元数据
useHead({
  title: computed(() => `${t('user.title')} - ${t('common.companyName')}`),
  meta: [
    { name: 'description', content: t('user.subtitle') },
  ],
});

onMounted(() => {
  fetchUser();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}
</style>
