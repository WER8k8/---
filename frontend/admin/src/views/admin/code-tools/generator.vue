/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="代码生成" subtitle="脚手架与片段（本地占位生成，可对接 AI 接口）" surface="elevated">
  <div class="p-6 space-y-6">
    <a-row :gutter="16">
      <a-col
        :xs="24"
        :lg="14"
      >
        <a-card title="需求与语言">
          <a-form layout="vertical">
            <a-form-item label="目标语言">
              <a-radio-group
                v-model:value="language"
                button-style="solid"
              >
                <a-radio-button value="vue">
                  Vue 3
                </a-radio-button>
                <a-radio-button value="typescript">
                  TypeScript
                </a-radio-button>
                <a-radio-button value="python">
                  Python
                </a-radio-button>
                <a-radio-button value="html">
                  HTML
                </a-radio-button>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="自然语言描述">
              <a-textarea
                v-model:value="prompt"
                :rows="8"
                placeholder="描述组件职责、接口字段、边界情况等"
                show-count
                :maxlength="4000"
              />
            </a-form-item>
            <a-space wrap>
              <a-button
                type="primary"
                :loading="busy"
                @click="generate"
              >
                生成代码
              </a-button>
              <a-button
                :disabled="!output"
                @click="copyOutput"
              >
                复制结果
              </a-button>
              <a-button
                danger
                ghost
                :disabled="!output"
                @click="clearOutput"
              >
                清空输出
              </a-button>
            </a-space>
          </a-form>
        </a-card>
      </a-col>
      <a-col
        :xs="24"
        :lg="10"
      >
        <a-card title="常用片段">
          <a-list
            size="small"
            :data-source="snippets"
            bordered
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.title">
                  <template #description>
                    <a-tag>{{ item.language }}</a-tag>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a @click="applyTemplate(item)">填入</a>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <a-card :title="`生成结果 · ${languageLabel}`">
      <a-empty
        v-if="!output && !busy"
        description="点击「生成代码」或从右侧填入片段"
      />
      <a-spin v-else-if="busy" />
      <pre
        v-else
        class="code-block"
      >{{ output }}</pre>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { useCodeGenerator } from '@/composables/useCodeGenerator';

onMounted(async () => {
  try { await apiGet('/developer') } catch { /* 空状态 */ }
});

const {
  language,
  prompt,
  output,
  busy,
  languageLabel,
  snippets,
  generate,
  applyTemplate,
  clearOutput,
} = useCodeGenerator();

async function copyOutput() {
  if (!output.value) return;
  try {
    await navigator.clipboard.writeText(output.value);
    message.success('已复制到剪贴板');
  } catch {
    message.error('复制失败，请手动选择文本');
  }
}
</script>

<style scoped>
.code-block {
  margin: 0;
  max-height: 480px;
  overflow: auto;
  padding: 16px;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}
</style>
