<template>
  <div class="ext-shell p-6">
    <header class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">
        {{ nav.title }}
      </h1>
      <p class="mt-1 text-sm text-slate-500">
        {{ nav.subtitle }}
      </p>
      <a-alert
        class="mt-4"
        type="info"
        show-icon
        message="规划能力预览"
        description="本模块后端能力尚在迭代；下方按钮可切换子页或跳转已上线功能，不会退出登录。"
      />
    </header>

    <section
      v-if="nav.siblings.length"
      class="mb-6"
    >
      <h2 class="mb-2 text-sm font-semibold text-slate-600">
        本子模块
      </h2>
      <a-space wrap>
        <a-button
          v-for="s in nav.siblings"
          :key="s.path"
          :type="isActive(s.path) ? 'primary' : 'default'"
          @click="go(s.path)"
        >
          {{ s.label }}
        </a-button>
      </a-space>
    </section>

    <section
      v-if="nav.related.length"
      class="mb-6"
    >
      <h2 class="mb-2 text-sm font-semibold text-slate-600">
        已上线能力
      </h2>
      <a-space wrap>
        <a-button
          v-for="r in nav.related"
          :key="r.path"
          @click="go(r.path)"
        >
          {{ r.label }}
        </a-button>
      </a-space>
    </section>

    <div class="rounded-2xl border border-slate-100 bg-white p-10 text-center shadow-sm">
      <p class="text-slate-500">
        {{ pageNote }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { resolveExtModuleNav } from '@/constants/extModuleNav';
import { normalizeLocationPath } from '@/constants/workbenchPathCapabilities';

const props = withDefaults(
  defineProps<{
    pageNote?: string;
  }>(),
  {
    pageNote: '功能界面建设中；请使用上方按钮切换子页或进入已上线模块。',
  }
);

const route = useRoute();
const router = useRouter();

const nav = computed(() => {
  const hit = resolveExtModuleNav(route.path);
  if (hit) return hit;
  return {
    title: '扩展模块',
    subtitle: '',
    siblings: [] as { label: string; path: string }[],
    related: [
      { label: '超级管理员工作台', path: '/admin' },
      { label: '能力导航', path: '/admin/capability-hub' },
    ],
  };
});

function isActive(path: string) {
  return normalizeLocationPath(route.path) === normalizeLocationPath(path);
}

function go(path: string) {
  router.push(path);
}
</script>

<style scoped>
.ext-shell {
  min-height: 60vh;
}
</style>
