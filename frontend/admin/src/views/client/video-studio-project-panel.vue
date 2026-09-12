<template>
  <a-card v-if="studio" title="当前项目" size="small" class="mb-4" :loading="loading">
    <template #extra>
      <a-tag v-if="trackLabel" :color="trackColor">{{ trackLabel }}</a-tag>
    </template>

    <a-descriptions size="small" :column="1" bordered class="mb-3">
      <a-descriptions-item label="任务">
        {{ studio.title || studio.media_task_id?.slice(0, 8) + '…' }}
      </a-descriptions-item>
      <a-descriptions-item v-if="project.asr_backend" label="听写引擎">
        {{ project.asr_backend }}
      </a-descriptions-item>
      <a-descriptions-item v-if="project.localization_provider" label="本地化">
        {{ providerLabel(String(project.localization_provider || '')) }}
      </a-descriptions-item>
      <a-descriptions-item v-if="studio.updated_at || project.updated_at" label="保存时间">
        {{ formatTime(String(studio.updated_at || project.updated_at || '')) }}
      </a-descriptions-item>
      <a-descriptions-item v-if="segmentCount" label="字幕轨">
        {{ segmentCount }} 条英文片段
      </a-descriptions-item>
    </a-descriptions>

    <div v-if="outputVideoUrl" class="mb-3">
      <p class="text-sm font-medium mb-1">成片预览</p>
      <video :src="outputVideoUrl" controls class="project-video" />
    </div>

    <a-space wrap class="mb-3">
      <a-button v-if="project.srt_url" size="small" @click="openAsset(String(project.srt_url))">
        下载英文字幕
      </a-button>
      <a-button v-if="project.output_url" size="small" @click="openAsset(String(project.output_url))">
        打开成片
      </a-button>
      <a-button size="small" type="primary" @click="emit('distribute')">去内容分发</a-button>
      <a-button v-if="studio?.media_task_id" size="small" @click="emit('openEditor', 'fly_cut')">
        Fly-Cut 剪辑
      </a-button>
      <a-button v-if="studio?.media_task_id" size="small" @click="emit('openEditor', 'opencut')">
        OpenCut 剪辑
      </a-button>
    </a-space>

    <a-collapse v-if="project.transcript_zh || project.script_en" ghost>
      <a-collapse-panel v-if="project.transcript_zh" key="zh" header="中文听写稿">
        <pre class="script-block">{{ project.transcript_zh }}</pre>
      </a-collapse-panel>
      <a-collapse-panel v-if="project.script_en" key="en" header="英文脚本">
        <pre class="script-block">{{ project.script_en }}</pre>
      </a-collapse-panel>
    </a-collapse>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { MediaStudioCapabilities, MediaStudioProject } from '@/api/cross-border';
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

const props = defineProps<{
  studio: MediaStudioProject | null;
  capabilities?: MediaStudioCapabilities | null;
  loading?: boolean;
}>();

const emit = defineEmits<{ distribute: []; openEditor: [id: string] }>();

const project = computed(() => {
  const p = props.studio?.project;
  return p && typeof p === 'object' ? (p as Record<string, unknown>) : {};
});

const segmentCount = computed(() => {
  const segs = project.value.segments;
  return Array.isArray(segs) ? segs.length : 0;
});

const outputVideoUrl = computed(() => {
  const url = String(project.value.output_url || props.studio?.result_url || '');
  return url ? resolveMediaAssetUrl(url) : '';
});

const trackLabel = computed(() => {
  const prov = project.value.localization_provider;
  if (!prov) {
    if (props.studio?.latest_premium) return '精品轨';
    if (props.studio?.latest_dub) return '标准出海';
    return '';
  }
  if (prov === 'vozo_ai') return 'Vozo 精品';
  return '开源精品';
});

const trackColor = computed(() => (trackLabel.value.includes('精品') ? 'purple' : 'blue'));

function providerLabel(id: string) {
  const row = props.capabilities?.localization?.find((l) => l.id === id);
  return row?.label || id;
}

function formatTime(iso?: string) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function openAsset(path: string) {
  const url = resolveMediaAssetUrl(path);
  if (url) window.open(url, '_blank');
}
</script>

<style scoped>
.project-video {
  width: 100%;
  max-height: 280px;
  border-radius: 8px;
  background: #000;
}
.script-block {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  max-height: 200px;
  overflow: auto;
}
</style>
