<template>
  <div class="min-h-screen flex flex-col saas-page">
    <slot />
  </div>
</template>

<script setup lang="ts">
import '~/assets/css/saas-marketing.css';

useHead({
  titleTemplate: '%s | 优丁出海工作台',
  meta: [{ name: 'theme-color', content: '#2563eb' }],
});
</script>
