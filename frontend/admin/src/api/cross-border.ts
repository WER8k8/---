/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** 跨境语言桥 — W1/W2/W3 Client API */

import { apiGet, apiPatch, apiPost, authHeaders, fetchWithAuthRetry, getAuthToken } from '@/utils/api';

export type BridgeSummary = {
  summary_zh?: string;
  buyer_language?: string;
  intent_level?: string;
  key_asks?: string[];
  suggested_next?: string;
  needs_phone_call?: boolean;
  human_confirm_required?: boolean;
  mode?: string;
  mock_reason?: string;
  disclaimer?: string;
};

export type ReplyDraft = {
  subject_en?: string;
  body_en?: string;
  body_zh_backtranslation?: string;
  missing_info?: string[];
  human_confirm_required?: boolean;
  disclaimer?: string;
  mode?: string;
  mock_reason?: string;
};

export type InquiryBridgeStatus = {
  configured?: boolean;
  providers_available?: string[];
  mode?: 'live' | 'mock' | string;
  disclaimer?: string | null;
  env_hints?: string[];
  imap_inquiry?: {
    configured?: boolean;
    healthy?: boolean | null;
    smtp_disabled?: boolean;
  };
};

export type ImapPollResult = {
  ok?: boolean;
  ingested?: number;
  skipped?: number;
  polled?: number;
  probe_mode?: string;
  disclaimer?: string;
  smtp_disabled?: boolean;
  items?: Array<{ inquiry_id?: string; message_id?: string; from_email?: string }>;
};

export type ExportQuote = {
  ready?: boolean;
  error?: string;
  one_pager_zh?: string;
  pi?: { markdown?: string; pi_no?: string };
  honest_note?: string;
};

export type VideoDubResult = {
  ok?: boolean;
  partial?: boolean;
  error?: string;
  media_task_id?: string;
  script_en?: string;
  notes_zh?: string;
  transcript_zh?: string;
  segments?: Array<{ start?: string; end?: string; text_en?: string; text?: string }>;
  srt_url?: string;
  output_url?: string;
  audio_url?: string;
  output_mode?: string;
  tts_available?: boolean;
  hint?: string;
  warnings?: string[];
  video_duration_sec?: number;
  asr?: { backend?: string; ok?: boolean };
  track?: string;
  localization_provider?: string;
  localization_mode?: string;
  lip_sync?: boolean;
  voice_clone?: boolean;
  error_code?: string;
  tts_voice?: string;
  dub_voice_gender?: string;
  dub_voice_source?: string;
  target_lang?: string;
  target_lang_name?: string;
  target_lang_flag?: string;
  script_translated?: string;
  social_copy?: {
    title?: string;
    description?: string;
    tags?: string[];
    hashtags?: string;
  };
  distribute_platforms?: string[];
  distribution_status?: Record<string, any>;
};

export type ProductCandidate = {
  candidate_id: string;
  name: string;
  category_name_zh?: string;
  town_cluster?: string;
  notes?: string;
};

export type TranscribeResult = {
  ok?: boolean;
  text?: string;
  backend?: string;
  hint?: string;
  error?: string;
};

export function inquiryBridgeStatus() {
  return apiGet<InquiryBridgeStatus>('/cross-border/inquiries/bridge-status');
}

export type PipelineStage = { id: string; label: string; label_zh: string };

export type PipelineSummary = {
  stages?: PipelineStage[];
  counts?: Record<string, number>;
  total?: number;
  gw_task?: string;
};

export type GeoVisibilityDashboard = {
  ok?: boolean;
  tenant_domain?: string;
  unified_geo_schema?: string;
  llms_urls?: {
    llms_txt?: string | null;
    llms_full?: string | null;
    public_api_llms?: string | null;
    public_api_geo_score?: string | null;
  };
  scores?: { aeo_fact_score?: number; content_readiness?: number; geo_productization?: number };
  content_stats?: {
    masters_total?: number;
    masters_published?: number;
    faq_entries?: number;
    products_with_images?: number;
  };
  citations?: { mode?: string; note?: string };
  next_actions?: string[];
};

export type UnifiedGeoScore = {
  ok?: boolean;
  schema_version?: string;
  overall?: number;
  tenant_domain?: string;
  components?: Record<
    string,
    {
      score?: number | null;
      source?: string;
      weight?: number;
      detail?: Record<string, unknown>;
      mode?: string;
      note?: string;
    }
  >;
};

