/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage :title="pageTitle" :subtitle="pageSubtitle" surface="elevated">
    <a-alert
      v-if="!embedUrl && !nativePreviewUrl"
      type="warning"
      show-icon
      class="mb-4"
      :message="`${editorLabel} 未部署`"
      :description="deployHint"
    />

    <a-alert
      v-if="handoffLoaded && handoffSummary"
      type="info"
      show-icon
      class="mb-4"
      message="项目素材已载入"
      :description="handoffSummary"
    />

    <template v-if="embedUrl">
      <a-alert
        type="info"
        show-icon
        class="mb-4"
        message="外部剪辑器嵌入"
        description="已把 video_url / srt_url 通过 URL 参数传给编辑器；若对方未实现握手，请用下方内置预览。"
      />
      <div class="embed-shell">
        <iframe
          :key="iframeSrc"
          :src="iframeSrc"
          class="embed-frame"
          title="video-editor"
          allow="clipboard-read; clipboard-write; fullscreen"
          referrerpolicy="no-referrer-when-downgrade"
        />
      </div>
    </template>

    <a-card v-if="nativePreviewUrl" title="优丁内置预览（真实成片）" class="mb-4">
      <video :src="nativePreviewUrl" controls class="native-video" />
      <a-space wrap class="mt-3">
        <a-button v-if="handoffParams.srt_url" @click="openAsset(handoffParams.srt_url!)">
          下载英文字幕 SRT
        </a-button>
        <a-button v-if="nativePreviewUrl" @click="openAsset(handoffParams.output_url || handoffParams.video_url!)">
          新窗口打开成片
        </a-button>
      </a-space>
      <a-collapse v-if="segmentList.length" ghost class="mt-2">
        <a-collapse-panel key="seg" :header="`字幕轨 ${segmentList.length} 条`">
          <pre class="seg-pre">{{ segmentPreview }}</pre>
        </a-collapse-panel>
      </a-collapse>
    </a-card>

    <a-space class="mt-4">
      <a-button @click="router.push('/client/video-studio')">返回剪辑台</a-button>
      <a-button v-if="handoff.mediaTaskId" type="primary" @click="openStudioWithHandoff">
        查看当前项目
      </a-button>
      <a-button
        v-if="handoff.mediaTaskId && nativePreviewUrl"
        @click="goDistribute"
      >
        去内容分发
      </a-button>
    </a-space>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import {
  fetchMediaStudioCapabilities,
  fetchMediaStudioProject,
  type MediaStudioCapabilities,
  type MediaStudioProject,
} from '@/api/cross-border';
import { appendHandoffToUrl, type EditorHandoffParams } from '@/utils/mediaStudioHandoff';
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

const router = useRouter();
const route = useRoute();
const capabilities = ref<MediaStudioCapabilities | null>(null);
const studioProject = ref<MediaStudioProject | null>(null);
const handoffLoaded = ref(false);

const editorId = computed(() => String(route.meta.editorId || route.params.editorId || ''));

const editorMeta = computed(() => {
  const list = capabilities.value?.editors || [];
  return list.find((e) => e.id === editorId.value) || null;
});

const editorLabel = computed(() => editorMeta.value?.label || editorId.value || '剪辑器');
const embedUrl = computed(() => String(editorMeta.value?.embed_url || '').trim());

const pageTitle = computed(() => editorLabel.value);
const pageSubtitle = computed(() => {
  if (embedUrl.value) return '已连接外部部署实例';
  if (nativePreviewUrl.value) return '内置真实预览 · 外部编辑器未配置';
  return 'PoC 壳页 · 需运维配置嵌入地址';
});

const deployHint = computed(() => {
  const envKey = editorId.value === 'opencut' ? 'OPENCUT_EMBED_URL' : 'FLY_CUT_EMBED_URL';
  return `请在 backend .env 配置 ${envKey}。未配置时若有出海成片，仍可在本页内置预览与下载字幕。`;
});

const handoff = computed(() => ({
  mediaTaskId: String(route.query.media_task_id || ''),
}));

const handoffParams = computed((): EditorHandoffParams => {
  const proj = (studioProject.value?.project || {}) as Record<string, string>;
  return {
    media_task_id: handoff.value.mediaTaskId || undefined,
    video_url: studioProject.value?.result_url,
    output_url: proj.output_url || studioProject.value?.result_url,
    srt_url: proj.srt_url,
    script_en: proj.script_en,
    transcript_zh: proj.transcript_zh,
  };
});

const iframeSrc = computed(() => {
  if (!embedUrl.value) return '';
  return appendHandoffToUrl(embedUrl.value, handoffParams.value);
});

const nativePreviewUrl = computed(() => {
  const out = handoffParams.value.output_url || handoffParams.value.video_url;
  return out ? resolveMediaAssetUrl(out) : '';
});

const segmentList = computed(() => {
  const segs = (studioProject.value?.project as Record<string, unknown> | undefined)?.segments;
  return Array.isArray(segs) ? segs : [];
});

const segmentPreview = computed(() => {
  return segmentList.value
    .slice(0, 20)
    .map((s: Record<string, string>, i: number) => {
      const en = s.text_en || s.text || '';
      return `${i + 1}. ${s.start || ''} → ${s.end || ''}\n   ${en}`;
    })
    .join('\n');
});

const handoffSummary = computed(() => {
  const parts: string[] = [];
  if (handoffParams.value.output_url || handoffParams.value.video_url) parts.push('成片');
  if (handoffParams.value.srt_url) parts.push('SRT');
  if (segmentList.value.length) parts.push(`${segmentList.value.length} 条字幕轨`);
  return parts.length ? parts.join(' · ') : '';
});

function openAsset(path: string) {
  const url = resolveMediaAssetUrl(path);
  if (url) window.open(url, '_blank');
}

function openStudioWithHandoff() {
  void router.push({
    path: '/client/video-studio',
    query: { media_task_id: handoff.value.mediaTaskId },
  });
}

function goDistribute() {
  void router.push({
    path: '/client/distribute',
    query: { media_task_id: handoff.value.mediaTaskId },
  });
}

async function loadProject() {
  if (!handoff.value.mediaTaskId) {
    handoffLoaded.value = true;
    return;
  }
  try {
    studioProject.value = await fetchMediaStudioProject(handoff.value.mediaTaskId);
  } catch {
    message.warning('未能加载剪辑台项目，仅显示编辑器壳页');
  } finally {
    handoffLoaded.value = true;
  }
}

onMounted(async () => {
  try {
    capabilities.value = await fetchMediaStudioCapabilities();
  } catch {
    message.error('加载剪辑器配置失败');
  }
  await loadProject();
});
</script>

<style scoped>
.embed-shell {
  width: 100%;
  min-height: 72vh;
  border: 1px solid var(--yd-border, #e5e7eb);
  border-radius: 8px;
  overflow: hidden;
  background: #0f172a;
}
.embed-frame {
  width: 100%;
  height: 72vh;
  border: 0;
  display: block;
}
.native-video {
  width: 100%;
  max-height: 420px;
  border-radius: 8px;
  background: #000;
}
.seg-pre {
  font-size: 12px;
  white-space: pre-wrap;
  max-height: 240px;
  overflow: auto;
  margin: 0;
}
</style>
