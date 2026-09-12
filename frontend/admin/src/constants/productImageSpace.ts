/** 产品图片空间 — 租户建站 / 超管运营共用（LOGIN-LOCK 相关路径见 file-manager） */

export {
  TENANT_IMAGE_SPACE,
  TENANT_VIDEO_SPACE,
  resolveTenantMediaSpaceFromRoute,
  tenantMediaSpacePath,
} from '@/constants/tenantMediaSpace';

export const PRODUCT_IMAGE_SPACE_TITLE = '产品图片空间';

export const PRODUCT_IMAGE_SPACE_SUBTITLE =
  '上传与管理产品白底图，建站、产品页与多平台发布统一复用';

export const PRODUCT_IMAGE_SPACE_PATH_ADMIN = '/admin/file-manager';

export const PRODUCT_IMAGE_SPACE_PATH_CLIENT = '/client/product-images';

export function productImageSpacePath(isClientShell: boolean): string {
  return isClientShell ? PRODUCT_IMAGE_SPACE_PATH_CLIENT : PRODUCT_IMAGE_SPACE_PATH_ADMIN;
}
