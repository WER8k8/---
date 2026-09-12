<template>
  <YdPage title="站点内容补齐" subtitle="Formily 快速补全 L-Pro 发布门禁 — 与可视化建站同页能力" surface="elevated">
    <div class="site-editor-lab coachpro-tertiary coachpro-tertiary--client">
      <template v-if="loading">
        <SkeletonCard variant="card" />
      </template>
      <template v-else>
        <div class="site-editor-lab__toolbar mb-4">
          <a-space wrap>
            <a-button v-if="previewUrl" type="link" :href="previewUrl" target="_blank" rel="noopener noreferrer">
              预览官网 →
            </a-button>
            <a-button type="link" @click="goProductImages">
              产品图片空间 →
            </a-button>
            <a-button type="link" @click="router.push({ path: '/client/site-editor', query: { side: 'gap' } })">
              完整建站页（可视化 + 发布补齐）→
            </a-button>
          </a-space>
        </div>

        <SiteEditorLProPublishBanner
          :site-content="siteContent"
          template-id="premium-b2b-v1"
        />

        <a-alert
          v-if="publishReady"
          class="mb-4"
          type="success"
          show-icon
          message="L-Pro 发布门禁已满足，可对外预览/送审"
        />

        <a-alert
          v-if="productGateHint"
          class="mb-4"
          type="info"
          show-icon
          :message="productGateHint"
        >
          <template #description>
            <a-button type="link" size="small" class="p-0" @click="goProductImages">
              去上传至少 3 张产品图 →
            </a-button>
          </template>
        </a-alert>

        <a-segmented
          v-model:value="activeTab"
          block
          class="site-editor-lab__tabs mb-4"
          :options="tabOptions"
        />

        <SiteEditorGapPanel
          v-show="activeTab === 'gap'"
          :site-content="siteContent"
          @apply="onGapApplied"
        />

        <div v-show="activeTab === 'jtbd'" class="site-editor-lab__jtbd">
          <JtbdSiteChecklist :items="jtbdChecklist" />
          <p class="text-sm text-gray-600 mt-3">
            下方「发布补齐」表单已含主承诺、阶段服务与技术干货字段；保存后公网 L-Pro 首页同步。
          </p>
          <a-button type="link" class="px-0" @click="activeTab = 'gap'">去编辑 JTBD 字段 →</a-button>
        </div>

        <div v-show="activeTab === 'seo'" class="site-editor-lab__seo">
          <SiteEditorSeoPanel v-model="seoFields" :site-url="previewHost" />
          <a-button type="primary" class="mt-4" :loading="seoSaving" @click="saveSeo">
            同步 SEO 到官网
          </a-button>
        </div>

        <div v-show="activeTab === 'i18n'" class="site-editor-lab__i18n">
          <p class="text-sm text-gray-600 mb-2">
            Tier1 十二语已写入站点 i18n 包；访客切换语言时 Hero/产品文案跟随（SITE-DESIGN-01g）。
          </p>
          <div class="flex flex-wrap gap-2">
            <a-tag v-for="loc in tier1Locales" :key="loc.value" color="blue">
              {{ loc.label }}
            </a-tag>
          </div>
          <a-button type="link" class="mt-3 px-0" @click="router.push('/client/geo-visibility')">
            查看 GEO/AEO 可见性看板 →
          </a-button>
        </div>
      </template>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import SiteEditorLProPublishBanner from '@/components/site-builder/SiteEditorLProPublishBanner.vue';
import SiteEditorGapPanel from '@/components/site-builder/SiteEditorGapPanel.vue';
import SiteEditorSeoPanel from '@/components/site-builder/SiteEditorSeoPanel.vue';
import JtbdSiteChecklist, {
  type JtbdChecklistItem,
} from '@/components/site-builder/JtbdSiteChecklist.vue';
import { bffSiteEditorDraftGet } from '@/api/admin-bff';
import { productImageSpacePath } from '@/constants/productImageSpace';
import { L_PRO_TIER1_LOCALES } from '@/constants/lProTier1Locales';
import {
  applySeoToSnapshot,
  snapshotToSeo,
  type SiteSeoFields,
} from '@/templates/site-builder';
import { evaluateLProPublishGate } from '@/utils/l-pro-publish-gate';
import {
  loadTenantSiteContent,
  refreshOnboardingPreviewUrl,
  saveTenantSiteContent,
} from '@/utils/siteEditorLabSync';
import { apiGet } from '@/utils/api';

const router = useRouter();
const loading = ref(false);
const seoSaving = ref(false);
const siteContent = ref<Record<string, unknown>>({});
const previewUrl = ref('');
const activeTab = ref<'gap' | 'jtbd' | 'seo' | 'i18n'>('gap');
const jtbdChecklist = ref<JtbdChecklistItem[]>([]);