export function inquiryPipelineSummary() {
  return apiGet<PipelineSummary>('/cross-border/inquiries/pipeline/summary');
}

export function inquiryPipelineStageUpdate(
  inquiryId: string,
  payload: { stage: string; note?: string },
) {
  return apiPatch<{ pipeline_stage?: string; pipeline_stage_label?: string }>(
    `/cross-border/inquiries/${encodeURIComponent(inquiryId)}/pipeline-stage`,
    payload,
  );
}

export function fetchGeoVisibilityDashboard() {
  return apiGet<GeoVisibilityDashboard>('/cross-border/geo-visibility');
}

export function fetchUnifiedGeoScore(includeProbes = false) {
  const q = includeProbes ? '?include_probes=true' : '?include_probes=false';
  return apiGet<UnifiedGeoScore>(`/cross-border/unified-geo-score${q}`);
}

export function inquiryImapPoll(payload: {
  tenant_consent: boolean;
  compliance_acknowledged: boolean;
  max_messages?: number;
  mailbox?: string;
}) {
  return apiPost<ImapPollResult>('/cross-border/inquiries/imap-poll', payload);
}

export function inquiryBridgeSummary(inquiryId: string) {
  return apiPost<BridgeSummary>(
    `/cross-border/inquiries/${encodeURIComponent(inquiryId)}/bridge-summary`,
    {},
  );
}

export function inquiryReplyDraft(inquiryId: string, bossReplyZh: string, tone = 'professional') {
  return apiPost<ReplyDraft>(
    `/cross-border/inquiries/${encodeURIComponent(inquiryId)}/reply-draft`,
    { boss_reply_zh: bossReplyZh, tone },
  );
}

export function fetchExportQuote(params?: Record<string, string | number | undefined>) {
  const qs = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') qs.set(k, String(v));
    });
  }
  const q = qs.toString();
  return apiGet<ExportQuote>(`/cross-border/export-quote${q ? `?${q}` : ''}`);
}

export function postExportQuote(body: Record<string, unknown>) {
  return apiPost<ExportQuote>('/cross-border/export-quote', body);
}

export function previewSeoKeywords() {
  return apiGet<Record<string, unknown>>('/cross-border/seo-keywords/preview');
}

export function seedSeoKeywords(beltId = 'all') {
  return apiPost<Record<string, unknown>>('/cross-border/seo-keywords/seed', {
    belt_id: beltId,
    include_ranking: true,
  });
}

export async function uploadVideoForDub(file: File): Promise<Record<string, unknown>> {
  const fd = new FormData();
  fd.append('file', file);
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetchWithAuthRetry('/api/v1/cross-border/video-dub/upload', {
    method: 'POST',
    headers,
    body: fd,
  });
  let json: Record<string, unknown> = {};
  try {
    json = (await res.json()) as Record<string, unknown>;
  } catch {
    throw new Error(res.ok ? '上传响应解析失败' : `上传失败 (HTTP ${res.status})`);
  }
  if (!res.ok) {
    throw new Error(String(json.message || json.detail || '上传失败'));
  }
  if (typeof json.code === 'number' && json.code !== 0) {
    throw new Error(String(json.message || '上传失败'));
  }
  if (json.code === 0 && json.data !== undefined) return json.data as Record<string, unknown>;
  return json;
}

export type CrossBorderJobStatus = {
  job_id: string;
  kind: 'transcribe' | 'dub' | 'premium';
  status: 'queued' | 'running' | 'done' | 'failed';
  progress: number;
  media_task_id?: string;
  text?: string;
  backend?: string;
  hint?: string;
  error?: string;
  events?: Array<{ progress?: number; hint?: string; ts?: string }>;
  result?: TranscribeResult & VideoDubResult;
  script_en?: string;
  transcript_zh?: string;
  srt_url?: string;
  output_url?: string;
  audio_url?: string;
  output_mode?: string;
  dispatch?: string;
  track?: string;
  localization_provider?: string;
  localization_mode?: string;
  lip_sync?: boolean;
  error_code?: string;
};

const JOB_TERMINAL = new Set(['done', 'failed']);

export type VideoDubTtsStatus = {
  edge_tts_available: boolean;
  default_voice: string;
  default_voice_male?: string;
  default_voice_female?: string;
  ffmpeg_available: boolean;
};

