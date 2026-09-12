/** 租户站产品 slug · L-Pro 路由用 */

export interface TenantCatalogProduct {
  name: string;
  summary?: string;
  description?: string;
  image?: string;
  imageAlt?: string;
  slug?: string;
  sku?: string;
  category?: string;
  specs?: Array<{ label: string; value: string }>;
  downloadUrl?: string;
  videoUrl?: string;
  videoTitle?: string;
  videoUpdatedAt?: string;
}

export function slugifyTenantSegment(value: string): string {
  const base = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return base || 'item';
}

export function productSlug(item: TenantCatalogProduct, index: number): string {
  if (item.slug?.trim()) return slugifyTenantSegment(item.slug);
  if (item.sku?.trim()) return slugifyTenantSegment(item.sku);
  return slugifyTenantSegment(item.name) || `p-${index}`;
}

export function categorySlug(name: string): string {
  return slugifyTenantSegment(name);
}

export function normalizeCatalogProducts(raw: unknown): TenantCatalogProduct[] {
  if (!Array.isArray(raw)) return [];
  const items: TenantCatalogProduct[] = [];
  raw.forEach((row, index) => {
    if (!row || typeof row !== 'object') return;
    const o = row as Record<string, unknown>;
    const name = String(o.name || '').trim();
    if (!name) return;
    const specsRaw = o.specs;
    const specs = Array.isArray(specsRaw)
      ? specsRaw
          .filter((s) => s && typeof s === 'object')
          .map((s) => {
            const spec = s as Record<string, unknown>;
            return {
              label: String(spec.label || ''),
              value: String(spec.value || ''),
            };
          })
          .filter((s) => s.label && s.value)
      : undefined;
    const item: TenantCatalogProduct = {
      name,
      summary: o.summary ? String(o.summary) : undefined,
      description: o.description ? String(o.description) : undefined,
      image: o.image ? String(o.image) : undefined,
      imageAlt: o.imageAlt ? String(o.imageAlt) : (o.alt_text ? String(o.alt_text) : undefined),
      slug: o.slug ? String(o.slug) : undefined,
      sku: o.sku ? String(o.sku) : undefined,
      category: o.category ? String(o.category) : undefined,
      specs,
      downloadUrl: o.downloadUrl ? String(o.downloadUrl) : undefined,
      videoUrl: o.videoUrl ? String(o.videoUrl) : (o.video_url ? String(o.video_url) : undefined),
      videoTitle: o.videoTitle ? String(o.videoTitle) : (o.video_title ? String(o.video_title) : undefined),
      videoUpdatedAt: o.videoUpdatedAt ? String(o.videoUpdatedAt) : (o.video_updated_at ? String(o.video_updated_at) : undefined),
    };
    items.push({ ...item, slug: productSlug(item, index) });
  });
  return items;
}

export function findProductBySlug(
  products: TenantCatalogProduct[],
  slug: string,
): TenantCatalogProduct | undefined {
  const key = slugifyTenantSegment(slug);
  return products.find((p, i) => productSlug(p, i) === key);
}
