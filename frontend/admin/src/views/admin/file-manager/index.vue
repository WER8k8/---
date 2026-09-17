/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="p-6">
    <a-card :title="PRODUCT_IMAGE_SPACE_TITLE">
      <router-view />
    </a-card>
  </div>
</template>
<script setup lang="ts">
import { PRODUCT_IMAGE_SPACE_TITLE } from '@/constants/productImageSpace';
</script>
