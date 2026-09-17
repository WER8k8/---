/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="脚本库" subtitle="保存常用脚本片段（本地）" surface="elevated">
    <template #actions>
      <router-link to="/admin/scheduler-hub">
        <a-button type="primary">调度中心</a-button>
      </router-link>
      <router-link to="/admin/automation">
        <a-button>自动化概览</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="新建 / 编辑"
      size="small"
    >
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <a-input
          v-model:value="name"
          placeholder="脚本名称"
          allow-clear
        />
        <a-textarea
          v-model:value="body"
          :rows="10"
          placeholder="#!/usr/bin/env bash ..."
          class="mono"
        />
        <a-space>
          <a-button
            type="primary"
            @click="save"
          >
            {{ editingId ? '更新' : '保存' }}
          </a-button>
          <a-button
            v-if="editingId"
            @click="reset"
          >
            取消编辑
          </a-button>
        </a-space>
      </a-space>
    </a-card>

    <a-table
      :columns="cols"
      :data-source="state.scripts"
      row-key="id"
      size="small"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'actions'">
          <a-button
            type="link"
            size="small"
            @click="edit(record)"
          >
            编辑
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
  try { await apiGet('/ops-jobs'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const name = ref('');
const body = ref('');
const editingId = ref<string | null>(null);

const cols: TableColumnsType = [
  { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '更新', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 140 },
];

function save() {
  const n = name.value.trim();
  if (!n || !body.value.trim()) {
    message.warning('请填写名称与脚本正文');
    return;
  }
  const now = new Date().toISOString();
  if (editingId.value) {
    const s = state.value.scripts.find((x) => x.id === editingId.value);
    if (s) {
      s.name = n;
      s.body = body.value;
      s.updatedAt = now;
      message.success('已更新');
    }
  } else {
    state.value.scripts.unshift({ id: genId(), name: n, body: body.value, updatedAt: now });
    message.success('已保存');
  }
  reset();
}

function edit(row: Record<string, unknown>) {
  editingId.value = String(row.id);
  name.value = String(row.name ?? '');
  body.value = String(row.body ?? '');
}

function reset() {
  editingId.value = null;
  name.value = '';
  body.value = '';
}

function remove(id: string) {
  state.value.scripts = state.value.scripts.filter((s) => s.id !== id);
}
</script>

<style scoped>
.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
</style>
