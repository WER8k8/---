# PWA 配置指南

## 概述

项目已集成 PWA（Progressive Web App）支持，用户可以将网站安装到桌面，享受类原生应用体验。

## 已完成配置

### 1. 依赖安装

- `@nuxt/image` - 图片优化模块，支持自动 WebP 转换
- `@vite-pwa/nuxt` - PWA 支持模块

### 2. nuxt.config.ts 配置

```typescript
modules: [
  '@nuxt/image',      // 图片优化
  '@vite-pwa/nuxt'    // PWA 支持
]

// 图片优化配置
image: {
  format: ['webp', 'png'],  // 优先使用 WebP 格式
  quality: 80,               // 图片质量 80%
  screens: { ... }           // 响应式断点
}

// PWA 配置
pwa: {
  manifest: { ... },         // Web App Manifest
  workbox: { ... }           // Service Worker 配置
}
```

## 待完成事项

### 添加 PWA 图标

需要在 `frontend/public/images/icons/` 目录下放置以下文件：

| 文件名 | 尺寸 | 用途 |
|--------|------|------|
| icon-192x192.png | 192x192 | 小屏幕设备、任务栏图标 |
| icon-512x512.png | 512x512 | 大屏幕设备、启动画面 |

**图标设计要求：**
- PNG 格式，透明背景或白色背景
- 建议使用公司 Logo
- 确保在不同尺寸下清晰可辨

**生成工具推荐：**
- [RealFaviconGenerator](https://realfavicongenerator.net/)
- [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator)

## 使用方法

### 图片优化

在组件中使用 `<NuxtImg>` 或 `<NuxtPicture>` 组件：

```vue
<template>
  <!-- 自动转换为 WebP 格式 -->
  <NuxtImg src="/images/product.jpg" alt="产品图片" />

  <!-- 指定多种格式 -->
  <NuxtPicture src="/images/banner.jpg" formats="webp png" />

  <!-- 响应式图片 -->
  <NuxtImg
    src="/images/hero.jpg"
    sizes="xs:320px sm:640px md:768px lg:1024px"
    alt="响应式图片"
  />
</template>
```

### PWA 功能

用户访问网站时，浏览器会自动显示安装提示（如果满足 PWA 安装条件）。

**验证 PWA 是否正常工作：**
1. 构建生产版本：`npm run build`
2. 预览：`npm run preview`
3. 在 Chrome DevTools > Application > Manifest 查看 Web App Manifest
4. 在 Chrome DevTools > Application > Service Workers 查看 Service Worker 状态

## 注意事项

1. **开发环境**：PWA 在开发模式下默认禁用，需构建生产版本测试
2. **HTTPS**：生产环境必须使用 HTTPS 才能启用 Service Worker
3. **缓存策略**：当前配置缓存静态资源，可根据需要调整 `workbox.globPatterns`
4. **图标缺失**：如果未添加图标，PWA 安装功能将不可用，但不影响其他功能

## 后续优化建议

1. 添加离线页面支持
2. 实现推送通知功能
3. 配置后台同步
4. 添加分享目标支持
