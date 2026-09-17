/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="出口报价一页" subtitle="FOB / MOQ · 绑定产品库" surface="elevated">
    <a-alert
      type="warning"
      show-icon
      class="mb-4"
      message="未填单价时只出模板，不会编造成交价；发给买家前务必人工核对。"
    />

    <a-card title="报价参数" class="mb-4">
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="MOQ">
              <a-input v-model:value="form.moq" placeholder="例如 100" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="单价 (USD)">
              <a-input-number v-model:value="form.unitPrice" :min="0" class="w-full" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="贸易条款">
              <a-input v-model:value="form.deliveryTerms" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="备注（中文）">
          <a-textarea v-model:value="form.notesZh" :rows="2" />
        </a-form-item>
        <a-button type="primary" :loading="loading" @click="generate">生成报价</a-button>
      </a-form>
    </a-card>

    <a-card v-if="quote" title="结果">
      <p v-if="!quote.ready" class="text-red-600">{{ quote.error }}</p>
      <template v-else>
        <pre class="quote-box">{{ quote.one_pager_zh }}</pre>
        <p class="text-xs text-gray-500 mt-2">{{ quote.honest_note }}</p>
        <a-space class="mt-3" wrap>
          <a-button @click="copyText(quote.one_pager_zh || '')">复制中文一页</a-button>
          <a-button v-if="quote.pi?.markdown" @click="copyText(quote.pi.markdown)">复制 PI 英文</a-button>
          <a-button @click="router.push('/client/seo-keywords')">去看 SEO 词库 →</a-button>
        </a-space>
      </template>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import { postExportQuote, type ExportQuote } from '@/api/cross-border';

const router = useRouter();
const loading = ref(false);
const quote = ref<ExportQuote | null>(null);
const form = reactive({
  moq: '',
  unitPrice: undefined as number | undefined,
  deliveryTerms: 'FOB Tianjin',
  notesZh: '',
});

async function generate() {
  loading.value = true;
  try {
    const res = await postExportQuote({
      moq: form.moq || undefined,
      unit_price: form.unitPrice,
      delivery_terms: form.deliveryTerms,
      notes_zh: form.notesZh,
    });
    quote.value = res as ExportQuote;
    if (!quote.value?.ready) {
      message.warning(quote.value?.error || '请先完善产品库');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '生成失败');
  } finally {
    loading.value = false;
  }
}

function copyText(text: string) {
  navigator.clipboard.writeText(text).then(() => message.success('已复制'));
}
</script>

<style scoped>
.quote-box {
  white-space: pre-wrap;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}
.w-full {
  width: 100%;
}
</style>
