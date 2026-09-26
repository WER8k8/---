/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <TenantSiteGateway :page="page" />
</template>

<script setup lang="ts">
const page = 'parameters' as const;
definePageMeta({ layout: 'tenant-blank' });
</script>
