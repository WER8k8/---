/** 租户媒体空间 — 产品图片 / 视频共用 files API 与七牛·R2 分轨存储 */

import type { RouteLocationNormalizedLoaded } from 'vue-router';

export type TenantMediaSpaceKind = 'image' | 'video';

export interface TenantMediaSpaceConfig {
  kind: TenantMediaSpaceKind;
  title: string;
  subtitle: string;
  clientPath: string;
  uploadCardTitle: string;
  uploadAccept: string;
  allowedExtensions: readonly string[];
  maxUploadMb: number;
  defaultFileType: 'image' | 'video';
  dropzoneHint: string;
}

export const TENANT_IMAGE_SPACE: TenantMediaSpaceConfig = {
  kind: 'image',
  title: '产品图片空间',
  subtitle: '上传与管理产品白底图，建站、产品页与多平台发布统一复用',
  clientPath: '/client/product-images',
  uploadCardTitle: '上传产品图片',
  uploadAccept: '.jpg,.jpeg,.png,.webp,.gif,.svg',
  allowedExtensions: ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'],
  maxUploadMb: 50,
  defaultFileType: 'image',
  dropzoneHint: '支持 JPG/PNG/WebP/GIF/SVG，单文件最大 50MB',
};

export const TENANT_VIDEO_SPACE: TenantMediaSpaceConfig = {
  kind: 'video',
  title: '视频空间',
  subtitle: '上传与管理产品/宣传视频，与产品图片共用国内七牛 / 海外 R2 存储链路',
  clientPath: '/client/video-space',
  uploadCardTitle: '上传视频',
  uploadAccept: '.mp4,.webm,.avi,.mov,.mkv,.flv,.wmv',
  allowedExtensions: ['mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'wmv'],
  maxUploadMb: 500,
  defaultFileType: 'video',
  dropzoneHint: '支持 MP4/WebM/MOV 等常见视频格式，单文件最大 500MB',
};

const SPACE_BY_KIND: Record<TenantMediaSpaceKind, TenantMediaSpaceConfig> = {
  image: TENANT_IMAGE_SPACE,
  video: TENANT_VIDEO_SPACE,
};

export function resolveTenantMediaSpaceFromRoute(
  route: RouteLocationNormalizedLoaded,
): TenantMediaSpaceConfig | null {
  if (route.meta.videoSpaceMode || route.path.includes('/client/video-space')) {
    return TENANT_VIDEO_SPACE;
  }
  if (route.meta.productImageSpaceMode || route.path.includes('/client/product-images')) {
    return TENANT_IMAGE_SPACE;
  }
  const kind = route.meta.tenantMediaSpaceKind as TenantMediaSpaceKind | undefined;
  if (kind && SPACE_BY_KIND[kind]) {
    return SPACE_BY_KIND[kind];
  }
  return null;
}

export function tenantMediaSpacePath(
  kind: TenantMediaSpaceKind,
  isClientShell: boolean,
): string {
  const cfg = SPACE_BY_KIND[kind];
  return isClientShell ? cfg.clientPath : kind === 'image' ? '/admin/file-manager' : '/admin/video-space';
}
