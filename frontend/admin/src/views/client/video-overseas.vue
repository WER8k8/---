<template>
  <YdPage title="中文片出海" subtitle="选视频 → 一键出海" surface="elevated">
    <a-alert
      v-if="envHint"
      type="warning"
      show-icon
      class="mb-4"
      :message="envHint"
    />

    <a-alert
      type="info"
      show-icon
      class="mb-4"
      message="上传中文产品片 → 自动听写 → 译成英文。选「英文 AI 配音」会用英文朗读替换原中文解说（不是克隆你的声音，也不是保留原声）。发送前请看右侧「英文配音版」预览。"
    />

    <a-card title="一键出海" class="mb-4">
      <div class="vo-layout">
        <div class="vo-main">
          <input ref="fileRef" type="file" accept="video/*" class="hidden" @change="onFilePick" />
          <a-space wrap class="mb-3">
            <a-button type="default" :loading="uploading" @click="fileRef?.click()">① 选择视频</a-button>
            <span v-if="uploadName" class="text-sm text-gray-600">{{ uploadName }}</span>
            <a-tag v-if="mediaTaskId" color="success">已上传</a-tag>
          </a-space>

          <a-radio-group v-model:value="outputMode" class="mb-3">
            <a-radio-button value="subtitle">英文字幕</a-radio-button>
            <a-radio-button value="dub">英文 AI 配音</a-radio-button>
          </a-radio-group>

          <div v-if="outputMode === 'dub'" class="mb-3">
            <p class="text-sm text-gray-600 mb-1">英文 AI 音色（非克隆原声）</p>
            <a-radio-group v-model:value="dubVoiceGender">
              <a-radio-button value="auto">自动男/女声</a-radio-button>
              <a-radio-button value="male">英文男声</a-radio-button>
              <a-radio-button value="female">英文女声</a-radio-button>
            </a-radio-group>
            <p class="text-xs text-gray-500 mt-1 mb-0">
              标准轨为 edge-tts 英文朗读，只替换解说词，不保留中文原声、不克隆声线。
            </p>
          </div>

          <a-checkbox v-model:checked="voiceConsent" class="mb-4 block">
            我确认内容真实，同意生成英文配音/字幕（发送前人工核对）
          </a-checkbox>

          <a-button
            type="primary"
            size="large"
            block
            :loading="processing"
            :disabled="!mediaTaskId || uploading"
            @click="runOneClick"
          >
            {{ oneClickLabel }}
          </a-button>

          <a-button
            v-if="premiumAvailable"
            type="default"
            size="large"
            block
            class="mt-3"
            :loading="processingPremium"
            :disabled="!mediaTaskId || uploading || processing"
            @click="runPremium"
          >
            {{ premiumButtonLabel }}
          </a-button>
          <p v-if="premiumHint" class="text-xs text-gray-500 mt-1 mb-0">{{ premiumHint }}</p>

          <div v-if="processing || processingPremium" class="mt-3">
            <a-progress :percent="jobProgress" :status="jobProgress >= 100 ? 'success' : 'active'" />
            <p v-if="jobHint" class="text-xs text-gray-500 mt-1">{{ jobHint }}</p>
          </div>

          <a-collapse v-if="mediaTaskId" ghost class="mt-4">
            <a-collapse-panel key="adv" header="高级：手动改中文解说词（可选）">
              <a-alert
                v-if="shortManualTranscript"
                type="warning"
                show-icon
                class="mb-2"
                message="高级区只有短短几句时，系统会优先对整段视频听写；若只想改个别句子，请先听写完成再编辑全文。"
              />
              <a-textarea
                v-model:value="transcriptZh"
                :rows="4"
                placeholder="留空 = 自动听写整段视频。若只填一两句，长视频会重新整段听写，避免成片只有几秒配音。"
              />
            </a-collapse-panel>
          </a-collapse>

          <div v-if="result" class="mt-4 space-y-2">
            <a-alert
              v-if="result.partial"
              type="warning"
              show-icon
              :message="result.hint || '成片未完全生成，可先下载已有文件继续'"
              class="mb-2"
            />
            <a-alert
              v-for="(w, i) in result.warnings || []"
              :key="i"
              type="warning"
              show-icon
              :message="w"
              class="mb-2"
            />
            <p v-if="result.transcript_zh" class="text-xs text-gray-600">
              中文：{{ result.transcript_zh.slice(0, 120) }}{{ result.transcript_zh.length > 120 ? '…' : '' }}
            </p>
            <p class="text-sm font-medium">英文解说稿</p>
            <pre class="script-box">{{ result.script_en }}</pre>
            <a-space wrap>
              <a-button v-if="result.srt_url" @click="openUrl(result.srt_url)">下载 SRT</a-button>
              <a-button v-if="result.output_url" @click="openUrl(result.output_url)">新窗口打开</a-button>
              <a-button v-if="result.audio_url" @click="openUrl(result.audio_url)">下载配音 MP3</a-button>
              <a-button type="primary" ghost @click="goStudio">进阶剪辑台</a-button>
              <a-button @click="router.push('/client/distribute')">去内容分发 →</a-button>
            </a-space>
            <p class="text-xs text-amber-700">{{ result.hint }}</p>
          </div>
        </div>

        <div class="vo-previews">
          <div class="preview-panel">
            <p class="preview-label">原片</p>
            <video
              v-if="sourcePreviewUrl"
              :key="sourcePreviewUrl"
              class="preview-video"
              :src="sourcePreviewUrl"
              controls
              playsinline
              preload="metadata"
            />
            <div v-else class="preview-empty">
              <span class="preview-empty__icon">▶</span>
              <span>先选择视频</span>
            </div>
          </div>

          <div class="preview-panel">
            <p class="preview-label">{{ outputPreviewTitle }}</p>
            <video
              v-if="outputPreviewUrl"
              :key="outputPreviewUrl"
              class="preview-video"
              :src="outputPreviewUrl"
              controls
              playsinline
              preload="metadata"
            />
            <video
              v-else-if="result && sourcePreviewUrl && result.srt_url && !outputPreviewUrl"
              class="preview-video"
              :src="sourcePreviewUrl"
              controls
              playsinline
              preload="metadata"
            />
            <audio
              v-if="audioPreviewUrl && !outputPreviewUrl"
              class="preview-audio mt-2"
              :src="audioPreviewUrl"
              controls
              preload="metadata"
            />
            <p
              v-if="result && !outputPreviewUrl && result.srt_url"
              class="text-xs text-amber-200 mt-2"
            >
              仅生成 SRT，画面未烧录；可下载后用剪映叠加。
            </p>
            <div v-else-if="processing || processingPremium" class="preview-empty">
              <a-spin />
              <span class="mt-2">{{ jobHint || '处理中…' }}</span>
            </div>
            <div v-else-if="!result" class="preview-empty">
              <span class="preview-empty__icon">🎬</span>
              <span>一键出海完成后在此预览</span>
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import {
  fetchMediaStudioCapabilities,
  fetchVideoDubTtsStatus,
  runOneClickOverseas,
  runPremiumOverseas,
  saveMediaStudioProject,
  uploadVideoForDub,
  type MediaStudioCapabilities,
  type VideoDubResult,
} from '@/api/cross-border';
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

