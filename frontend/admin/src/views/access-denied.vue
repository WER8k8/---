<template>
  <div class="access-denied">
    <a-result
      :status="isRouteKilled ? 'warning' : '403'"
      :title="pageTitle"
      :sub-title="subTitle"
    >
      <template #extra>
        <a-space wrap>
          <a-button
            v-if="!isRouteKilled && auth.isAuthenticated"
            @click="resyncFromJwt"
          >
            恢复按账号 JWT 同步会话
          </a-button>
          <a-button
            v-if="!isRouteKilled"
            type="primary"
            @click="goCapabilities"
          >
            代理能力划拨
          </a-button>
          <a-button
            :type="isRouteKilled ? 'primary' : 'default'"
            @click="goHome"
          >
            {{ homeLabel }}
          </a-button>
        </a-space>
      </template>
    </a-result>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useAgentCapabilitiesStore } from '@/stores/agentCapabilities';
import { homePathForRole } from '@/constants/roleShellLock';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const capStore = useAgentCapabilitiesStore();

const isRouteKilled = computed(() => route.query.reason === 'route_killed');

const pageTitle = computed(() => (isRouteKilled.value ? '功能已下架' : '无权访问'));

const subTitle = computed(() => {
  const reason = route.query.reason;
  const from = route.query.from;
  const fromText = typeof from === 'string' && from.length > 0 ? from : '';

  if (reason === 'route_killed') {
    const tail = fromText ? `原路径：${fromText}。` : '';
    return `${tail}该实验室功能已在商用评审中永久下架，菜单入口已移除。请从工作台使用送检范围内的能力。`;
  }
  if (reason === 'api403') {
    const apiPath = route.query.apiPath;
    const p = typeof apiPath === 'string' && apiPath.length > 0 ? apiPath : '接口';
    const f = fromText ? `来源：${fromText}。` : '';
    return `接口返回无权限（HTTP 403）：${p}。${f}您仍保持登录，可刷新页面或联系管理员开通权限。`;
  }
  const cap = route.query.cap;
  if (typeof cap === 'string' && cap.length > 0) {
    return `当前会话级别未包含能力：${cap}。可在「代理能力划拨」中为该级别勾选对应入口。`;
  }
  return '当前会话级别未包含该页面的工作台能力，请联系管理员或在「代理能力划拨」中调整。';
});

const homeLabel = computed(() => {
  if (!auth.isAuthenticated) return '去登录';
  if (isRouteKilled.value) return '返回工作台';
  return '超级管理员工作台';
});

function goCapabilities() {
  router.push('/admin/system/agent-capabilities');
}

function goHome() {
  if (!auth.isAuthenticated) {
    router.push({ path: '/login', query: route.query.from ? { redirect: String(route.query.from) } : {} });
    return;
  }
  router.push(homePathForRole(auth.currentRole));
}

function resyncFromJwt() {
  const t = auth.token;
  if (!t) return;
  capStore.resetSessionLevelFromJwt(t);
  router.push('/admin');
}
</script>

<style scoped lang="scss">
.access-denied {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  background: var(--yd-page-bg, #f5f7fb);
}
</style>
