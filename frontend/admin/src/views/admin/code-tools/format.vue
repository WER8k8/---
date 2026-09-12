<template>
  <YdPage title="代码格式化工作台" subtitle="JSON 美化与片段保存（本地）" surface="elevated">
    <template #actions>
      <router-link to="/admin/code-tools/scanner">
        <a-button>代码扫描</a-button>
      </router-link>
    </template>
  <div class="page p-6 space-y-4">
    <a-row :gutter="16">
      <a-col
        :xs="24"
        :lg="14"
      >
        <a-card
          title="输入"
          size="small"
        >
          <a-textarea
            v-model:value="input"
            :rows="14"
            placeholder="粘贴 JSON 或文本"
          />
          <a-space
            style="margin-top: 12px"
            wrap
          >
            <a-button
              type="primary"
              @click="formatJson"
            >
              尝试 JSON 美化
            </a-button>
            <a-button @click="copyOut">
              复制输出
            </a-button>
          </a-space>
        </a-card>
      </a-col>
      <a-col
        :xs="24"
        :lg="10"
      >
        <a-card
          title="输出"
          size="small"
        >
          <a-textarea
            v-model:value="output"
            :rows="14"
            readonly
            class="out"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-card
      title="已存片段（本地）"
      size="small"
    >
      <a-space
        wrap
        style="margin-bottom: 12px"
      >
        <a-input
          v-model:value="snapTitle"
          placeholder="片段标题"
          style="width: 200px"
        />
        <a-button
          type="dashed"
          @click="saveSnippet"
        >
          保存当前输出
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
              <a @click="apply(item)">载入</a>
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
const input = ref('');
const output = ref('');
const snapTitle = ref('');

const snips = computed(() =>
  state.value.snippets
    .filter((s) => s.kind === 'format')
    .sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1))
);

function formatJson() {
  const raw = input.value.trim();
  if (!raw) {
    message.warning('请先输入内容');
    return;
  }
  try {
    const obj = JSON.parse(raw);
    output.value = JSON.stringify(obj, null, 2);
    message.success('JSON 已格式化');
  } catch {
    message.error('不是合法 JSON，未修改输出区');
  }
}

async function copyOut() {
  if (!output.value) {
    message.warning('输出为空');
    return;
  }
  try {
    await navigator.clipboard.writeText(output.value);
    message.success('已复制');
  } catch {
    message.error('复制失败，请手动选择复制');
  }
}

function saveSnippet() {
  const t = snapTitle.value.trim() || `片段-${new Date().toLocaleString()}`;
  if (!output.value.trim()) {
    message.warning('请先在输出区生成内容');
    return;
  }
  state.value.snippets.unshift({
    id: genId(),
    title: t,
    content: output.value,
    kind: 'format',
    updatedAt: new Date().toISOString(),
  });
  snapTitle.value = '';
  message.success('已保存到本地');
}

function apply(item: { content: string }) {
  output.value = item.content;
  message.success('已载入到输出区');
}

function del(id: string) {
  state.value.snippets = state.value.snippets.filter((s) => s.id !== id);
}
</script>

<style scoped>
.out {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
</style>
