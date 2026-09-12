<!-- 文件与对象变更历史 -->
<template>
  <YdPage title="文件与对象变更历史" subtitle="以全站操作审计为准，可按 action / resource_type 缩小范围" surface="elevated">
    <template #actions>
      <router-link to="/admin/file-manager">
        <a-button>产品图片空间</a-button>
      </router-link>
    </template>
    <AdminAuditLogTable title="操作审计（后端）" />
  </YdPage>
</template>

<script setup lang="ts">
import { YdPage } from '@/components/youding';
import AdminAuditLogTable from '@/components/admin/AdminAuditLogTable.vue';
</script>
