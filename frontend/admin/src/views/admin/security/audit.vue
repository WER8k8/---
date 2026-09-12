<!-- 安全审计 -->
<template>
  <YdPage title="安全审计" subtitle="管理员操作与安全相关 resource 的审计流水" surface="elevated">
    <template #actions>
      <router-link to="/admin/system/logs">
        <a-button type="primary">系统日志（同数据源）</a-button>
      </router-link>
      <router-link to="/analytics">
        <a-button>数据分析</a-button>
      </router-link>
    </template>
    <AdminAuditLogTable />
  </YdPage>
</template>

<script setup lang="ts">
import { YdPage } from '@/components/youding';
import AdminAuditLogTable from '@/components/admin/AdminAuditLogTable.vue';
</script>
