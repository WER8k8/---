/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="重构备忘" subtitle="记录重构意图与影响面，持久化在本机" surface="elevated">
    <template #actions>
      <router-link to="/admin/code-tools/generator">
        <a-button type="primary">代码生成</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-card
      title="新建备忘"
      size="small"
    >
      <a-space
        direction="vertical"
        style="width: 100%"
      >
        <a-input
          v-model:value="title"
          placeholder="标题"
          allow-clear
        />
        <a-textarea
          v-model:value="body"
          :rows="5"
          placeholder="范围、风险、待办"
        />
        <a-button
          type="primary"
          @click="save"
        >
          保存
        </a-button>
      </a-space>
    </a-card>

    <a-card
      title="列表"
      size="small"
    >
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
              :description="item.content"
            />
            <template #actions>
              <a @click="load(item)">编辑区载入</a>
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
import { useAdminWorkspace } from '@/composables/useAdminWorkspace';

onMounted(async () => {
  try { await apiGet('/developer'); } catch { /* 空状态 */ }
});

const { state, genId } = useAdminWorkspace();
const title = ref('');
const body = ref('');

const snips = computed(() =>
  state.value.snippets
    .filter((s) => s.kind === 'refactor')
    .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1))
);

function save() {
  const t = title.value.trim();
  if (!t) {
    message.warning('请输入标题');
    return;
  }
  state.value.snippets.unshift({
    id: genId(),
    title: t,
    content: body.value,
    kind: 'refactor',
    updatedAt: new Date().toISOString(),
  });
  title.value = '';
  body.value = '';
  message.success('已保存');
}

function load(item: { title: string; content: string }) {
  title.value = item.title;
  body.value = item.content;
}

function del(id: string) {
  state.value.snippets = state.value.snippets.filter((s) => s.id !== id);
}
</script>
