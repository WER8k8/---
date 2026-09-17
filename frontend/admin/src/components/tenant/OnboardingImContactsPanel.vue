/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="im-contacts-panel">
    <OnboardingWangcaiGuide :bubble-text="guideBubble" :point-at="focusField" />

    <p class="im-contacts-panel__note">
      这一步只配置<strong>即时通讯</strong>，写入官网 contact 页。客户站右下角旺财仍是
      <strong>Trade Q&amp;A 智能顾问</strong>（与此处指引分离，逻辑不变）。
    </p>

    <div class="im-contacts-grid">
      <div
        v-for="tool in tools"
        :key="tool.key"
        :id="`im-field-${tool.key}`"
        class="im-field"
        :class="{ 'im-field--focus': focusField === tool.key }"
        @focusin="focusField = tool.key"
      >
        <label class="im-field__label">
          <span class="im-field__icon">{{ iconFor(tool.key) }}</span>
          {{ tool.label }}
          <span v-if="tool.key === 'whatsapp' || tool.key === 'wechat'" class="im-field__badge">推荐</span>
        </label>
        <p class="im-field__hint">{{ tool.hint }}</p>
        <a-input
          v-model:value="form[tool.key]"
          :placeholder="placeholderFor(tool.key)"
          allow-clear
          @focus="focusField = tool.key"
        />
      </div>
    </div>

    <div class="im-contacts-panel__actions">
      <a-button type="primary" size="large" :loading="saving" @click="save(true)">
        保存并继续
      </a-button>
      <a-button size="large" @click="save(false)">稍后填写</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost } from '@/utils/api';
import OnboardingWangcaiGuide from '@/components/tenant/OnboardingWangcaiGuide.vue';

interface ImTool {
  key: string;
  label: string;
  hint: string;
}

const emit = defineEmits<{ done: [] }>();

const tools = ref<ImTool[]>([]);
const saving = ref(false);
const focusField = ref('whatsapp');
const form = reactive<Record<string, string>>({
  whatsapp: '',
  wechat: '',
  qq: '',
  telegram: '',
  line: '',
  phone: '',
  email: '',
});

const guideBubble = computed(() => {
  const map: Record<string, string> = {
    whatsapp: '🐾 海外客户最爱 WhatsApp！填国际号码，官网挂件一键跳转聊天。',
    wechat: '🐾 微信给华人/国内客户；挂件会一键复制微信号。',
    qq: '🐾 QQ 是国内客户常用方式；填 QQ 号，挂件一键复制。',
    telegram: '🐾 Telegram 在俄语区/中东很常用，可填 @用户名。',
    line: '🐾 LINE 适合日本/泰国/台湾市场。',
    phone: '🐾 国际电话格式，如 +86-138xxxx。',
    email: '🐾 正式报价与开发信用邮箱。',
  };
  return map[focusField.value] || map.whatsapp;
});

function iconFor(key: string): string {
  const icons: Record<string, string> = {
    whatsapp: '💬',
    wechat: '🟢',
    qq: '🐧',
    telegram: '✈️',
    line: '💚',
    phone: '📞',
    email: '✉️',
  };
  return icons[key] || '•';
}

function placeholderFor(key: string): string {
  const ph: Record<string, string> = {
    whatsapp: '如 8613800138000（不含 + 也可）',
    wechat: '如 Export-Sales',
    qq: '如 123456789',
    telegram: '如 @your_export_bot',
    line: 'LINE ID',
    phone: '+86-138-0000-0000',
    email: 'sales@yourcompany.com',
  };
  return ph[key] || '';
}

async function load() {
  try {
    const data = await apiGet<{
      contacts?: Record<string, string>;
      guide_tools?: ImTool[];
    }>('/tenants/self/onboarding-chain/im-contacts');
    tools.value = data?.guide_tools || defaultTools();
    const c = data?.contacts || {};
    for (const k of Object.keys(form)) {
      form[k] = c[k] || '';
    }
  } catch {
    tools.value = defaultTools();
  }
}

function defaultTools(): ImTool[] {
  return [
    { key: 'whatsapp', label: 'WhatsApp', hint: '海外客户第一选择' },
    { key: 'wechat', label: '微信', hint: '国内/华人客户' },
    { key: 'qq', label: 'QQ', hint: '国内客户' },
    { key: 'telegram', label: 'Telegram', hint: '俄语区/中东' },
    { key: 'line', label: 'LINE', hint: '日/泰/台' },
    { key: 'phone', label: '电话', hint: '国际格式' },
    { key: 'email', label: '邮箱', hint: '正式报价' },
  ];
}

async function save(markDone: boolean) {
  if (markDone && !form.whatsapp.trim() && !form.wechat.trim() && !form.qq.trim()) {
    message.warning('请至少填写 WhatsApp、微信或 QQ 其中一项');
    focusField.value = 'whatsapp';
    return;
  }
  saving.value = true;
  try {
    await apiPost('/tenants/self/onboarding-chain/im-contacts', {
      ...form,
      mark_done: markDone,
    });
    message.success(markDone ? '联系方式已写入官网' : '已跳过，可稍后在建站编辑器补填');
    emit('done');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

onMounted(load);
</script>

<style scoped lang="scss">
.im-contacts-panel {
  &__note {
    font-size: 12px;
    color: #64748b;
    margin: 0 0 16px;
    line-height: 1.55;
  }
  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 20px;
  }
}

.im-contacts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.im-field {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;

  &--focus {
    border-color: #818cf8;
    box-shadow: 0 0 0 3px rgb(129 140 248 / 0.15);
  }

  &__label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
  }
  &__icon {
    font-size: 16px;
  }
  &__badge {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 999px;
    background: #dcfce7;
    color: #15803d;
    font-weight: 600;
  }
  &__hint {
    margin: 0 0 8px;
    font-size: 11px;
    color: #94a3b8;
  }
}
</style>
