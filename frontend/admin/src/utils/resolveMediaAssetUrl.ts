/** 媒体 URL：相对路径补 origin；外链走同源代理，避免 WebView ORB */
export function resolveMediaAssetUrl(url: string): string {
  const raw = (url || '').trim();
  if (!raw) return '';

  if (/^https?:\/\//i.test(raw)) {
    return `/api/v1/files/asset-proxy?url=${encodeURIComponent(raw)}`;
  }

  const path = raw.startsWith('/') ? raw : `/${raw}`;
  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}${path}`;
  }
  return path;
}
