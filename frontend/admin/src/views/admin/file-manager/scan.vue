<template>
  <YdPage title="文件扫描登记" subtitle="登记路径/发现备忘，与代码扫描联动" surface="elevated">
    <template #actions>
      <router-link to="/admin/code-tools/scanner">
        <a-button type="primary">代码扫描</a-button>
      </router-link>
      <router-link to="/admin/file-manager">
        <a-button>产品图片空间</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="登记发现项（本地）"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="path"
          placeholder="路径或对象键"
          style="width: 220px"
          allow-clear
        />
        <a-select
          v-model:value="severity"
          style="width: 100px"
        >
          <a-select-option value="info">
            信息
          </a-select-option>
          <a-select-option value="warn">
            警告
          </a-select-option>
          <a-select-option value="high">
            严重
          </a-select-option>
        </a-select>
        <a-input
          v-model:value="note"
          placeholder="说明"
          style="width: 200px"
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
        :data-source="state.scanFindings"
        row-key="id"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'actions'">
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

const { state, genId } = useAdminWorkspace();
const path = ref('');
const severity = ref('warn');
const note = ref('');

const cols: TableColumnsType = [
  { title: '路径', dataIndex: 'path', key: 'path', ellipsis: true },
  { title: '等级', dataIndex: 'severity', key: 'severity', width: 90 },
  { title: '说明', dataIndex: 'note', key: 'note', ellipsis: true },
  { title: '登记时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 180 },
  { title: '操作', key: 'actions', width: 90 },
];

function add() {
  const p = path.value.trim();
  if (!p) {
    message.warning('请输入路径');
    return;
  }
  const now = new Date().toISOString();
  state.value.scanFindings.unshift({
    id: genId(),
    path: p,
    severity: severity.value,
    note: note.value.trim(),
    updatedAt: now,
  });
  path.value = '';
  note.value = '';
  message.success('已保存到本地');
}

function remove(id: string) {
  state.value.scanFindings = state.value.scanFindings.filter((x) => x.id !== id);
}

onMounted(async () => {
  try { await apiGet('/files'); } catch { /* 空状态 */ }
});
</script>