const router = useRouter();
const fileRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const processing = ref(false);
const processingPremium = ref(false);
const capabilities = ref<MediaStudioCapabilities | null>(null);
const uploadName = ref('');
const mediaTaskId = ref('');
const transcriptZh = ref('');
const shortManualTranscript = computed(() => {
  const t = transcriptZh.value.trim();
  return t.length > 0 && t.length < 150;
});
const voiceConsent = ref(false);
const outputMode = ref<'subtitle' | 'dub'>('dub');
const dubVoiceGender = ref<'auto' | 'male' | 'female'>('auto');
const jobProgress = ref(0);
const jobHint = ref('');
const result = ref<VideoDubResult | null>(null);
const envHint = ref('');
const sourceVideoUrl = ref('');
const localPreviewUrl = ref('');

const sourcePreviewUrl = computed(() => sourceVideoUrl.value || localPreviewUrl.value);
const outputPreviewUrl = computed(() =>
  result.value?.output_url ? resolveMediaAssetUrl(result.value.output_url) : '',
);
const audioPreviewUrl = computed(() =>
  result.value?.audio_url ? resolveMediaAssetUrl(result.value.audio_url) : '',
);

const oneClickLabel = computed(() =>
  outputMode.value === 'dub' ? '② 一键出海（听写+英文配音）' : '② 一键出海（听写+英文字幕）',
);

