<template>
  <div>
    <!-- This component doesn't render anything visible -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRuntimeConfig, useRoute, useHead } from '#imports';
import { SITE_CONFIG } from '~/config/site';

/**
 * SEO Head Component - Enhanced SEO metadata management
 *
 * Features:
 * - Dynamic meta titles and descriptions
 * - Open Graph tags for social sharing (Facebook, LinkedIn, etc.)
 * - Twitter Card support
 * - Canonical URLs
 * - Structured data (JSON-LD) for products, cases, articles, and organization
 * - Multi-language support
 */

interface SEOProps {
  // Basic SEO
  title?: string;
  description?: string;
  keywords?: string[];

  // Open Graph
  ogType?: 'website' | 'article' | 'product' | 'profile';
  ogImage?: string;
  ogImageWidth?: number;
  ogImageHeight?: number;

  // Twitter Card
  twitterCard?: 'summary' | 'summary_large_image' | 'app' | 'player';
  twitterImage?: string;

  // Canonical URL
  canonicalUrl?: string;

  // Structured Data
  structuredData?: Record<string, any> | Array<Record<string, any>>;

  // Additional meta
  noindex?: boolean;
  nofollow?: boolean;
  robots?: string;

  // Language and hreflang
  language?: string;
  /** 支持的语言列表，用于生成 hreflang 标签 */
  supportedLanguages?: string[];
  /** 当前页面的路径（不含语言前缀），用于生成各语言的 hreflang 链接 */
  currentPath?: string;
}

const props = withDefaults(defineProps<SEOProps>(), {
  title: '',
  description: '',
  keywords: () => [],
  ogType: 'website',
  ogImage: '',
  ogImageWidth: 1200,
  ogImageHeight: 630,
  twitterCard: 'summary_large_image',
  twitterImage: '',
  canonicalUrl: '',
  structuredData: undefined,
  noindex: false,
  nofollow: false,
  robots: '',
  language: 'zh',
  supportedLanguages: () => ['zh', 'en', 'de', 'fr', 'es', 'ar', 'ja', 'ko', 'ru', 'pt', 'th', 'vi'],
  currentPath: '',
});

const config = useRuntimeConfig();
const route = useRoute();
const baseUrl = computed(() => config.public?.siteUrl || SITE_CONFIG.url);

// Generate full URL
const fullUrl = computed(() => {
  if (props.canonicalUrl) return props.canonicalUrl;
  return `${baseUrl.value}${route.fullPath}`;
});

// Default images
const defaultOgImage = '/images/og-default.jpg';
const defaultTwitterImage = '/images/twitter-card.jpg';

// Build meta tags
const metaTags = computed(() => {
  const tags: Array<Record<string, string>> = [];

  // Basic meta tags
  if (props.description) {
    tags.push({ name: 'description', content: props.description });
  }

  if (props.keywords.length > 0) {
    tags.push({ name: 'keywords', content: props.keywords.join(',') });
  }

  // Robots meta
  if (props.noindex || props.nofollow || props.robots) {
    const robotsValue =
      props.robots ||
      `${props.noindex ? 'noindex' : 'index'},${props.nofollow ? 'nofollow' : 'follow'}`;
    tags.push({ name: 'robots', content: robotsValue });
  }

  // Open Graph tags
  tags.push({ property: 'og:type', content: props.ogType });
  tags.push({ property: 'og:url', content: fullUrl.value });

  if (props.title) {
    tags.push({ property: 'og:title', content: props.title });
  }

  if (props.description) {
    tags.push({ property: 'og:description', content: props.description });
  }

  const ogImage = props.ogImage || defaultOgImage;
  tags.push({ property: 'og:image', content: ogImage });
  tags.push({ property: 'og:image:width', content: String(props.ogImageWidth) });
  tags.push({ property: 'og:image:height', content: String(props.ogImageHeight) });

  // Twitter Card tags
  tags.push({ name: 'twitter:card', content: props.twitterCard });

  if (props.title) {
    tags.push({ name: 'twitter:title', content: props.title });
  }

  if (props.description) {
    tags.push({ name: 'twitter:description', content: props.description });
  }

  const twitterImage = props.twitterImage || defaultTwitterImage;
  tags.push({ name: 'twitter:image', content: twitterImage });

  return tags;
});

// Generate hreflang links for multi-language SEO
const hreflangLinks = computed(() => {
  const links: Array<Record<string, string>> = [];
  
  // If no currentPath provided, try to extract from route
  const path = props.currentPath || route.path;
  
  // Generate hreflang links for each supported language
  props.supportedLanguages.forEach(lang => {
    // Construct the URL for this language version
    let langPath = path;
    
    // Remove existing language prefix if present
    props.supportedLanguages.forEach(supportedLang => {
      if (langPath.startsWith(`/${supportedLang}/`)) {
        langPath = langPath.substring(supportedLang.length + 1);
      } else if (langPath === `/${supportedLang}` || langPath === `/${supportedLang}/`) {
        langPath = '/';
      }
    });
    
    // Add language prefix (except for default language 'zh' which uses prefix_except_default strategy)
    const langPrefix = lang === 'zh' ? '' : `/${lang}`;
    const fullPath = langPrefix + (langPath === '/' ? '' : langPath);
    const href = `${baseUrl.value}${fullPath || '/'}`;
    
    // Map language code to hreflang format
    const hreflangMap: Record<string, string> = {
      'zh': 'zh-CN',
      'en': 'en-US',
      'de': 'de-DE',
      'fr': 'fr-FR',
      'es': 'es-ES',
      'ar': 'ar-SA',
      'ja': 'ja-JP',
      'ko': 'ko-KR',
      'ru': 'ru-RU',
      'pt': 'pt-PT',
      'th': 'th-TH',
      'vi': 'vi-VN',
    };
    
    links.push({
      rel: 'alternate',
      hreflang: hreflangMap[lang] || lang,
      href: href,
    });
  });
  
  // Add x-default link (points to the default language version)
  const defaultPath = path;
  let defaultFullPath = defaultPath;
  props.supportedLanguages.forEach(supportedLang => {
    if (defaultFullPath.startsWith(`/${supportedLang}/`)) {
      defaultFullPath = defaultFullPath.substring(supportedLang.length + 1);
    } else if (defaultFullPath === `/${supportedLang}` || defaultFullPath === `/${supportedLang}/`) {
      defaultFullPath = '/';
    }
  });
  const defaultHref = `${baseUrl.value}${defaultFullPath || '/'}`;
  links.push({
    rel: 'alternate',
    hreflang: 'x-default',
    href: defaultHref,
  });
  
  return links;
});

// Generate structured data
const jsonLd = computed(() => {
  if (!props.structuredData) return null;

  const data = Array.isArray(props.structuredData) ? props.structuredData : [props.structuredData];

  return {
    type: 'application/ld+json',
    children: JSON.stringify({
      '@context': 'https://schema.org',
      '@graph': data,
    }),
  };
});

// Use Nuxt's useHead composable
useHead({
  title: props.title || undefined,
  meta: metaTags.value,
  link: [
    ...(props.canonicalUrl ? [{ rel: 'canonical', href: fullUrl.value }] : []),
    ...hreflangLinks.value,
  ],
  script: jsonLd.value ? [jsonLd.value] : [],
});
</script>