export function fetchVideoDubTtsStatus() {
  return apiGet<VideoDubTtsStatus>('/cross-border/video-dub/tts-status');
}

function hasDubArtifacts(s: CrossBorderJobStatus | VideoDubResult): boolean {
  return Boolean(s.srt_url || s.audio_url || s.script_en || s.output_url);
}

function normalizeDubJobResult(
  final: CrossBorderJobStatus,
  payload: { output_mode?: string },
): VideoDubResult {
  const r = (final.result || final) as VideoDubResult;
  const hint = final.hint || r.hint || r.error || '生成失败';
  const dubIncomplete =
    payload.output_mode === 'dub' && r.output_mode && r.output_mode !== 'english_dub';

  if (final.status === 'failed' || r.ok === false) {
    if (hasDubArtifacts(final) || hasDubArtifacts(r)) {
      return {
        ok: true,
        partial: true,
        ...r,
        script_en: r.script_en || final.script_en,
        transcript_zh: r.transcript_zh || final.transcript_zh,
        srt_url: r.srt_url || final.srt_url,
        output_url: r.output_url || final.output_url,
        audio_url: r.audio_url || final.audio_url,
        output_mode: r.output_mode || final.output_mode,
        hint: hint || '成片未完全生成，可下载已有文件后继续',
      };
    }
    throw new Error(hint);
  }

  if (dubIncomplete) {
    if (hasDubArtifacts(r)) {
      return {
        ok: true,
        partial: true,
        ...r,
        hint: r.hint || '英文配音视频未合成，可下载 MP3/SRT 用剪映替换音轨',
      };
    }
    throw new Error(r.hint || '英文配音未合成到视频，请查看提示或下载 MP3');
  }

  return { ok: true, ...r };
}

function parseSseJobPayload(line: string): CrossBorderJobStatus | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith('data:')) return null;
  const raw = trimmed.slice(5).trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CrossBorderJobStatus;
  } catch {
    return null;
  }
}

/** SSE 推送任务进度（带 Authorization，失败时抛错由调用方降级轮询）。 */
export async function watchCrossBorderJobViaSse(
  jobId: string,
  opts?: { onProgress?: (s: CrossBorderJobStatus) => void; timeoutMs?: number },
): Promise<CrossBorderJobStatus> {
  const timeoutMs = opts?.timeoutMs ?? 600_000;
  const token = getAuthToken();
  const headers: Record<string, string> = { Accept: 'text/event-stream' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchWithAuthRetry(
      `/api/v1/cross-border/video-dub/jobs/${encodeURIComponent(jobId)}/events`,
      { headers, signal: controller.signal },
    );
    if (!res.ok) throw new Error(`SSE 连接失败 (HTTP ${res.status})`);
    const reader = res.body?.getReader();
    if (!reader) throw new Error('SSE 无响应体');
    const decoder = new TextDecoder();
    let buffer = '';
    let last: CrossBorderJobStatus | null = null;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        const snap = parseSseJobPayload(line);
        if (!snap) continue;
        last = snap;
        opts?.onProgress?.(snap);
        if (JOB_TERMINAL.has(snap.status)) return snap;
      }
    }
    if (last && JOB_TERMINAL.has(last.status)) return last;
    throw new Error('SSE 流已结束但任务未完成');
  } finally {
    clearTimeout(timer);
  }
}

export function fetchCrossBorderJob(jobId: string) {
  return apiGet<CrossBorderJobStatus>(`/cross-border/video-dub/jobs/${encodeURIComponent(jobId)}`);
}

