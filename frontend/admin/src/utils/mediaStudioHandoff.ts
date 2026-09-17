/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { resolveMediaAssetUrl } from '@/utils/resolveMediaAssetUrl';

export type EditorHandoffParams = {
  media_task_id?: string;
  video_url?: string;
  output_url?: string;
  srt_url?: string;
  script_en?: string;
  transcript_zh?: string;
};

export function buildEditorHandoffQuery(params: EditorHandoffParams): Record<string, string> {
  const q: Record<string, string> = {};
  if (params.media_task_id) q.media_task_id = params.media_task_id;
  const video = params.output_url || params.video_url;
  if (video) {
    const abs = resolveMediaAssetUrl(video);
    if (abs) q.video_url = abs;
  }
  if (params.srt_url) {
    const abs = resolveMediaAssetUrl(params.srt_url);
    if (abs) q.srt_url = abs;
  }
  if (params.script_en) q.script_en = params.script_en.slice(0, 2000);
  if (params.transcript_zh) q.transcript_zh = params.transcript_zh.slice(0, 2000);
  return q;
}

export function appendHandoffToUrl(base: string, params: EditorHandoffParams): string {
  const q = buildEditorHandoffQuery(params);
  const keys = Object.keys(q);
  if (!keys.length) return base;
  const sep = base.includes('?') ? '&' : '?';
  const query = keys.map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(q[k])}`).join('&');
  return `${base}${sep}${query}`;
}
