<template>
  <YdPage title="买家问答" subtitle="Apache Answer Sidecar · SEO 长尾" surface="elevated">
    <a-alert type="info" show-icon class="mb-4" :message="config?.honest_note || '问答页嵌入独立站，新问题进 SEO 候选，不自动灌帖'" />

    <a-card title="Sidecar 状态" class="mb-4" :loading="loading">
      <p>
        地址：<code>{{ sidecar?.url || '—' }}</code>
        <a-tag :color="sidecar?.healthy ? 'success' : 'warning'" class="ml-2">
          {{ sidecar?.healthy ? '在线' : '未就绪' }}
        </a-tag>
      </p>
      <a-button size="small" class="mt-2" @click="reload">刷新</a-button>
    </a-card>

    <a-card title="嵌入设置" class="mb-4">
      <a-form layout="vertical">
        <a-form-item label="在独立站展示买家问答">
          <a-switch v-model:checked="form.enabled" />
        </a-form-item>
        <a-form-item label="Answer 地址（Sidecar）">
          <a-input v-model:value="form.embed_url" placeholder="http://127.0.0.1:9080" />
        </a-form-item>
        <a-form-item label="公开路径">
          <a-input v-model:value="form.public_path" placeholder="/questions" />
        </a-form-item>
        <a-space>
          <a-button type="primary" :loading="saving" @click="save">保存</a-button>
          <a-button @click="rotateSecret">轮换 Webhook 密钥</a-button>
        </a-space>
      </a-form>
    </a-card>

    <a-card title="语言桥（FORUM-05）" class="mb-4">
      <a-radio-group v-model:value="bridgeMode" class="mb-3">
        <a-radio-button value="question_to_zh">英文提问 → 中文摘要</a-radio-button>
        <a-radio-button value="answer_to_en">中文要点 → 英文回答草稿</a-radio-button>
      </a-radio-group>
      <a-form layout="vertical">
        <a-form-item v-if="bridgeMode === 'answer_to_en'" label="买家问题标题">
          <a-input v-model:value="bridgeContextTitle" placeholder="What is the fire rating of rock wool?" />
        </a-form-item>
        <a-form-item :label="bridgeMode === 'question_to_zh' ? '英文提问正文' : '老板中文要点'">
          <a-textarea v-model:value="bridgeText" :rows="5" />
        </a-form-item>
        <a-button type="primary" :loading="bridgeLoading" @click="runBridge">生成草稿</a-button>
      </a-form>
      <pre v-if="bridgeResult" class="code-box mt-3">{{ bridgeResult }}</pre>
    </a-card>

    <a-card v-if="config?.iframe_src" title="预览" class="mb-4">
      <iframe :src="config.iframe_src" class="forum-preview" title="买家问答预览" />
    </a-card>

    <a-card title="Webhook（Answer 管理后台填写）">
      <p class="text-sm">URL：<code>{{ config?.webhook_url }}</code></p>
      <p class="text-sm mt-2">Headers：</p>
      <pre class="code-box">{{ webhookHeadersText }}</pre>
      <a-button size="small" class="mt-2" @click="copyWebhook">复制说明</a-button>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import {
  fetchForumConfig,
  fetchForumStatus,
  translateForumQa,
  updateForumConfig,
  type ForumConfig,
} from '@/api/forum';

const loading = ref(false);
const saving = ref(false);
const sidecar = ref<{ healthy?: boolean; url?: string } | null>(null);
const config = ref<ForumConfig | null>(null);
const form = reactive({
  enabled: false,
  embed_url: 'http://127.0.0.1:9080',
  public_path: '/questions',
});
const bridgeMode = ref<'question_to_zh' | 'answer_to_en'>('question_to_zh');
const bridgeText = ref('');
const bridgeContextTitle = ref('');
const bridgeLoading = ref(false);
const bridgeResult = ref('');

const webhookHeadersText = computed(() => {
  const h = config.value?.webhook_headers || {};
  return JSON.stringify({ ...h, 'Content-Type': 'application/json' }, null, 2);
});

async function reload() {
  loading.value = true;
  try {
    sidecar.value = await fetchForumStatus();
    config.value = await fetchForumConfig();
    form.enabled = !!config.value?.enabled;
    form.embed_url = config.value?.embed_url || form.embed_url;
    form.public_path = config.value?.public_path || form.public_path;
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  try {
    config.value = await updateForumConfig({
      enabled: form.enabled,
      embed_url: form.embed_url,
      public_path: form.public_path,
    });
    message.success('已保存');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

async function rotateSecret() {
  try {
    config.value = await updateForumConfig({ rotate_webhook_secret: true });
    message.success('Webhook 密钥已轮换，请同步到 Answer');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '失败');
  }
}

function copyWebhook() {
  const text = `POST ${config.value?.webhook_url}\n${webhookHeadersText.value}`;
  navigator.clipboard.writeText(text).then(() => message.success('已复制'));
}

async function runBridge() {
  if (!bridgeText.value.trim()) {
    message.warning('请先填写内容');
    return;
  }
  bridgeLoading.value = true;
  try {
    const data = await translateForumQa({
      mode: bridgeMode.value,
      text: bridgeText.value,
      context_title: bridgeContextTitle.value || undefined,
    });
    bridgeResult.value = JSON.stringify(data, null, 2);
    message.success('草稿已生成，发布前请人工核对');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '生成失败');
  } finally {
    bridgeLoading.value = false;
  }
}

onMounted(reload);
</script>

<style scoped>
.forum-preview {
  width: 100%;
  min-height: 420px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.code-box {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow: auto;
}
</style>
