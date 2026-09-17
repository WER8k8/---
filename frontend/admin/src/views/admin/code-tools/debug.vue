/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="调试工作台" subtitle="日志与堆栈分行展示，数据仅存本地浏览器" surface="elevated">
  <div class="page p-6 space-y-4">
    <a-card
      title="原始文本"
      size="small"
    >
      <a-textarea
        v-model:value="raw"
        :rows="8"
        placeholder="粘贴日志 / 堆栈"
      />
      <a-space
        style="margin-top: 12px"
        wrap
      >
        <a-button
          type="primary"
          @click="splitLines"
        >
          按行拆分
        </a-button>
        <a-button @click="copyLines">
          复制分行结果
        </a-button>
      </a-space>
    </a-card>

    <a-card
      title="分行预览"
      size="small"
    >
      <a-table
        :columns="cols"
        :data-source="lines"
        row-key="i"
        size="small"
        :pagination="{ pageSize: 20 }"
      />
    </a-card>

    <a-card
      title="调试备忘（本地片段）"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="title"
          placeholder="标题"
          style="width: 200px"
        />
        <a-button @click="save">
          保存当前原文
        </a-button>
      </a-space>
      <a-list
        v-if="snips.length"
        bordered
        :data-source="snips"
        size="small"
      >
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta
              :title="item.title"
              :description="item.updatedAt"
            />
            <template #actions>
              <a @click="raw = item.content">载入</a>
              <a
                style="color: #cf1322"
                @click="del(item.id)"
              >删</a>
            </template>
          </a-list-item>
        </template>
      </a-list>
      <a-empty v-else />
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';
import { useAdminWorkspace } from '@/composables/useAdminWorkspace';

onMounted(async () => {
  try { await apiGet('/developer'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const raw = ref('');
const lines = ref<{ i: number; line: string }[]>([]);
const title = ref('');

const cols: TableColumnsType = [
  { title: '#', dataIndex: 'i', key: 'i', width: 60 },
  { title: '内容', dataIndex: 'line', key: 'line', ellipsis: true },
];

const snips = computed(() =>
  state.value.snippets
    .filter((s) => s.kind === 'debug')
    .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1))
);

function splitLines() {
  const t = raw.value.replace(/\r\n/g, '\n');
  lines.value = t.split('\n').map((line, idx) => ({ i: idx + 1, line }));
  message.success(`共 ${lines.value.length} 行`);
}

async function copyLines() {
  const text = lines.value.map((l) => l.line).join('\n');
  if (!text) {
    message.warning('请先拆分');
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    message.success('已复制');
  } catch {
    message.error('复制失败');
  }
}

function save() {
  const t = title.value.trim() || `调试-${new Date().toLocaleString()}`;
  if (!raw.value.trim()) {
    message.warning('内容为空');
    return;
  }
  state.value.snippets.unshift({
    id: genId(),
    title: t,
    content: raw.value,
    kind: 'debug',
    updatedAt: new Date().toISOString(),
  });
  title.value = '';
  message.success('已保存');
}

function del(id: string) {
  state.value.snippets = state.value.snippets.filter((s) => s.id !== id);
}
</script>
