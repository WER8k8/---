/**
 * 租户建站 — 上传产品白底图到平台存储（客户只需提供产品图，不生成装饰图）。
 */
import { getAuthToken } from '@/utils/api';

export interface UploadedProductImage {
  url: string;
  name: string;
}

export async function uploadSiteProductImages(files: File[]): Promise<UploadedProductImage[]> {
  const token = getAuthToken();
  const results: UploadedProductImage[] = [];

  for (const file of files) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/v1/files/upload', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    const body = await res.json();
    if (!res.ok) {
      const detail = body?.detail
      const reason =
        (typeof detail === 'object' && detail?.reason) ||
        body?.reason ||
        (typeof detail === 'string' ? detail : null)
      const msg =
        reason ||
        body?.message ||
        (typeof body?.detail === 'string' ? body.detail : null) ||
        '产品图上传失败'
      throw new Error(msg)
    }
    const data = body.data || body;
    const url = String(data.url || '');
    if (url) {
      results.push({ url, name: file.name });
    }
  }
  return results;
}

export function productImageUrls(images: UploadedProductImage[]): string[] {
  return images.map((i) => i.url).filter(Boolean);
}