const premiumAvailable = computed(() => {
  const rec = capabilities.value?.recommended;
  return Boolean(rec?.active_opensource_id) || Boolean(
    capabilities.value?.localization?.some((x) => x.id === 'vozo_ai' && x.configured),
  );
});

const premiumButtonLabel = computed(() => {
  const activeId = capabilities.value?.recommended?.active_opensource_id;
  const active = capabilities.value?.recommended?.active_opensource_label;
  if (activeId === 'youding_self_hosted') return '③ 真实英文配音（内置链·无口型）';
  if (active) return `③ 精品出海（${active}）`;
  return '③ 精品出海（口型/声线克隆，可选）';
});

const premiumHint = computed(() => {
  const activeId = capabilities.value?.recommended?.active_opensource_id;
  if (!premiumAvailable.value) {
    return '需配置听写+ffmpeg+edge-tts；口型精品需 Linly/V2VT 等真实 GPU sidecar';
  }
  if (activeId === 'youding_self_hosted') {
    return '与②相同：讯飞/Whisper 听写 → LLM 英译 → edge-tts 英文 AI 朗读（非克隆）';
  }
  if (activeId) {
    return '开源精品轨，可能含声线克隆/口型；若只要英文 AI 朗读请用上方②';
  }
  return '商业 Vozo 精品轨';
});

const outputPreviewTitle = computed(() => {
  if (outputPreviewUrl.value) {
    const mode = result.value?.output_mode || '';
    if (mode.includes('lip') || result.value?.lip_sync) return '精品口型版';
    if (mode.includes('dub') || mode === 'english_dub') return '英文 AI 配音版（看这里）';
    if (mode.startsWith('opensource') || mode.startsWith('vozo')) return '精品出海版';
    return '字幕烧录版';
  }
  if (result.value?.srt_url) return '原片（待叠加字幕）';
  if (processing.value) return '生成中';
  return '成品';
});

function revokeLocalPreview() {
  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value);
    localPreviewUrl.value = '';
  }
}

function setLocalPreview(file: File) {
  revokeLocalPreview();
  localPreviewUrl.value = URL.createObjectURL(file);
}

async function onFilePick(ev: Event) {
  const input = ev.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  uploadName.value = file.name;
  setLocalPreview(file);
  result.value = null;
  mediaTaskId.value = '';
  sourceVideoUrl.value = '';
  uploading.value = true;
  try {
    const data = await uploadVideoForDub(file);
    mediaTaskId.value = String(data.id || data.media_task_id || '');
    const src = String(data.src || data.result_url || '');
    if (src) {
      sourceVideoUrl.value = resolveMediaAssetUrl(src);
      revokeLocalPreview();
    }
    if (!mediaTaskId.value) {
      message.warning('上传完成但未拿到任务编号，请重试');
    } else {
      message.success('视频已就绪，可点「一键出海」');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '上传失败';
    message.error(
      msg === 'Failed to fetch' || /network|timeout/i.test(msg)
        ? '上传失败：请用 http://127.0.0.1:5173 并确认后台已启动'
        : msg,
    );
  } finally {
    uploading.value = false;
    input.value = '';
  }
}

async function runOneClick() {
  if (!mediaTaskId.value) {
    message.warning('请先选择视频');
    return;
  }
  if (outputMode.value === 'dub' && !voiceConsent.value) {
    message.warning('英文配音需勾选确认');
    return;
  }
  processing.value = true;
  jobProgress.value = 0;
  jobHint.value = '已入队，听写+生成一次完成…';
  result.value = null;
  try {
    const res = await runOneClickOverseas(
      {
        media_task_id: mediaTaskId.value,
        transcript_zh: transcriptZh.value.trim() || undefined,
        voice_consent: voiceConsent.value,
        output_mode: outputMode.value,
        dub_voice_gender: dubVoiceGender.value,
      },
      (snap) => {
        jobProgress.value = snap.progress ?? 0;
        jobHint.value = snap.hint || '';
      },
    );
    result.value = res;
    if (res.transcript_zh) transcriptZh.value = res.transcript_zh;
    await persistStudioProject(res);
    if (res.warnings?.length) {
      message.warning(res.warnings.join(' '));
    }
    if (res.partial) {
      message.warning(res.hint || '部分生成成功，请下载文件或重试合成视频');
    } else if (outputMode.value === 'dub' && res.output_mode === 'english_dub') {
      message.success('一键出海完成：右侧为英文配音版，请试听');
    } else if (res.output_url) {
      message.success('一键出海完成，请在右侧预览成品');
    } else {
      message.success('字幕文件已生成，可下载 SRT');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '一键出海失败');
  } finally {
    processing.value = false;
    jobProgress.value = 0;
    jobHint.value = '';
  }
}

async function runPremium() {
  if (!mediaTaskId.value) {
    message.warning('请先选择视频');
    return;
  }
  if (!voiceConsent.value) {
    message.warning('精品出海需勾选配音确认');
    return;
  }
  const track = capabilities.value?.recommended?.active_opensource_id
    ? 'opensource_premium'
    : 'vozo';
  processingPremium.value = true;
  jobProgress.value = 0;
  jobHint.value = '精品轨处理中…';
  result.value = null;
  try {
    const res = await runPremiumOverseas(
      {
        media_task_id: mediaTaskId.value,
        transcript_zh: transcriptZh.value.trim() || undefined,
        voice_consent: voiceConsent.value,
        output_mode: 'dub',
        dub_voice_gender: dubVoiceGender.value,
        track,
        localization_provider: capabilities.value?.recommended?.active_opensource_id || undefined,
      },
      (snap) => {
        jobProgress.value = snap.progress ?? 0;
        jobHint.value = snap.hint || '';
      },
    );
    result.value = res;
    if (res.transcript_zh) transcriptZh.value = res.transcript_zh;
    await persistStudioProject(res);
    message.success(res.lip_sync ? '精品口型版已生成，请试听' : '精品配音版已生成，请试听');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '精品出海失败');
  } finally {
    processingPremium.value = false;
    jobProgress.value = 0;
    jobHint.value = '';
  }
}

