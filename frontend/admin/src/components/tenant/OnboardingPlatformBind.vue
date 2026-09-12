<template>
  <a-modal
    v-model:open="visible"
    :title="slot?.platform_name ? `绑定 ${slot.platform_name}` : '绑定第一个平台'"
    :footer="null"
    width="520px"
    :mask-closable="false"
    @cancel="onSkip"
  >
    <p class="text-sm text-slate-500 mb-4">
      {{ slot?.connect_hint || '绑定后即可自动发布首篇引流稿，无需跳转「多平台分发」菜单。' }}
    </p>

    <a-alert v-if="slot?.bound" type="success" show-icon message="该平台已绑定" class="mb-4" />

    <a-form v-else layout="vertical" @finish="submit">
      <a-form-item v-if="slot?.need_select" label="平台名称" required>
        <a-input v-model:value="form.platform_name" placeholder="如：微信公众号、LinkedIn" />
      </a-form-item>

      <a-form-item label="账号 / 用户名">
        <a-input v-model:value="form.username" placeholder="平台登录名或显示名" />
      </a-form-item>

      <a-form-item label="Cookie（可选）">
        <a-textarea
          v-model:value="form.cookie"
          :rows="3"
          placeholder="部分平台支持 Cookie 绑定"
        />
      </a-form-item>

      <a-divider>或 OAuth Token</a-divider>

      <a-form-item label="Access Token">
        <a-input v-model:value="form.accessToken" placeholder="OAuth access_token" />
      </a-form-item>

      <a-form-item label="Refresh Token">
        <a-input v-model:value="form.refreshToken" placeholder="可选" />
      </a-form-item>

      <div class="flex flex-wrap gap-2 justify-end mt-4">
        <a-button @click="onSkip">稍后绑定</a-button>
        <a-button type="primary" html-type="submit" :loading="saving">确认绑定</a-button>
      </div>
    </a-form>

    <div v-if="slot?.bound" class="flex justify-end mt-4">
      <a-button type="primary" @click="visible = false">继续</a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost } from '@/utils/api';

export interface PlatformSlot {
  account_id?: string | null;
  platform_id?: string | null;
  platform_name?: string | null;
  bound?: boolean;
  need_select?: boolean;
  connect_hint?: string;
}

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void;
  (e: 'bound', payload: { queued_task_id?: string | null }): void;
  (e: 'skip'): void;
}>();

const visible = ref(false);
const saving = ref(false);
const slot = ref<PlatformSlot | null>(null);

const form = reactive({
  platform_name: '',
  username: '',
  cookie: '',
  accessToken: '',
  refreshToken: '',
});

watch(
  () => props.open,
  async (v) => {
    visible.value = v;
    if (v) {
      await loadSlot();
    }
  },
  { immediate: true },
);

watch(visible, (v) => emit('update:open', v));

async function loadSlot() {
  try {
    slot.value = await apiGet<PlatformSlot>('/tenants/self/onboarding-chain/first-platform');
    form.platform_name = slot.value?.platform_name || '';
  } catch {
    slot.value = { need_select: true, connect_hint: '加载平台位失败，可手动填写' };
  }
}

async function submit() {
  if (slot.value?.need_select && !form.platform_name.trim()) {
    message.warning('请填写平台名称');
    return;
  }
  if (!form.cookie.trim() && !form.accessToken.trim() && !form.username.trim()) {
    message.warning('请至少填写 Cookie、Token 或用户名');
    return;
  }

  saving.value = true;
  try {
    const payload: Record<string, unknown> = {
      platform_id: slot.value?.platform_id || undefined,
      platform_name: form.platform_name.trim() || slot.value?.platform_name || undefined,
      username: form.username.trim() || undefined,
      cookie: form.cookie.trim() || undefined,
    };
    if (form.accessToken.trim()) {
      payload.configs = {
        access_token: form.accessToken.trim(),
        refresh_token: form.refreshToken.trim() || undefined,
      };
      payload.token_data = { access_token: form.accessToken.trim() };
    }
    const data = await apiPost<{ queued_task_id?: string | null }>(
      '/tenants/self/onboarding-chain/bind-platform',
      payload,
    );
    message.success(data?.queued_task_id ? '绑定成功，首篇已入队' : '平台绑定成功');
    emit('bound', { queued_task_id: data?.queued_task_id });
    visible.value = false;
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '绑定失败');
  } finally {
    saving.value = false;
  }
}

function onSkip() {
  visible.value = false;
  emit('skip');
}
</script>
