/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="优丁出海视音频数字人工厂"
    subtitle="中文视频/产品实拍 → 多语种专业翻译 + 零样本原声克隆 + 神经嘴型对齐 → 全网社媒矩阵分发"
    surface="elevated"
  >
    <!-- 顶部状态提示与能力徽标 -->
    <a-alert
      v-if="envHint"
      type="warning"
      show-icon
      class="mb-4"
      :message="envHint"
    />

    <div class="feature-banner mb-4">
      <div class="feature-item">
        <span class="feature-icon">🎙️</span>
        <div class="feature-text">
          <strong>零样本原声克隆</strong>
          <span>提取说话人声纹，讲地道外语</span>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">👄</span>
        <div class="feature-text">
          <strong>神经嘴型对齐</strong>
          <span>驱动唇部关键点，声画合一</span>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">🌍</span>
        <div class="feature-text">
          <strong>12 大出海目标语</strong>
          <span>英/阿/西/俄/葡等建材专业术语</span>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">🚀</span>
        <div class="feature-text">
          <strong>全网 50+ 矩阵分发</strong>
          <span>YouTube / TikTok / Reels 一键推流</span>
        </div>
      </div>
    </div>

    <a-card title="视音频本土化出海工坊" class="mb-4">
      <div class="vo-layout">
        <!-- 左侧参数与控制配置 -->
        <div class="vo-main">
          <!-- 步骤一：上传视频 -->
          <input ref="fileRef" type="file" accept="video/*" class="hidden" @change="onFilePick" />
          <div class="step-section mb-4">
            <div class="step-title">① 选择产品或实拍视频</div>
            <a-space wrap class="mt-2">
              <a-button type="primary" ghost :loading="uploading" @click="fileRef?.click()">
                📂 上传中文视频
              </a-button>
              <span v-if="uploadName" class="text-sm font-medium text-slate-700">{{ uploadName }}</span>
              <a-tag v-if="mediaTaskId" color="success">视频已就绪</a-tag>
            </a-space>
          </div>

          <!-- 步骤二：目标出海国家语言 -->
          <div class="step-section mb-4">
            <div class="step-title">② 目标出海国家语言</div>
            <div class="mt-2">
              <a-select
                v-model:value="targetLang"
                style="width: 100%"
                size="large"
                placeholder="选择目标出海语言"
              >
                <a-select-option
                  v-for="item in languagesList"
                  :key="item.code"
                  :value="item.code"
                >
                  <span class="mr-2">{{ item.flag }}</span>
                  <span class="font-medium mr-2">{{ item.name }}</span>
                  <span class="text-xs text-slate-400">({{ item.en_name }})</span>
                </a-select-option>
              </a-select>
            </div>
          </div>

          <!-- 步骤三：出海视音频黑科技开关 -->
          <div class="step-section mb-4">
            <div class="step-title">③ 视音频本土化核心配置</div>
            <div class="options-grid mt-2">
              <!-- 声线克隆开关 -->
              <div class="option-card" :class="{ active: voiceClone }">
                <div class="option-header">
                  <span class="option-name">🎙️ 零样本原声音色克隆</span>
                  <a-switch v-model:checked="voiceClone" />
                </div>
                <div class="option-desc">
                  自动提取原片中说话人的干音声纹特征，用客户本人音色与语气说出流利外语。
                </div>
              </div>

              <!-- 嘴型对齐开关 -->
              <div class="option-card" :class="{ active: lipSync }">
                <div class="option-header">
                  <span class="option-name">👄 神经元嘴型对齐 (Lip-Sync)</span>
                  <a-switch v-model:checked="lipSync" />
                </div>
                <div class="option-desc">
                  精确驱动面部唇部关键点，让人脸嘴型完全贴合外语发音节奏，彻底告别假唱违和感。
                </div>
              </div>
            </div>

            <!-- 输出模式 -->
            <div class="mt-3">
              <p class="text-xs text-slate-500 mb-1">合成成片类型：</p>
              <a-radio-group v-model:value="outputMode">
                <a-radio-button value="dub">高清配音成片 (替换音轨/口型对齐)</a-radio-button>
                <a-radio-button value="burn">烧录字幕成片 (含外文字幕)</a-radio-button>
                <a-radio-button value="subtitle">仅生成双语 SRT 字幕</a-radio-button>
              </a-radio-group>
            </div>
          </div>

          <!-- 步骤四：矩阵分发平台预勾选 -->
          <div class="step-section mb-4">
            <div class="step-title">④ 全网出海社媒矩阵分发（可选）</div>
            <div class="mt-2">
              <a-checkbox-group v-model:value="distributePlatforms" class="platform-checkbox-group">
                <a-checkbox value="youtube">
                  <span class="platform-tag">🔴 YouTube Shorts</span>
                </a-checkbox>
                <a-checkbox value="tiktok">
                  <span class="platform-tag">🎵 TikTok</span>
                </a-checkbox>
                <a-checkbox value="instagram">
                  <span class="platform-tag">📸 Instagram Reels</span>
                </a-checkbox>
                <a-checkbox value="facebook">
                  <span class="platform-tag">📘 Facebook Video</span>
                </a-checkbox>
                <a-checkbox value="linkedin">
                  <span class="platform-tag">💼 LinkedIn Video</span>
                </a-checkbox>
              </a-checkbox-group>
              <p class="text-xs text-slate-500 mt-1 mb-0">
                生成成片时将由 AI 同步撰写高权重 SEO 爆款标题、帖子简介与行业 Hashtags。
              </p>
            </div>
          </div>

          <!-- 确认框 -->
          <a-checkbox v-model:checked="voiceConsent" class="mb-4 block">
            我确认视频内容真实合规，授权进行多语种原声克隆与数字人嘴型对齐。
          </a-checkbox>

          <!-- 核心执行按钮 -->
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

          <!-- 进度条 -->
          <div v-if="processing || processingPremium" class="mt-3">
            <a-progress :percent="jobProgress" :status="jobProgress >= 100 ? 'success' : 'active'" stroke-color="#4a9b8c" />
            <p v-if="jobHint" class="text-xs text-teal-700 font-medium mt-1">{{ jobHint }}</p>
          </div>

          <!-- 高级解说词微调折叠区 -->
          <a-collapse v-if="mediaTaskId" ghost class="mt-4">
            <a-collapse-panel key="adv" header="📝 高级选项：微调中文解说词（可选）">
              <a-textarea
                v-model:value="transcriptZh"
                :rows="3"
                placeholder="默认自动听写整段视频。如需定制原片讲稿，可在此粘贴或修改中文解说词。"
              />
            </a-collapse-panel>
          </a-collapse>

          <!-- 生成成果交付面板 -->
          <div v-if="result" class="mt-4 deliverable-card">
            <div class="flex items-center justify-between mb-2">
              <h4 class="m-0 text-base font-semibold text-slate-800">🎉 出海视音频成果已就绪</h4>
              <a-space>
                <a-tag v-if="result.voice_clone" color="cyan">原声克隆已生效</a-tag>
                <a-tag v-if="result.lip_sync" color="green">嘴型对齐已生效</a-tag>
                <a-tag color="blue">{{ currentLangMeta.flag }} {{ currentLangMeta.name }}</a-tag>
              </a-space>
            </div>

            <!-- 警告与提示 -->
            <a-alert
              v-for="(w, i) in result.warnings || []"
              :key="i"
              type="info"
              show-icon
              :message="w"
              class="mb-2 text-xs"
            />

            <!-- 多语种译文稿 -->
            <div class="mb-3">
              <div class="text-xs font-semibold text-slate-700 mb-1">
                【{{ currentLangMeta.name }}】配音解说稿：
              </div>
              <pre class="script-box">{{ result.script_translated || result.script_en }}</pre>
            </div>

            <!-- 社媒矩阵 SEO 文案 -->
            <div v-if="result.social_copy" class="social-copy-box mb-3">
              <div class="text-xs font-semibold text-teal-800 mb-1 flex items-center justify-between">
                <span>🚀 海外社媒 SEO 爆款文案 (YouTube / TikTok / Reels)</span>
                <a-button type="link" size="small" @click="copySocialCopy">复制全部文案</a-button>
              </div>
              <div class="text-xs text-slate-700 mb-1">
                <strong>标题：</strong> {{ result.social_copy.title }}
              </div>
              <div class="text-xs text-slate-600 mb-1">
                <strong>简介：</strong> {{ result.social_copy.description }}
              </div>
              <div class="text-xs text-teal-700 font-mono">
                {{ result.social_copy.hashtags }}
              </div>
            </div>

            <!-- 操作按钮群 -->
            <a-space wrap class="mt-2">
              <a-button v-if="result.output_url" type="primary" @click="openUrl(result.output_url)">
                📥 下载出海高清成片
              </a-button>
              <a-button v-if="result.audio_url" @click="openUrl(result.audio_url)">
                🎵 下载克隆音频 MP3
              </a-button>
              <a-button v-if="result.srt_url" @click="openUrl(result.srt_url)">
                📄 下载双语 SRT 字幕
              </a-button>
              <a-button
                v-if="distributePlatforms.length > 0 && result.output_url"
                type="default"
                :loading="distributing"
                @click="triggerMatrixDistribute"
              >
                🚀 一键推向 {{ distributePlatforms.length }} 个社媒平台
              </a-button>
              <a-button type="dashed" @click="goStudio">进阶剪辑台</a-button>
            </a-space>
            <p class="text-xs text-teal-800 font-medium mt-2">{{ result.hint }}</p>
          </div>
        </div>

        <!-- 右侧视音频对比播放器 -->
        <div class="vo-previews">
          <!-- 原片播放器 -->
          <div class="preview-panel">
            <div class="flex items-center justify-between mb-2">
              <span class="preview-label">🇨🇳 原视频 (中文实拍)</span>
              <a-tag v-if="sourcePreviewUrl" color="default">源视频</a-tag>
            </div>
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
              <span>请先在左侧选择产品视频</span>
            </div>
          </div>

          <!-- 成品播放器 -->
          <div class="preview-panel preview-panel--result">
            <div class="flex items-center justify-between mb-2">
              <span class="preview-label">{{ outputPreviewTitle }}</span>
              <a-tag v-if="result?.lip_sync" color="success">嘴型已对齐</a-tag>
            </div>
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
            <div v-else-if="processing || processingPremium" class="preview-empty">
              <a-spin />
              <span class="mt-2 text-white">{{ jobHint || '正在进行原声克隆与神经嘴型对齐…' }}</span>
            </div>
            <div v-else-if="!result" class="preview-empty">
              <span class="preview-empty__icon">🎬</span>
              <span>点击「一键开始出海」后在此试听试看</span>
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
  autoDistributeDubVideo,
  fetchMediaStudioCapabilities,
  fetchSupportedLanguages,
  fetchVideoDubTtsStatus,
  runOneClickOverseas,
  runPremiumOverseas,
  saveMediaStudioProject,
  uploadVideoForDub,
  type MediaStudioCapabilities,
  type SupportedLanguage,
  type VideoDubResult,
} from '@/api/cross-border';
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

