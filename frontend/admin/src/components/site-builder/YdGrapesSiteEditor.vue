<template>
  <div class="yd-grapes-editor">
    <div class="yd-grapes-editor__toolbar">
      <a-space wrap>
        <span class="yd-grapes-editor__label">端预览</span>
        <a-radio-group v-model:value="device" size="small" button-style="solid" @change="onDeviceChange">
          <a-radio-button value="desktop">桌面</a-radio-button>
          <a-radio-button value="mobile">手机</a-radio-button>
        </a-radio-group>
        <a-button size="small" @click="syncFromStructured">从 AI/表单同步</a-button>
        <a-dropdown>
          <a-button size="small">插入区块 ▾</a-button>
          <template #overlay>
            <a-menu @click="onInsertBlock">
              <a-menu-item key="yd-inquiry-form">询盘表单</a-menu-item>
              <a-menu-item key="yd-whatsapp">WhatsApp 按钮</a-menu-item>
              <a-menu-item key="yd-trust-badges">信任徽章</a-menu-item>
              <a-menu-item key="yd-stats-row">数据条</a-menu-item>
              <a-menu-item key="yd-cert-strip">认证条</a-menu-item>
              <a-menu-item key="yd-section-head">区块标题</a-menu-item>
              <a-menu-item key="yd-cta-band">全宽 CTA 条</a-menu-item>
              <a-menu-item key="yd-process">合作流程</a-menu-item>
              <a-menu-item key="yd-partners">合作伙伴</a-menu-item>
              <a-menu-item key="yd-footer">企业页脚</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-button size="small" type="primary" ghost @click="emit('request-save')">保存当前版式</a-button>
      </a-space>
      <p class="yd-grapes-editor__hint">右侧为组件库：拖入「询盘表单」「数据条」等；顶部图标依次为预览、全屏、查看代码、撤销/重做等</p>
    </div>
    <div ref="containerRef" class="yd-grapes-editor__canvas" />
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
  padding: 10px 12px;
  background: var(--uj-glass-bg-strong, #fff);
  border: 1px solid var(--uj-border, #e2e8f0);
  border-radius: 12px;
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
}

:deep(.gjs-editor) {
  height: 100%;
}

:deep(.gjs-cv-canvas) {
  background: #e2e8f0;
}
</style>