const tabOptions = [
  { label: '发布补齐', value: 'gap' },
  { label: 'JTBD 四要素', value: 'jtbd' },
  { label: 'SEO', value: 'seo' },
  { label: '多语言', value: 'i18n' },
];

const tier1Locales = L_PRO_TIER1_LOCALES;

const defaultSeo = (): SiteSeoFields => ({
  pageTitle: '',
  seoDescription: '',
  seoKeywords: '',
  domesticPageTitle: '',
  domesticSeoDescription: '',
  domesticSeoKeywords: '',
  russianPageTitle: '',
  russianSeoDescription: '',
  russianSeoKeywords: '',
  allowIndex: true,
  seoPrimaryMarket: 'export',
});

const seoFields = ref<SiteSeoFields>(defaultSeo());

const previewHost = computed(() => {
  const raw = previewUrl.value || '';
  try {
    return raw ? new URL(raw).host : '';
  } catch {
    return raw.replace(/^https?:\/\//, '').split('/')[0] || '';
  }
});

const productGateHint = computed(() => {
  const gate = evaluateLProPublishGate({
    ...siteContent.value,
    templateId: 'premium-b2b-v1',
    templateTier: 'L-Pro',
  });
  const productIssues = gate.issues.filter((i) =>
    ['product_count', 'product_images'].includes(i.check),
  );
  if (!productIssues.length) return '';
  return productIssues.map((i) => i.detail).join('；');
});

const publishReady = computed(() => {
  const gate = evaluateLProPublishGate({
    ...siteContent.value,
    templateId: 'premium-b2b-v1',
    templateTier: 'L-Pro',
  });
  return gate.publish_ready === true && gate.p0 === 0;
});

function syncSeoFromContent(content: Record<string, unknown>) {
  seoFields.value = snapshotToSeo(content as unknown as Parameters<typeof snapshotToSeo>[0]);
}

async function loadPreviewUrl() {
  try {
    const urls = await refreshOnboardingPreviewUrl();
    previewUrl.value = urls.dev || urls.prod || '';
  } catch {
    previewUrl.value = '';
  }
}

async function loadJtbdChecklist() {
  try {
    const data = await apiGet<{ jtbd_checklist?: JtbdChecklistItem[] }>('/client/onboarding-guides');
    jtbdChecklist.value = data?.jtbd_checklist || [];
  } catch {
    jtbdChecklist.value = [];
  }
}

async function loadSite() {
  loading.value = true;
  try {
    const [siteContentResult, draftResult, previewResult] = await Promise.allSettled([
      loadTenantSiteContent(),
      bffSiteEditorDraftGet(),
      loadPreviewUrl(),
      loadJtbdChecklist(),
    ]);
    if (siteContentResult.status === 'fulfilled') {
      siteContent.value = siteContentResult.value;
      syncSeoFromContent(siteContent.value);
    }
    if (siteContentResult.status === 'rejected' && draftResult.status === 'rejected') {
      throw siteContentResult.reason;
    }
    if (previewResult.status === 'rejected') {
      await loadPreviewUrl();
    }
  } catch (err: unknown) {
    message.warning(err instanceof Error ? err.message : '加载站点内容失败');
  } finally {
    loading.value = false;
  }
}

function onGapApplied(merged: Record<string, unknown>) {
  siteContent.value = merged;
  syncSeoFromContent(merged);
  void loadPreviewUrl();
  void loadJtbdChecklist();
}

async function saveSeo() {
  seoSaving.value = true;
  try {
    const merged = applySeoToSnapshot(
      siteContent.value as unknown as Parameters<typeof applySeoToSnapshot>[0],
      seoFields.value,
    );
    await saveTenantSiteContent(merged as unknown as Record<string, unknown>);
    siteContent.value = merged as unknown as Record<string, unknown>;
    message.success('SEO 已同步到官网');
    await loadPreviewUrl();
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : 'SEO 保存失败');
  } finally {
    seoSaving.value = false;
  }
}

function goProductImages() {
  router.push(productImageSpacePath(true));
}

onMounted(() => {
  void loadSite();
});
</script>

<style scoped>
.site-editor-lab {
  max-width: 820px;
  margin: 24px auto;
  padding: 0 24px 24px;
}

.site-editor-lab__toolbar {
  display: flex;
  justify-content: flex-end;
}

.site-editor-lab__tabs {
  max-width: 360px;
}

.site-editor-lab__seo {
  margin-top: 4px;
}
</style>