const router = useRouter();
const fileRef = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const processing = ref(false);
const processingPremium = ref(false);
const distributing = ref(false);
const capabilities = ref<MediaStudioCapabilities | null>(null);
const uploadName = ref('');
const mediaTaskId = ref('');
const transcriptZh = ref('');
const voiceConsent = ref(true);

// 12 大出海目标国家语言列表
const defaultLanguages: SupportedLanguage[] = [
  { code: 'en', name: '英语', en_name: 'English', flag: '🇺🇸' },
  { code: 'ar', name: '阿拉伯语', en_name: 'Arabic', flag: '🇸🇦' },
  { code: 'es', name: '西班牙语', en_name: 'Spanish', flag: '🇪🇸' },
  { code: 'ru', name: '俄语', en_name: 'Russian', flag: '🇷🇺' },
  { code: 'pt', name: '葡萄牙语', en_name: 'Portuguese', flag: '🇧🇷' },
  { code: 'fr', name: '法语', en_name: 'French', flag: '🇫🇷' },
  { code: 'de', name: '德语', en_name: 'German', flag: '🇩🇪' },
  { code: 'ja', name: '日语', en_name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: '韩语', en_name: 'Korean', flag: '🇰🇷' },
  { code: 'vi', name: '越南语', en_name: 'Vietnamese', flag: '🇻🇳' },
  { code: 'id', name: '印尼语', en_name: 'Indonesian', flag: '🇮🇩' },
  { code: 'th', name: '泰语', en_name: 'Thai', flag: '🇹🇭' },
];
const languagesList = ref<SupportedLanguage[]>(defaultLanguages);
const targetLang = ref('en');