export async function pollCrossBorderJob(
  jobId: string,
  opts?: { intervalMs?: number; timeoutMs?: number; onProgress?: (s: CrossBorderJobStatus) => void },
): Promise<CrossBorderJobStatus> {
  try {
    return await watchCrossBorderJobViaSse(jobId, opts);
  } catch {
    /* SSE 不可用时降级轮询 */
  }
  const intervalMs = opts?.intervalMs ?? 2000;
  const timeoutMs = opts?.timeoutMs ?? 600_000;
  const started = Date.now();
  for (;;) {
    const snap = await fetchCrossBorderJob(jobId);
    opts?.onProgress?.(snap);
    if (JOB_TERMINAL.has(snap.status)) return snap;
    if (Date.now() - started > timeoutMs) {
      throw new Error('任务超时，请稍后在任务列表重试或手动粘贴解说词');
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

export async function enqueueTranscribeJob(mediaTaskId: string) {
  return apiPost<CrossBorderJobStatus>('/cross-border/video-dub/transcribe', {
    media_task_id: mediaTaskId,
  });
}

export async function transcribeVideo(
  mediaTaskId: string,
  onProgress?: (s: CrossBorderJobStatus) => void,
): Promise<TranscribeResult> {
  const enqueued = await enqueueTranscribeJob(mediaTaskId);
  const jobId = enqueued.job_id;
  if (!jobId) throw new Error('听写入队失败');
  const final = await pollCrossBorderJob(jobId, { onProgress });
  if (final.status === 'failed') {
    return {
      ok: false,
      error: final.error,
      hint: final.hint || final.error || '听写失败',
    };
  }
  const r = final.result || final;
  return {
    ok: true,
    text: r.text || final.text,
    backend: r.backend || final.backend,
    hint: r.hint || final.hint,
  };
}

export type SupportedLanguage = {
  code: string;
  name: string;
  en_name: string;
  flag: string;
};

export function fetchSupportedLanguages() {
  return apiGet<{ languages: SupportedLanguage[] }>('/cross-border/video-dub/languages');
}

export function autoDistributeDubVideo(
  mediaTaskId: string,
  platforms: string[],
  socialCopy?: Record<string, any>,
  videoUrl?: string,
) {
  return apiPost<{ media_task_id: string; distribution: Record<string, any> }>(
    '/cross-border/video-dub/auto-distribute',
    {
      media_task_id: mediaTaskId,
      platforms,
      social_copy: socialCopy,
      video_url: videoUrl,
    },
  );
}

export async function runOneClickOverseas(
  payload: {
    media_task_id: string;
    transcript_zh?: string;
    voice_consent?: boolean;
    output_mode?: 'subtitle' | 'dub' | 'burn';
    dub_voice_gender?: 'auto' | 'male' | 'female';
    track?: 'standard' | 'opensource_premium' | 'vozo';
    localization_provider?: string;
    target_lang?: string;
    voice_clone?: boolean;
    lip_sync?: boolean;
    distribute_platforms?: string[];
  },
  onProgress?: (s: CrossBorderJobStatus) => void,
): Promise<VideoDubResult> {
  return createVideoDubJob(
    {
      media_task_id: payload.media_task_id,
      transcript_zh: payload.transcript_zh,
      voice_consent: payload.voice_consent,
      output_mode: payload.output_mode,
      auto_asr: !payload.transcript_zh?.trim(),
      dub_voice_gender: payload.dub_voice_gender || 'auto',
      track: payload.track || 'standard',
      localization_provider: payload.localization_provider,
      target_lang: payload.target_lang || 'en',
      voice_clone: payload.voice_clone ?? true,
      lip_sync: payload.lip_sync ?? true,
      distribute_platforms: payload.distribute_platforms,
    },
    onProgress,
  );
}

export async function runPremiumOverseas(
  payload: {
    media_task_id: string;
    transcript_zh?: string;
    voice_consent?: boolean;
    output_mode?: 'subtitle' | 'dub' | 'burn';
    dub_voice_gender?: 'auto' | 'male' | 'female';
    track?: 'opensource_premium' | 'vozo';
    localization_provider?: string;
    target_lang?: string;
    voice_clone?: boolean;
    lip_sync?: boolean;
    distribute_platforms?: string[];
  },
  onProgress?: (s: CrossBorderJobStatus) => void,
): Promise<VideoDubResult> {
  const enqueued = await apiPost<CrossBorderJobStatus>('/cross-border/video-dub/premium-jobs', {
    media_task_id: payload.media_task_id,
    transcript_zh: payload.transcript_zh,
    voice_consent: payload.voice_consent,
    output_mode: payload.output_mode || 'dub',
    track: payload.track || 'opensource_premium',
    localization_provider: payload.localization_provider,
    dub_voice_gender: payload.dub_voice_gender || 'auto',
    target_lang: payload.target_lang || 'en',
    voice_clone: payload.voice_clone ?? true,
    lip_sync: payload.lip_sync ?? true,
    distribute_platforms: payload.distribute_platforms,
  });
  const jobId = enqueued.job_id;
  if (!jobId) throw new Error('精品出海入队失败');
  const final = await pollCrossBorderJob(jobId, { onProgress });
  if (final.status === 'failed') {
    throw new Error(final.hint || final.error || '精品出海失败');
  }
  const r = (final.result || final) as VideoDubResult;
  if (r.ok === false) {
    throw new Error(r.hint || r.error_code || '精品出海失败');
  }
  if (!r.output_url && !r.srt_url) {
    throw new Error(r.hint || '精品轨未返回成片或字幕，禁止假成功');
  }
  return { ok: true, ...r };
}

export async function createVideoDubJob(
  payload: {
    media_task_id: string;
    transcript_zh?: string;
    voice_consent?: boolean;
    output_mode?: string;
    auto_asr?: boolean;
    tts_voice?: string;
    dub_voice_gender?: 'auto' | 'male' | 'female';
    track?: string;
    localization_provider?: string;
    target_lang?: string;
    voice_clone?: boolean;
    lip_sync?: boolean;
    distribute_platforms?: string[];
  },
  onProgress?: (s: CrossBorderJobStatus) => void,
): Promise<VideoDubResult> {
  const enqueued = await apiPost<CrossBorderJobStatus>('/cross-border/video-dub/jobs', payload);
  const jobId = enqueued.job_id;
  if (!jobId) throw new Error('出海任务入队失败');
  const final = await pollCrossBorderJob(jobId, { onProgress });
  return normalizeDubJobResult(final, payload);
}

export function fetchProductCandidates(params?: {
  category_id?: string;
  search?: string;
  page?: number;
}) {
  return apiGet<{
    items: ProductCandidate[];
    total: number;
    categories: Array<{ id: string; name: string }>;
    honest_note?: string;
    pm_review_status?: string;
  }>('/cross-border/product-candidates', params);
}

export function importProductCandidates(candidateIds: string[]) {
  return apiPost<{
    imported_count: number;
    skipped_count: number;
    honest_note?: string;
  }>('/cross-border/product-candidates/import', { candidate_ids: candidateIds });
}

export type MediaStudioAsrEngine = {
  id: string;
  label: string;
  mode: string;
  configured?: boolean;
  preferred?: boolean;
  status?: string;
  doc?: string | null;
};

export type MediaStudioCapabilities = {
  product_id: string;
  pipeline: Array<{ step: string; label: string; route: string }>;
  asr: {
    engines: MediaStudioAsrEngine[];
    primary: string | null;
    chain_order: string[];
  };
  editors: Array<{
    id: string;
    label: string;
    status: string;
    stack?: string;
    route?: string;
    github?: string;
    embed_url?: string | null;
    configured?: boolean;
    access_note?: string | null;
  }>;
  localization?: Array<{
    id: string;
    label: string;
    status: string;
    configured?: boolean;
    lip_sync?: boolean;
    voice_clone?: boolean;
    visual_translate?: boolean;
    api_doc?: string;
    github?: string;
    access_note?: string;
  }>;
  tts: { available?: boolean; voice?: string; hint?: string };
  recommended?: {
    standard: string;
    open_premium_lip: string;
    open_premium_dub: string;
    open_subtitle_premium: string;
    open_short_drama: string;
    saas_premium: string;
    active_opensource_id?: string | null;
    active_opensource_label?: string | null;
    pick_order?: string[];
  };
};

export function fetchMediaStudioCapabilities() {
  return apiGet<MediaStudioCapabilities>('/cross-border/media-studio/capabilities');
}

export type MediaStudioProject = {
  media_task_id: string;
  title?: string;
  result_url?: string;
  project?: Record<string, unknown>;
  latest_dub?: Record<string, unknown> | null;
  latest_premium?: Record<string, unknown> | null;
  updated_at?: string;
};

export function fetchMediaStudioProject(mediaTaskId: string) {
  return apiGet<MediaStudioProject>(
    `/cross-border/media-studio/projects/${encodeURIComponent(mediaTaskId)}`,
  );
}

export function saveMediaStudioProject(
  mediaTaskId: string,
  body: Record<string, unknown>,
) {
  return apiPost<MediaStudioProject>(
    `/cross-border/media-studio/projects/${encodeURIComponent(mediaTaskId)}`,
    body,
  );
}
