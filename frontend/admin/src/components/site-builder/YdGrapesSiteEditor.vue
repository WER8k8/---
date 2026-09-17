/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-grapes-editor site-builder-isolated">
    <div class="yd-grapes-editor__toolbar">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <a-space wrap>
          <span class="yd-grapes-editor__label font-medium">预览端:</span>
          <a-radio-group v-model:value="device" size="small" button-style="solid" @change="onDeviceChange">
            <a-radio-button value="desktop">桌面端</a-radio-button>
            <a-radio-button value="mobile">移动端 (Mobile-First)</a-radio-button>
          </a-radio-group>
          <a-divider type="vertical" />
          <a-dropdown>
            <a-button size="small">
              + 插入业务组件 ▾
            </a-button>
            <template #overlay>
              <a-menu @click="onInsertBlock">
                <a-menu-item key="yd-inquiry-form">询盘表单 (RFQ)</a-menu-item>
                <a-menu-item key="yd-whatsapp">WhatsApp 沟通按钮</a-menu-item>
                <a-menu-item key="yd-trust-badges">信任徽章 (Trust)</a-menu-item>
                <a-menu-item key="yd-stats-row">核心数据条 (Stats)</a-menu-item>
                <a-menu-item key="yd-cert-strip">国际认证条 (CE/ISO)</a-menu-item>
                <a-menu-item key="yd-cta-band">全宽行动条 (CTA)</a-menu-item>
                <a-menu-item key="yd-process">外贸履约流程</a-menu-item>
                <a-menu-item key="yd-footer">多栏出海页脚</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <a-button size="small" @click="syncFromStructured">重新同步整站数据</a-button>
        </a-space>

        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-400">💡 提示：在页面上直接点击文字打字修改，双击图片更换素材</span>
          <a-button size="small" type="primary" ghost @click="emit('request-save')">
            保存修改
          </a-button>
        </div>
      </div>
    </div>
    <div ref="containerRef" class="yd-grapes-editor__canvas site-canvas-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue';
import type { MenuProps } from 'ant-design-vue';

import { useGrapesSiteEditor } from '@/composables/useGrapesSiteEditor';
import type { SiteBuilderTemplateId, SiteContentSnapshot, VisualEditorPayload } from '@/templates/site-builder';

const props = defineProps<{
  templateId: SiteBuilderTemplateId;
  siteSnapshot: SiteContentSnapshot;
  visualPayload?: VisualEditorPayload | null;
}>();

const emit = defineEmits<{
  'request-save': [];
  'update:templateId': [SiteBuilderTemplateId];
}>();

const containerRef = ref<HTMLElement | null>(null);
const device = ref<'desktop' | 'mobile'>('desktop');

const {
  ready,
  loadFromSiteContent,
  loadFromVisualPayload,
  exportVisual,
  setDevice,
  insertBlock,
  initEditor,
} = useGrapesSiteEditor(containerRef);

const onInsertBlock: MenuProps['onClick'] = (info) => {
  insertBlock(String(info.key));
};

function onDeviceChange() {
  setDevice(device.value);
}

function syncFromStructured() {
  loadFromSiteContent(props.siteSnapshot, props.templateId);
}

function applyTemplate(id: SiteBuilderTemplateId) {
  emit('update:templateId', id);
  loadFromSiteContent(props.siteSnapshot, id);
}

function bootstrap() {
  if (!ready.value) {
    initEditor();
  }
  nextTick(() => {
    if (props.visualPayload?.html || props.visualPayload?.projectData) {
      loadFromVisualPayload(props.visualPayload);
    } else {
      loadFromSiteContent(props.siteSnapshot, props.templateId);
    }
  });
}

watch(
  () => props.templateId,
  (id, prev) => {
    if (id !== prev && ready.value) {
      loadFromSiteContent(props.siteSnapshot, id);
    }
  },
);

onMounted(() => {
  initEditor();
  nextTick(() => bootstrap());
});

defineExpose({
  exportVisual,
  syncFromStructured,
  applyTemplate,
  loadFromVisualPayload,
});
</script>

<style scoped lang="scss">
.yd-grapes-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 640px;
  height: calc(100vh - 220px);
}

.yd-grapes-editor__toolbar {
  padding: 10px 14px;
  background: var(--uj-glass-bg-strong, #fff);
  border: 1px solid var(--uj-border, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.yd-grapes-editor__label {
  font-size: 13px;
  color: #64748b;
}

.yd-grapes-editor__hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.yd-grapes-editor__canvas {
  flex: 1;
  min-height: 520px;
  border: 1px solid var(--uj-border, #e2e8f0);
  border-radius: 12px;
  overflow: hidden;
  background: #f8fafc;
  position: relative;
}

:deep(.gjs-editor) {
  height: 100%;
}

:deep(.gjs-cv-canvas) {
  width: 100% !important;
  top: 0 !important;
  background: #f1f5f9;
}

/* 彻底隐藏 GrapesJS 原生杂乱面板（包括侧边积木块、图层树、设置栏等），打造纯净所见即所得 AI 画布 */
:deep(.gjs-pn-views-container),
:deep(.gjs-pn-panel.gjs-pn-views),
:deep(.gjs-pn-panel.gjs-pn-options),
:deep(.gjs-pn-panel.gjs-pn-devices-c),
:deep(.gjs-pn-commands) {
  display: none !important;
}

:deep(.gjs-cv-canvas) {
  right: 0 !important;
  left: 0 !important;
  bottom: 0 !important;
}
</style>
