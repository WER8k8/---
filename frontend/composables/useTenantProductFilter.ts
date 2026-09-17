/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { computed, ref, type Ref } from 'vue';
import { categorySlug, productSlug, type TenantCatalogProduct } from '../utils/tenant-product-slug';

export type TenantProductListItem = TenantCatalogProduct & { slug: string };

export type ProductSortKey = 'default' | 'name-asc' | 'name-desc';

/** L-Pro 产品中心 · 分类 + 关键词 + 规格 + 排序（B2B 目录页模式） */
export function useTenantProductFilter(
  products: Ref<TenantCatalogProduct[]>,
  activeCategorySlug: Ref<string>,
) {
  const searchQuery = ref('');
  const sortBy = ref<ProductSortKey>('default');
  const specFilter = ref('');

  const catalogWithSlugs = computed<TenantProductListItem[]>(() =>
    products.value.map((p, i) => ({ ...p, slug: productSlug(p, i) })),
  );

  const specFilterOptions = computed(() => {
    const labels = new Map<string, string>();
    for (const item of catalogWithSlugs.value) {
      for (const spec of item.specs || []) {
        const label = String(spec.label || '').trim();
        if (!label) continue;
        const slug = categorySlug(label);
        if (!labels.has(slug)) labels.set(slug, label);
      }
    }
    return Array.from(labels.entries())
      .map(([slug, label]) => ({ slug, label }))
      .sort((a, b) => a.label.localeCompare(b.label));
  });

  const filteredProducts = computed(() => {
    let list = catalogWithSlugs.value;

    if (activeCategorySlug.value) {
      list = list.filter((p) => categorySlug(p.category || '') === activeCategorySlug.value);
    }

    if (specFilter.value) {
      list = list.filter((p) =>
        (p.specs || []).some((s) => categorySlug(String(s.label || '')) === specFilter.value),
      );
    }

    const q = searchQuery.value.trim().toLowerCase();
    if (q) {
      list = list.filter((p) => {
        const specText = (p.specs || [])
          .map((s) => `${s.label} ${s.value}`)
          .join(' ');
        const haystack = [p.name, p.summary, p.category, specText].filter(Boolean).join(' ').toLowerCase();
        return haystack.includes(q);
      });
    }

    if (sortBy.value === 'name-asc') {
      return [...list].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    }
    if (sortBy.value === 'name-desc') {
      return [...list].sort((a, b) => b.name.localeCompare(a.name, 'zh-CN'));
    }
    return list;
  });

  const hasActiveFilters = computed(
    () =>
      Boolean(activeCategorySlug.value || searchQuery.value.trim() || specFilter.value),
  );

  function clearSearch() {
    searchQuery.value = '';
  }

  function clearSpecFilter() {
    specFilter.value = '';
  }

  function resetFilters() {
    searchQuery.value = '';
    specFilter.value = '';
    sortBy.value = 'default';
  }

  return {
    searchQuery,
    sortBy,
    specFilter,
    specFilterOptions,
    filteredProducts,
    hasActiveFilters,
    clearSearch,
    clearSpecFilter,
    resetFilters,
  };
}