// 核心特性开关
const voiceClone = ref(true);
const lipSync = ref(true);
const outputMode = ref<'dub' | 'burn' | 'subtitle'>('dub');
const distributePlatforms = ref<string[]>(['youtube', 'tiktok', 'instagram']);

const jobProgress = ref(0);
const jobHint = ref('');
const result = ref<VideoDubResult | null>(null);
const envHint = ref('');
const sourceVideoUrl = ref('');
const localPreviewUrl = ref('');

const currentLangMeta = computed(() => {
  return languagesList.value.find((l) => l.code === targetLang.value) || defaultLanguages[0];
});

const sourcePreviewUrl = computed(() => sourceVideoUrl.value || localPreviewUrl.value);
const outputPreviewUrl = computed(() =>
  result.value?.output_url ? resolveMediaAssetUrl(result.value.output_url) : '',
);
const audioPreviewUrl = computed(() =>
  result.value?.audio_url ? resolveMediaAssetUrl(result.value.audio_url) : '',
);

const oneClickLabel = computed(() => {
  const lang = currentLangMeta.value.name;
  return `🚀 一键生成【${lang}】出海视频（原声克隆+嘴型对齐）`;
});

const outputPreviewTitle = computed(() => {
  if (outputPreviewUrl.value) {
    const lang = currentLangMeta.value.name;
    if (result.value?.lip_sync) return `✨ ${currentLangMeta.value.flag} ${lang}神经嘴型对齐成片`;
    if (result.value?.voice_clone) return `🎙️ ${currentLangMeta.value.flag} ${lang}原声克隆成片`;
    return `🎬 ${currentLangMeta.value.flag} ${lang}出海成片`;
  }
  if (result.value?.srt_url) return '原片（待叠加字幕）';
  if (processing.value) return '生成中…';
  return '目标语言成片预览';
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
      message.success('产品视频已就绪，可一键开始出海！');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '上传失败';
    message.error(
      msg === 'Failed to fetch' || /network|timeout/i.test(msg)
        ? '上传失败：请确认开发后台运行中'
        : msg,
    );
  } finally {
    uploading.value = false;
    input.value = '';
  }
}

