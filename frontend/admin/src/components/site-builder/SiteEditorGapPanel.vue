<template>
  <div class="site-editor-gap-panel uj-glass-panel">
    <header class="site-editor-gap-panel__head">
      <h3>发布门禁补齐</h3>
      <p>关于页、联系渠道等为 L-Pro 对外上线必填项，填完可一键应用。</p>
    </header>

    <YdFormilyForm v-model="form" :schema="siteEditorFormilySchema">
      <template #actions>
        <a-space wrap>
          <a-button type="primary" :loading="applying" @click="handleApply">
            {{ embedded ? '应用到编辑器' : '同步到官网' }}
          </a-button>
          <a-button v-if="!embedded" :loading="saving" @click="saveDraftOnly">
            仅保存草稿
          </a-button>
        </a-space>
      </template>
    </YdFormilyForm>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import { message } from 'ant-design-vue';

import { YdFormilyForm } from '@/components/youding';
import { siteEditorFormilySchema } from '@/components/youding/formily/siteEditorSchema';
import type { SiteEditorDraft } from '@/api/admin-bff';
import { bffSiteEditorDraftGet, bffSiteEditorDraftSave } from '@/api/admin-bff';
import {
  draftFromSiteContent,
  mergeDraftIntoSiteContent,
  saveTenantSiteContent,
} from '@/utils/siteEditorLabSync';

const props = withDefaults(
  defineProps<{
    siteContent: Record<string, unknown>;
    embedded?: boolean;
  }>(),
  { embedded: false },
);

const emit = defineEmits<{
  apply: [merged: Record<string, unknown>];
}>();

const defaultForm = (): SiteEditorDraft => ({
  title: '优丁独立站',
  hero: '建材外贸 · AI 营销',
  locale: 'zh-CN',
  showCta: true,
  brandName: '',
  aboutText: '',
  contactPhone: '',
  contactEmail: '',
  ctaLabel: '立即询盘',
});

const form = reactive<SiteEditorDraft>(defaultForm());
const applying = ref(false);
const saving = ref(false);

function syncFormFromSite(content: Record<string, unknown>) {
  Object.assign(form, { ...defaultForm(), ...draftFromSiteContent(content) });
}

watch(
  () => props.siteContent,
  (content) => {
    if (content && Object.keys(content).length) {
      syncFormFromSite(content);
    }
  },
  { immediate: true, deep: true },
);

function buildPayload(): SiteEditorDraft {
  return {
    title: String(form.title ?? ''),
    hero: String(form.hero ?? ''),
    locale: String(form.locale ?? 'zh-CN'),
    showCta: Boolean(form.showCta),
    brandName: String(form.brandName ?? ''),
    aboutText: String(form.aboutText ?? ''),
    contactPhone: String(form.contactPhone ?? ''),
    contactEmail: String(form.contactEmail ?? ''),
    ctaLabel: String(form.ctaLabel ?? '立即询盘'),
    primaryPromise: String(form.primaryPromise ?? ''),
    inquiryHook: String(form.inquiryHook ?? ''),
    stage1Title: String(form.stage1Title ?? ''),
    stage1Desc: String(form.stage1Desc ?? ''),
    stage2Title: String(form.stage2Title ?? ''),
    stage2Desc: String(form.stage2Desc ?? ''),
    stage3Title: String(form.stage3Title ?? ''),
    stage3Desc: String(form.stage3Desc ?? ''),
    stage4Title: String(form.stage4Title ?? ''),
    stage4Desc: String(form.stage4Desc ?? ''),
    knowledge1Title: String(form.knowledge1Title ?? ''),
    knowledge1Hook: String(form.knowledge1Hook ?? ''),
    knowledge2Title: String(form.knowledge2Title ?? ''),
    knowledge2Hook: String(form.knowledge2Hook ?? ''),
    knowledge3Title: String(form.knowledge3Title ?? ''),
    knowledge3Hook: String(form.knowledge3Hook ?? ''),
  };
}

async function saveDraftOnly() {
  saving.value = true;
  try {
    const saved = await bffSiteEditorDraftSave(buildPayload());
    Object.assign(form, { ...defaultForm(), ...saved });
    message.success('草稿已保存');
  } catch {
    message.error('草稿保存失败');
  } finally {
    saving.value = false;
  }
}

async function handleApply() {
  applying.value = true;
  try {
    const payload = buildPayload();
    const merged = mergeDraftIntoSiteContent(props.siteContent, payload);

    if (props.embedded) {
      emit('apply', merged);
      message.success('已应用到编辑器，请点顶部「保存」写入服务器');
      return;
    }

    await bffSiteEditorDraftSave(payload);
    await saveTenantSiteContent(merged);
    emit('apply', merged);
    message.success('已同步到官网');
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败');
  } finally {
    applying.value = false;
  }
}

onMounted(async () => {
  if (props.embedded) return;
  try {
    const draft = await bffSiteEditorDraftGet();
    Object.assign(form, { ...defaultForm(), ...draftFromSiteContent(props.siteContent), ...draft });
  } catch {
    /* 使用 siteContent 默认值 */
  }
});
</script>

<style scoped lang="scss">
.site-editor-gap-panel {
  padding: 14px 16px;
  border-radius: 12px;
  height: fit-content;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.site-editor-gap-panel__head {
  margin-bottom: 12px;

  h3 {
    margin: 0 0 4px;
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
  }

  p {
    margin: 0;
    font-size: 12px;
    color: #64748b;
    line-height: 1.45;
  }
}
</style>
