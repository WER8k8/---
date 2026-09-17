/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="全媒体剪辑台" subtitle="听写 · 翻译 · 多轨剪辑 · 分发" surface="elevated">
    <a-alert
      type="info"
      show-icon
      class="mb-4"
      message="一键出海完成后可在此校对字幕、查看引擎状态；Fly-Cut / OpenCut 等专业剪辑器将按阶段嵌入。"
    />

    <a-steps :current="pipelineStep" class="mb-6" size="small">
      <a-step v-for="s in capabilities?.pipeline || defaultPipeline" :key="s.step" :title="s.label" />
    </a-steps>

    <a-row :gutter="[16, 16]" class="mb-4">
      <a-col :xs="24" :md="12">
        <a-card title="快捷操作" size="small">
          <a-space direction="vertical" style="width: 100%">
            <a-button type="primary" block @click="router.push('/client/video-overseas')">
              去一键出海
            </a-button>
            <a-button
              block
              :disabled="!handoff.mediaTaskId"
              @click="openOverseasWithHandoff"
            >
              继续当前项目（出海页）
            </a-button>
            <a-button block @click="router.push('/client/distribute')">去内容分发</a-button>
          </a-space>
          <p v-if="handoff.mediaTaskId" class="text-xs text-gray-500 mt-3 mb-0">
            任务 ID：{{ handoff.mediaTaskId.slice(0, 8) }}…
            <span v-if="handoff.asrBackend"> · 听写：{{ handoff.asrBackend }}</span>
          </p>
        </a-card>
      </a-col>
      <a-col :xs="24" :md="12">
        <a-card title="英文配音" size="small">
          <p v-if="capabilities?.tts?.available" class="text-sm text-green-700 mb-2">
            edge-tts 可用（{{ capabilities.tts.voice || '默认音色' }}）
          </p>
          <p v-else class="text-sm text-amber-700 mb-2">
            {{ capabilities?.tts?.hint || '配音引擎未就绪' }}
          </p>
        </a-card>
      </a-col>
    </a-row>

    <VideoStudioProjectPanel
      v-if="handoff.mediaTaskId"
      :studio="studioProject"
      :capabilities="capabilities"
      :loading="projectLoading"
      @distribute="goDistribute"
      @open-editor="openEditorById"
    />

    <a-card title="听写引擎（ASR）" class="mb-4" :loading="loading">
      <a-table
        :columns="asrColumns"
        :data-source="asrRows"
        :pagination="false"
        size="small"
        row-key="id"
      />
    </a-card>

    <a-card title="智能推荐栈" class="mb-4" :loading="loading">
      <a-descriptions v-if="capabilities?.recommended" size="small" :column="1" bordered>
        <a-descriptions-item label="日常标准轨">
          {{ capabilities.recommended.standard }}（讯飞→LLM→edge-tts）
        </a-descriptions-item>
        <a-descriptions-item label="开源口型精品">
          {{ capabilities.recommended.open_premium_lip }}
        </a-descriptions-item>
        <a-descriptions-item label="开源配音集成">
          {{ capabilities.recommended.open_premium_dub }}
        </a-descriptions-item>
        <a-descriptions-item label="当前可激活开源">
          <a-tag v-if="capabilities.recommended.active_opensource_id" color="success">
            {{ capabilities.recommended.active_opensource_label }}
          </a-tag>
          <span v-else class="text-gray-500">未部署 GPU sidecar（可用内置真实链）</span>
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <a-card title="本地化引擎" class="mb-4" :loading="loading">
      <a-list :data-source="capabilities?.localization || []" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.label">
              <template #description>
                <span>
                  {{ item.lip_sync ? '含口型同步' : '无口型' }}
                  <span v-if="item.voice_clone"> · 克隆配音</span>
                  · {{ statusLabel(item.status) }}
                </span>
                <a
                  v-if="item.github"
                  :href="item.github"
                  target="_blank"
                  rel="noopener"
                  class="ml-2"
                >
                  GitHub
                </a>
                <a
                  v-if="item.api_doc"
                  :href="item.api_doc"
                  target="_blank"
                  rel="noopener"
                  class="ml-2"
                >
                  API 文档
                </a>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a-tag :color="item.configured ? 'success' : 'default'">
                {{ item.configured ? '已配置' : item.access_note || '未配置' }}
              </a-tag>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card title="Web 剪辑适配器" :loading="loading">
      <a-list :data-source="capabilities?.editors || []" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :title="item.label">
              <template #description>
                <span>{{ item.stack }} · {{ statusLabel(item.status) }}</span>
                <a v-if="item.github" :href="item.github" target="_blank" rel="noopener" class="ml-2">
                  GitHub
                </a>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a-tag v-if="item.status === 'integrated'" color="success">已集成</a-tag>
              <a-tag v-else-if="item.status === 'planned'" color="processing">排期中</a-tag>
              <a-tag v-else color="default">评估</a-tag>
              <a-button
                v-if="item.route"
                type="link"
                size="small"
                @click="openEditor(item)"
              >
                {{ item.configured ? '打开' : '查看 PoC' }}
              </a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
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
import VideoStudioProjectPanel from '@/views/client/video-studio-project-panel.vue';

