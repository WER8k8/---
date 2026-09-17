/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { onUnmounted, ref, shallowRef, type Ref } from 'vue';
import grapesjs, { type Editor } from 'grapesjs';
import gjsPresetWebpage from 'grapesjs-preset-webpage';

import {
  buildPageHtml,
  DEFAULT_TEMPLATE_ID,
  type SiteBuilderTemplateId,
  type SiteContentSnapshot,
  type VisualEditorPayload,
} from '@/templates/site-builder';

import 'grapesjs/dist/css/grapes.min.css';

import {
  appendBlockStyles,
  insertBlockById,
  registerYoudingBlocks,
} from '@/templates/site-builder/registerYoudingBlocks';
import { grapesjsLocaleZh } from '@/templates/site-builder/grapesjsLocaleZh';
import { localizeGrapesEditor } from '@/templates/site-builder/localizeGrapesEditor';

export function useGrapesSiteEditor(container: Ref<HTMLElement | null>) {
  const editor = shallowRef<Editor | null>(null);
  const ready = ref(false);
  const templateId = ref<SiteBuilderTemplateId>(DEFAULT_TEMPLATE_ID);

  function initEditor() {
    if (!container.value || editor.value) return;
    editor.value = grapesjs.init({
      container: container.value,
      height: '100%',
      width: 'auto',
      fromElement: false,
      storageManager: false,
      noticeOnUnload: false,
      plugins: [gjsPresetWebpage],
      pluginsOpts: {
        'gjs-preset-webpage': {
          modalImportTitle: '导入 HTML',
          modalImportButton: '导入',
          modalImportLabel: '粘贴 HTML 代码后点击导入',
          textCleanCanvas: '确定要清空画布吗？此操作不可撤销。',
        },
      },
      i18n: {
        locale: 'zh',
        detectLocale: false,
        localeFallback: 'zh',
        messages: { zh: grapesjsLocaleZh },
      },
      canvas: {
        styles: [],
      },
      deviceManager: {
        devices: [
          { id: 'desktop', name: '桌面', width: '' },
          { id: 'mobile', name: '手机', width: '375px', widthMedia: '480px' },
        ],
      },
    });
    registerYoudingBlocks(editor.value);
    appendBlockStyles(editor.value);
    localizeGrapesEditor(editor.value);
    ready.value = true;
  }

  function loadHtmlCss(html: string, css: string) {
    const ed = editor.value;
    if (!ed) return;
    ed.setComponents(html);
    ed.setStyle(css);
  }

  function loadFromSiteContent(data: SiteContentSnapshot, id: SiteBuilderTemplateId = templateId.value) {
    templateId.value = id;
    const built = buildPageHtml(id, data);
    loadHtmlCss(built.html, built.css);
  }

  function loadFromVisualPayload(payload: VisualEditorPayload) {
    templateId.value = payload.templateId || DEFAULT_TEMPLATE_ID;
    const ed = editor.value;
    if (!ed) return;
    if (payload.projectData && Object.keys(payload.projectData).length) {
      ed.loadProjectData(payload.projectData as Parameters<Editor['loadProjectData']>[0]);
      return;
    }
    if (payload.html) {
      loadHtmlCss(payload.html, payload.css || '');
    }
  }

  function exportVisual(): VisualEditorPayload {
    const ed = editor.value;
    if (!ed) {
      return { templateId: templateId.value, html: '', css: '' };
    }
    return {
      templateId: templateId.value,
      projectData: ed.getProjectData() as Record<string, unknown>,
      html: ed.getHtml(),
      css: ed.getCss() as string,
      updatedAt: new Date().toISOString(),
    };
  }

  function setDevice(device: 'desktop' | 'mobile') {
    editor.value?.setDevice(device === 'mobile' ? 'mobile' : 'desktop');
  }

  function insertBlock(blockId: string) {
    if (editor.value) insertBlockById(editor.value, blockId);
  }

  function destroyEditor() {
    editor.value?.destroy();
    editor.value = null;
    ready.value = false;
  }

  onUnmounted(() => {
    destroyEditor();
  });

  return {
    editor,
    ready,
    templateId,
    loadFromSiteContent,
    loadFromVisualPayload,
    exportVisual,
    setDevice,
    insertBlock,
    destroyEditor,
    initEditor,
  };
}
