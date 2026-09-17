/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen flex flex-col">
    <Header />

    <main class="flex-1">
      <slot />
    </main>

    <Footer />

    <!-- 全站浮动联系按钮 -->
    <FloatingContact />
    <!-- P1-01：移动端全渠道 IM 吸底条 -->
    <StickyImBar />
  </div>
</template>

<script setup lang="ts">
import Header from '~/components/common/Header.vue';
import Footer from '~/components/common/Footer.vue';
import StickyImBar from '~/components/StickyImBar.vue';

const { load: loadTenantPolicy } = useTenantSitePolicy();
onMounted(() => loadTenantPolicy());

/**
 * 微信 JS-SDK 初始化（生产环境需填入实际参数）
 *
 * 使用方式：在页面加载时通过后端接口获取签名，然后调用 wx.config
 *
 * 示例：
 *   const res = await fetch('/api/wechat/jssdk-config?url=' + encodeURIComponent(window.location.href))
 *   const { appId, timestamp, nonceStr, signature } = await res.json()
 *   wx.config({
 *     debug: false,
 *     appId,         // 微信 AppID，如 wx1234567890abcdef
 *     timestamp,     // 当前时间戳（秒）
 *     nonceStr,      // 随机字符串
 *     signature,     // 签名
 *     jsApiList: ['onMenuShareTimeline', 'onMenuShareAppMessage'],
 *   })
 */

useHead({
  script: [
    {
      // 微信 JS-SDK（生产环境取消注释）
      // src: 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js',
      // defer: true,
    },
  ],
});
</script>
