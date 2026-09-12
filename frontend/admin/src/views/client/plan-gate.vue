<template>
  <YdPage title="升级后可使用该能力" surface="elevated">
  <div class="plan-gate-page coachpro-tertiary coachpro-tertiary--client">
    <div class="plan-gate-page__card uj-kpi-card">
      <p class="plan-gate-page__copy">{{ gateCopy }}</p>
      <div class="plan-gate-page__plans">
        <a-tag color="blue">当前：{{ gateInfo.current_plan_name || '体验版' }}</a-tag>
        <span class="plan-gate-page__arrow">→</span>
        <a-tag color="purple">需要：{{ gateInfo.required_plan_name || '企业版' }}</a-tag>
      </div>
      <div class="plan-gate-page__actions">
        <a-button type="primary" @click="goBilling">查看套餐与升级</a-button>
        <a-button v-if="fromPath" @click="goBack">返回上一页</a-button>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { YdPage } from '@/components/youding';

import { bffPlanCheck } from '@/api/admin-bff';

const route = useRoute();
const router = useRouter();

const featureKey = computed(() => String(route.query.feature || 'egress_ip'));
const fromPath = computed(() => (route.query.from ? String(route.query.from) : ''));

const gateInfo = reactive<Record<string, string | boolean>>({
  cta_copy: '',
  current_plan_name: '',
  required_plan_name: '',
});

const defaultCopy = '该能力属于更高套餐，升级后立即可用。';

const FEATURE_GATE_COPY: Record<string, string> = {
  media_factory:
    '视频工厂需开通企业版并部署翻译/配音 Sidecar（LibreTranslate / Vozo）。当前未配置上游时不会假成功，请联系管理员开通或升级套餐。',
  egress_ip: '独立出口 IP 需 Enterprise 套餐，由超管 fulfillment 后分配真实 host/port/账密。',
  seo_matrix: 'AI 场景矩阵需 SEO Pro 套餐，并配置 AI Key 后方可探测收录。',
  article_to_video: '文章转视频属于视频工厂增值能力，需 media_factory 套餐 + Sidecar。',
};

const gateCopy = computed(() => {
  const fromApi = String(gateInfo.cta_copy || '').trim();
  if (fromApi) return fromApi;
  return FEATURE_GATE_COPY[featureKey.value] || defaultCopy;
});

async function loadGate() {
  try {
    const data = await bffPlanCheck(featureKey.value);
    Object.assign(gateInfo, data);
    if (data.allowed) {
      router.replace(fromPath.value || '/client/dashboard');
    }
  } catch {
    /* 离线降级：仍展示升级 CTA */
  }
}

function goBilling() {
  router.push('/client/billing');
}

function goBack() {
  router.push(fromPath.value || '/client/dashboard');
}

onMounted(loadGate);
</script>

<style scoped lang="scss">
@use '@/styles/design-tokens-v2.scss';

.plan-gate-page {
  max-width: 560px;
  margin: 48px auto;
  padding: 0 var(--uj-space-page);
  &__card {
    padding: var(--uj-space-card);
  }
  &__title {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 12px;
  }
  &__copy {
    color: var(--uj-text-muted);
    margin: 0 0 16px;
  }
  &__plans {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 24px;
  }
  &__arrow {
    color: var(--uj-text-muted);
  }
  &__actions {
    display: flex;
    gap: 12px;
  }
}
</style>
