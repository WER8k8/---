<template>
  <div class="oauth-callback-wrap">
    <div class="oauth-callback-wrap__card">
      <a-spin size="large" />
      <p class="oauth-callback-wrap__text">{{ statusText }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/stores/auth';
import { postLoginNavigatePath, postLoginShellHint, roleFromAccessToken } from '@/utils/postLoginNavigation';
import { bindOAuthAccount } from '@/api/oauthBindings';
import {
  oauthProviderLabel,
  parseOAuthState,
  resolveOAuthProvider,
  type OAuthProvider,
} from '@/api/oauth';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const statusText = ref('正在完成第三方登录…');

function redirectTarget(state?: string, fallback?: unknown, role?: string | null): string {
  const parsed = parseOAuthState(state);
  const raw = parsed?.redirect ?? fallback;
  return postLoginNavigatePath(raw, role ?? undefined);
}

function validateOAuthState(provider: OAuthProvider, state?: string): boolean {
  if (!state) return true;
  const key = `oauth_state_${provider}`;
  const expected = sessionStorage.getItem(key);
  if (!expected) return true;
  if (expected !== state) {
    message.error('授权状态已失效，请重新登录');
    return false;
  }
  sessionStorage.removeItem(key);
  return true;
}

onMounted(async () => {
  const code = String(route.query.code || '').trim();
  const state = route.query.state ? String(route.query.state) : undefined;
  const provider = resolveOAuthProvider(
    route.query.provider ? String(route.query.provider) : undefined,
    state
  );

  if (!provider || !code) {
    message.error('授权回调参数无效（缺少 code 或无法识别登录渠道）');
    await router.replace('/login');
    return;
  }

  if (!validateOAuthState(provider, state)) {
    await router.replace('/login');
    return;
  }

  const parsed = parseOAuthState(state);
  const isBind = parsed?.mode === 'bind';

  try {
    if (isBind) {
      statusText.value = `正在绑定${oauthProviderLabel(provider)}…`;
      await bindOAuthAccount(provider, code);
      message.success('绑定成功');
      await router.replace(redirectTarget(state, '/admin/system/account-bindings'));
      return;
    }
    statusText.value = `正在通过${oauthProviderLabel(provider)}登录…`;
    await auth.loginWithOAuth(provider, code, state);
    const role = auth.currentRole ?? roleFromAccessToken(auth.token);
    const target = redirectTarget(state, route.query.redirect, role);
    message.success(postLoginShellHint(role));
    await router.replace(target);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '第三方登录失败';
    message.error(msg);
    await router.replace(isBind ? '/admin/system/account-bindings' : '/login');
  }
});
</script>

<style scoped lang="scss">
.oauth-callback-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
  padding: 24px;
}
.oauth-callback-wrap__card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 48px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
}
.oauth-callback-wrap__text {
  margin: 0;
  font-size: 14px;
  color: #666;
}
</style>
