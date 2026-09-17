/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="合规检查" subtitle="超管内控检查清单（本地）+ 外链站点合规工具" surface="elevated">
    <template #actions>
      <router-link to="/seo/compliance">
        <a-button type="primary">SEO 广告法合规</a-button>
      </router-link>
      <router-link to="/compliance">
        <a-button>合规治理中心</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-alert
      type="info"
      show-icon
      message="分工说明"
      description="超管侧清单用于流程备忘；敏感词扫描与页面合规仍以 SEO 矩阵与合规中心为准。"
    />

    <a-card
      title="内控检查项（本地）"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="title"
          placeholder="检查项标题"
          style="width: 260px"
          allow-clear
        />
        <a-button
          type="primary"
          @click="add"
        >
          添加
        </a-button>
      </a-space>
      <a-table
        :columns="cols"
        :data-source="state.complianceChecks"
        row-key="id"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'done' ? 'green' : 'blue'">
              {{ record.status === 'done' ? '已完成' : '待办' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button
              type="link"
              size="small"
              @click="toggle(record)"
            >
              {{ record.status === 'done' ? '标为待办' : '标为完成' }}
            </a-button>
            <a-button
              type="link"
              danger
              size="small"
              @click="remove(record.id)"
            >
              删除
            </a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';
import { useAdminWorkspace } from '@/composables/useAdminWorkspace';

onMounted(async () => {
  try { await apiGet('/compliance'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const title = ref('');

const cols: TableColumnsType = [
  { title: '检查项', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '等级', dataIndex: 'severity', key: 'severity', width: 90 },
  { title: '状态', key: 'status', width: 100 },
  { title: '备注', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 170 },
  { title: '操作', key: 'actions', width: 180 },
];

function add() {
  const t = title.value.trim();
  if (!t) {
    message.warning('请输入标题');
    return;
  }
  const now = new Date().toISOString();
  state.value.complianceChecks.unshift({
    id: genId(),
    title: t,
    severity: 'low',
    status: 'open',
    note: '',
    updatedAt: now,
  });
  title.value = '';
  message.success('已保存到本地');
}

function toggle(row: Record<string, unknown>) {
  const x = state.value.complianceChecks.find((c) => c.id === String(row.id));
  if (!x) return;
  x.status = x.status === 'done' ? 'open' : 'done';
  x.updatedAt = new Date().toISOString();
}

function remove(id: string) {
  state.value.complianceChecks = state.value.complianceChecks.filter((c) => c.id !== id);
}
</script>