async function persistStudioProject(res: VideoDubResult) {
  if (!mediaTaskId.value) return;
  try {
    await saveMediaStudioProject(mediaTaskId.value, {
      transcript_zh: res.transcript_zh,
      script_en: res.script_en,
      srt_url: res.srt_url,
      output_url: res.output_url,
      segments: res.segments,
      asr_backend: res.asr?.backend,
      localization_provider: res.localization_provider,
    });
  } catch {
    /* 非阻塞 */
  }
}

function openUrl(path: string) {
  const url = resolveMediaAssetUrl(path);
  if (url) window.open(url, '_blank');
}

function goStudio() {
  void router.push({
    path: '/client/video-studio',
    query: {
      media_task_id: mediaTaskId.value || undefined,
      asr_backend: result.value?.asr?.backend || undefined,
    },
  });
}

onMounted(async () => {
  try {
    capabilities.value = await fetchMediaStudioCapabilities();
  } catch {
    /* 标准轨仍可用 */
  }
  try {
    const tts = await fetchVideoDubTtsStatus();
    const hints: string[] = [];
    if (outputMode.value === 'dub' && !tts.ffmpeg_available) {
      hints.push('当前后台未检测到 ffmpeg，英文配音视频无法合成。请重启开发后台或安装 ffmpeg。');
    }
    if (outputMode.value === 'dub' && !tts.edge_tts_available) {
      hints.push('edge-tts 未安装：请在 backend 执行 pip install -U edge-tts>=7.2.7 并重启 API。');
    }
    if (hints.length) {
      envHint.value = `${hints.join(' ')}可先切「英文字幕」或下载 MP3/SRT。`;
    }
  } catch {
    /* 非阻塞 */
  }
});

onBeforeUnmount(revokeLocalPreview);
</script>

<style scoped>
.hidden {
  display: none;
}
.vo-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 44%);
  gap: 20px;
  align-items: start;
}
@media (max-width: 960px) {
  .vo-layout {
    grid-template-columns: 1fr;
  }
}
.vo-previews {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.preview-panel {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #0f172a;
  padding: 12px;
}
.preview-label {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
}
.preview-video {
  display: block;
  width: 100%;
  max-height: 220px;
  border-radius: 6px;
  background: #000;
}
.preview-audio {
  display: block;
  width: 100%;
}
.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 140px;
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  border: 1px dashed #334155;
  border-radius: 6px;
  background: #111827;
}
.preview-empty__icon {
  font-size: 24px;
  opacity: 0.5;
}
.script-box {
  white-space: pre-wrap;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  max-height: 160px;
  overflow: auto;
}
</style>