const router = useRouter();
const route = useRoute();
const loading = ref(true);
const projectLoading = ref(false);
const capabilities = ref<MediaStudioCapabilities | null>(null);
const studioProject = ref<MediaStudioProject | null>(null);

const defaultPipeline = [
  { step: 'upload', label: '上传中文片' },
  { step: 'one_click', label: '一键出海' },
  { step: 'studio', label: '进阶剪辑' },
  { step: 'distribute', label: '内容分发' },
];

const handoff = computed(() => ({
  mediaTaskId: String(route.query.media_task_id || ''),
  asrBackend: String(route.query.asr_backend || ''),
}));

const pipelineStep = computed(() => {
  if (handoff.value.mediaTaskId) return 2;
  return 0;
});

const asrColumns = [
  { title: '引擎', dataIndex: 'label', key: 'label' },
  { title: '模式', dataIndex: 'mode', key: 'mode' },
  {
    title: '状态',
    key: 'configured',
    customRender: ({ record }: { record: { configured?: boolean; status?: string } }) =>
      record.configured ? '已配置' : record.status === 'planned' ? '规划中' : '未配置',
  },
];

const asrRows = computed(() => capabilities.value?.asr?.engines || []);

function statusLabel(status?: string) {
  if (status === 'integrated') return '已集成';
  if (status === 'planned') return '排期中';
  if (status === 'eval') return '评估中';
  return status || '—';
}

function openOverseasWithHandoff() {
  if (!handoff.value.mediaTaskId) return;
  void router.push({
    path: '/client/video-overseas',
    query: {
      media_task_id: handoff.value.mediaTaskId,
      asr_backend: handoff.value.asrBackend || undefined,
    },
  });
}

function openEditor(item: { route?: string; id?: string }) {
  if (!item.route) return;
  void router.push({
    path: item.route,
    query: handoff.value.mediaTaskId
      ? { media_task_id: handoff.value.mediaTaskId }
      : undefined,
  });
}

function openEditorById(id: string) {
  const routes: Record<string, string> = {
    fly_cut: '/client/video-editor/fly-cut',
    opencut: '/client/video-editor/opencut',
  };
  const path = routes[id];
  if (!path) return;
  openEditor({ route: path, id });
}

function goDistribute() {
  void router.push({
    path: '/client/distribute',
    query: handoff.value.mediaTaskId
      ? { media_task_id: handoff.value.mediaTaskId }
      : undefined,
  });
}

async function loadStudioProject() {
  if (!handoff.value.mediaTaskId) {
    studioProject.value = null;
    return;
  }
  projectLoading.value = true;
  try {
    studioProject.value = await fetchMediaStudioProject(handoff.value.mediaTaskId);
  } catch {
    studioProject.value = null;
  } finally {
    projectLoading.value = false;
  }
}

onMounted(async () => {
  try {
    capabilities.value = await fetchMediaStudioCapabilities();
    await loadStudioProject();
  } catch {
    message.error('加载剪辑台能力失败');
  } finally {
    loading.value = false;
  }
});
</script>
