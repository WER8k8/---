<template>
  <div class="ai-center-layout">
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.ai-center-layout {
  min-height: 100%;
}
</style>
