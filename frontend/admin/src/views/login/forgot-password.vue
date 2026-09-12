<template>
  <div class="forgot-page">
    <div class="forgot-card">
      <h1>找回密码</h1>
      <p class="sub">通过注册邮箱验证码重置密码。生产环境未配置 SMTP 时将明确返回失败，不会假成功。</p>
      <a-form layout="vertical" @submit.prevent>
        <a-form-item label="注册邮箱" required>
          <a-input v-model:value="email" type="email" placeholder="you@company.com" />
        </a-form-item>
        <a-form-item label="验证码" required>
          <div class="row">
            <a-input v-model:value="code" placeholder="邮箱验证码" />
            <a-button :loading="sending" :disabled="!email || cooldown > 0" @click="sendCode">
              {{ cooldown > 0 ? `${cooldown}s` : '发送验证码' }}
            </a-button>
          </div>
          <p v-if="devCode" class="dev-hint">开发环境验证码：{{ devCode }}</p>
        </a-form-item>
        <a-form-item label="新密码（至少 8 位）" required>
          <a-input-password v-model:value="password" />
        </a-form-item>
        <a-alert v-if="errorMsg" type="error" show-icon :message="errorMsg" class="mb" />
        <a-alert v-if="okMsg" type="success" show-icon :message="okMsg" class="mb" />
        <a-button type="primary" block :loading="submitting" @click="submitReset">重置密码</a-button>
        <a-button type="link" block class="back" @click="router.push('/login')">返回登录</a-button>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

const router = useRouter();
const email = ref('');
const code = ref('');
const password = ref('');
const sending = ref(false);
const submitting = ref(false);
const errorMsg = ref('');
const okMsg = ref('');
const devCode = ref('');
const cooldown = ref(0);
let timer: number | undefined;

async function sendCode() {
  errorMsg.value = '';
  okMsg.value = '';
  sending.value = true;
  try {
    const res = await fetch('/api/v1/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value.trim() }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || (body.code !== undefined && body.code !== 0)) {
      throw new Error(body.message || `发送失败 (${res.status})`);
    }
    const data = body.data || {};
    okMsg.value = data.message || '若该邮箱已注册，验证码将发送至邮箱';
    if (data.dev_code) devCode.value = String(data.dev_code);
    cooldown.value = 60;
    timer = window.setInterval(() => {
      cooldown.value -= 1;
      if (cooldown.value <= 0 && timer) {
        clearInterval(timer);
        timer = undefined;
      }
    }, 1000);
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : String(e);
  } finally {
    sending.value = false;
  }
}

async function submitReset() {
  errorMsg.value = '';
  okMsg.value = '';
  if (password.value.trim().length < 8) {
    errorMsg.value = '新密码至少 8 位';
    return;
  }
  submitting.value = true;
  try {
    const res = await fetch('/api/v1/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value.trim(),
        code: code.value.trim(),
        new_password: password.value,
      }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || (body.code !== undefined && body.code !== 0)) {
      throw new Error(body.message || `重置失败 (${res.status})`);
    }
    message.success(body.message || '密码已重置');
    okMsg.value = '密码已重置，请返回登录';
    setTimeout(() => router.push('/login'), 800);
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : String(e);
  } finally {
    submitting.value = false;
  }
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #e8f3f0 0%, #f7faf9 55%, #ffffff 100%);
  padding: 24px;
}
.forgot-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  box-shadow: 0 12px 40px rgba(74, 155, 140, 0.12);
}
h1 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #1f2937;
}
.sub {
  margin: 0 0 20px;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}
.row {
  display: flex;
  gap: 8px;
}
.dev-hint {
  margin: 6px 0 0;
  color: #4a9b8c;
  font-size: 12px;
}
.mb {
  margin-bottom: 12px;
}
.back {
  margin-top: 8px;
}
</style>
