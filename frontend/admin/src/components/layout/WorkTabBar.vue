/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdProWorktabs hide-meta v-bind="$attrs" />
</template>

<script setup lang="ts">
/**
 * @deprecated 请使用 YdProWorktabs；保留别名以免旧引用报错
 */
import YdProWorktabs from '@/components/layout/YdProWorktabs.vue'

defineOptions({ inheritAttrs: false })
</script>