async function runOneClick() {
  if (!mediaTaskId.value) {
    message.warning('请先选择或上传视频');
    return;
  }
  if (!voiceConsent.value) {
    message.warning('生成外语配音与原声克隆需勾选确认授权');
    return;
  }
  processing.value = true;
  jobProgress.value = 5;
  jobHint.value = `任务已入队，开始【${currentLangMeta.value.name}】听写、翻译与原声克隆…`;
  result.value = null;

  try {
    const res = await runOneClickOverseas(
      {
        media_task_id: mediaTaskId.value,
        transcript_zh: transcriptZh.value.trim() || undefined,
        voice_consent: voiceConsent.value,
        output_mode: outputMode.value,
        target_lang: targetLang.value,
        voice_clone: voiceClone.value,
        lip_sync: lipSync.value,
        distribute_platforms: distributePlatforms.value,
      },
      (snap) => {
        jobProgress.value = snap.progress ?? 0;
        jobHint.value = snap.hint || '';
      },
    );
    result.value = res;
    if (res.transcript_zh) transcriptZh.value = res.transcript_zh;
    await persistStudioProject(res);

    if (res.lip_sync && res.voice_clone) {
      message.success(`【${currentLangMeta.value.name}】出海成片已生成：原声克隆与嘴型对齐均生效！`);
    } else if (res.output_url) {
      message.success(`【${currentLangMeta.value.name}】出海成片已生成，请在右侧预览试看！`);
    } else {
      message.success('多语种字幕与音频已生成，可下载使用！');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '生成出海成片失败');
  } finally {
    processing.value = false;
    jobProgress.value = 0;
    jobHint.value = '';
  }
}

