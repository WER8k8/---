/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="system-layout">
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script setup lang="ts"></script>

<style scoped lang="scss">
.system-layout {
  min-height: 100vh;
}
</style>
