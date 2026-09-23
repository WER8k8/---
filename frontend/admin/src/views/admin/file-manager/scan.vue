/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="文件扫描登记" subtitle="登记扫描路径与发现备忘 · 已接后端 /file-scans" surface="elevated">
    <template #actions>
      <router-link to="/admin/code-tools/scanner">
        <a-button type="primary">代码扫描</a-button>
      </router-link>
      <router-link to="/admin/file-manager">
        <a-button>产品图片空间</a-button>
      </router-link>
    </template>
    <div class="page p-6 space-y-4">
      <a-card title="登记扫描路径" size="small">
        <a-space wrap style="margin-bottom: 12px">
          <a-input
            v-model:value="path"
            placeholder="路径或对象键"
            style="width: 220px"
            allow-clear
          />
          <a-input
            v-model:value="label"
            placeholder="标签"
            style="width: 140px"
            allow-clear
          />
          <a-select v-model:value="severity" style="width: 100px">
            <a-select-option value="info">信息</a-select-option>
            <a-select-option value="warn">警告</a-select-option>
            <a-select-option value="high">严重</a-select-option>
          </a-select>
          <a-input
            v-model:value="note"
            placeholder="说明"
            style="width: 200px"
            allow-clear
          />
          <a-button type="primary" :loading="saving" @click="add">添加</a-button>
        </a-space>
        <a-table
          :columns="cols"
          :data-source="rows"
          row-key="id"
          size="small"
          :loading="loading"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'stats'">
              <span v-if="record.stats?.available">
                {{ record.stats.file_count ?? 0 }} 文件 / {{ record.stats.dir_count ?? 0 }} 目录
                <span v-if="record.stats.truncated">（截断）</span>
              </span>
              <span v-else class="text-gray-400">{{ record.stats?.reason || '—' }}</span>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-popconfirm title="确认删除该登记项？" @confirm="remove(String(record.id))">
                <a-button type="link" danger size="small" :loading="deletingId === record.id">
                  删除
                </a-button>
              </a-popconfirm>
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
import { apiGet, apiPost, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';

interface ScanRow {
  id: string;
  path: string;
  label: string;
  severity: string;
  note: string;
  stats: any;
  updatedAt: string;
}

const path = ref('');
const label = ref('');
const severity = ref('warn');
const note = ref('');
const rows = ref<ScanRow[]>([]);
const loading = ref(false);
const saving = ref(false);
const deletingId = ref<string | null>(null);

const cols: TableColumnsType = [
  { title: '路径', dataIndex: 'path', key: 'path', ellipsis: true },
  { title: '标签', dataIndex: 'label', key: 'label', width: 120, ellipsis: true },
  { title: '等级', dataIndex: 'severity', key: 'severity', width: 90 },
  { title: '统计', key: 'stats', width: 160 },
  { title: '说明', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '登记时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 170 },
  { title: '操作', key: 'actions', width: 90 },
];

function mapItem(raw: any): ScanRow {
  return {
    id: String(raw.id),
    path: String(raw.path ?? ''),
    label: String(raw.label ?? ''),
    severity: String(raw.severity ?? 'info'),
    note: String(raw.note ?? raw.label ?? ''),
    stats: raw.stats ?? null,
    updatedAt: String(raw.created_at ?? raw.updated_at ?? '').slice(0, 19).replace('T', ' ') || '-',
  };
}

async function load() {
  loading.value = true;
  try {
    const res = await apiGet<any>('/file-scans');
    const items = res?.items ?? res?.data?.items ?? (Array.isArray(res) ? res : []);
    rows.value = items.map(mapItem);
  } catch (e: any) {
    message.error(e?.message || '扫描登记加载失败');
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

async function add() {
  const p = path.value.trim();
  if (!p) {
    message.warning('请输入路径');
    return;
  }
  saving.value = true;
  try {
    await apiPost('/file-scans', {
      path: p,
      label: label.value.trim(),
      severity: severity.value,
      note: note.value.trim(),
    });
    path.value = '';
    label.value = '';
    note.value = '';
    message.success('已登记');
    await load();
  } catch (e: any) {
    message.error(e?.message || '登记失败');
  } finally {
    saving.value = false;
  }
}

async function remove(id: string) {
  deletingId.value = id;
  try {
    await apiDelete(`/file-scans/${id}`);
    message.success('已删除');
    await load();
  } catch (e: any) {
    message.error(e?.message || '删除失败');
  } finally {
    deletingId.value = null;
  }
}

onMounted(() => {
  void load();
});
</script>