async function triggerMatrixDistribute() {
  if (!mediaTaskId.value || !result.value?.output_url) {
    message.warning('请先生成出海成片');
    return;
  }
  if (!distributePlatforms.value.length) {
    message.warning('请至少勾选一个海外社媒平台');
    return;
  }
  distributing.value = true;
  try {
    await autoDistributeDubVideo(
      mediaTaskId.value,
      distributePlatforms.value,
      result.value.social_copy,
      result.value.output_url,
    );
    message.success(`已成功投递至 ${distributePlatforms.value.join(', ')} 全网分发矩阵！`);
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '分发失败');
  } finally {
    distributing.value = false;
  }
}

function copySocialCopy() {
  if (!result.value?.social_copy) return;
  const { title, description, hashtags } = result.value.social_copy;
  const text = `${title || ''}\n\n${description || ''}\n\n${hashtags || ''}`;
  navigator.clipboard.writeText(text);
  message.success('已复制海外社媒爆款文案与 Hashtags 到剪贴板');
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
    const langData = await fetchSupportedLanguages();
    if (langData.languages?.length) {
      languagesList.value = langData.languages;
    }
  } catch {
    /* 保持默认 12 语种 */
  }

  try {
    capabilities.value = await fetchMediaStudioCapabilities();
  } catch {
    /* 非阻塞 */
  }

  try {
    const tts = await fetchVideoDubTtsStatus();
    if (outputMode.value === 'dub' && !tts.ffmpeg_available) {
      envHint.value = '提示：当前后台未检测到 ffmpeg，视频混流与嘴型合成需依赖 ffmpeg。';
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
.feature-banner {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 900px) {
  .feature-banner {
    grid-template-columns: repeat(2, 1fr);
  }
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f0fdf9;
  border: 1px solid #ccfbf1;
  border-radius: 8px;
  padding: 10px 14px;
}
.feature-icon {
  font-size: 24px;
}
.feature-text {
  display: flex;
  flex-direction: column;
}
.feature-text strong {
  font-size: 13px;
  color: #0f766e;
}
.feature-text span {
  font-size: 11px;
  color: #64748b;
}

.vo-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 46%);
  gap: 24px;
  align-items: start;
}
@media (max-width: 1024px) {
  .vo-layout {
    grid-template-columns: 1fr;
  }
}

.step-section {
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 16px;
}
.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 640px) {
  .options-grid {
    grid-template-columns: 1fr;
  }
}
.option-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  background: #f8fafc;
  transition: all 0.2s ease;
}
.option-card.active {
  border-color: #4a9b8c;
  background: #f0fdf9;
}
.option-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.option-name {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}
.option-desc {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.platform-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.platform-tag {
  font-size: 12px;
  font-weight: 500;
}

.deliverable-card {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 16px;
}
.social-copy-box {
  background: #f0fdf9;
  border: 1px solid #99f6e4;
  border-radius: 8px;
  padding: 12px;
}

.vo-previews {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.preview-panel {
  border: 1px solid #334155;
  border-radius: 10px;
  background: #0f172a;
  padding: 14px;
}
.preview-panel--result {
  border-color: #0d9488;
}
.preview-label {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}
.preview-video {
  display: block;
  width: 100%;
  max-height: 240px;
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
  min-height: 160px;
  padding: 14px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  border: 1px dashed #334155;
  border-radius: 6px;
  background: #111827;
}
.preview-empty__icon {
  font-size: 28px;
  opacity: 0.6;
}
.script-box {
  white-space: pre-wrap;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px;
  font-size: 12px;
  max-height: 140px;
  overflow: auto;
  color: #334155;
}
</style>
