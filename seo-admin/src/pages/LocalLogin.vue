<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">SEO矩阵管理系统</h2>
      <p class="login-subtitle">超级管理员登录</p>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        size="large"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();
const loginFormRef = ref(null);
const loading = ref(false);

const loginForm = reactive({
  username: 'admin',
  password: 'admin123',
});

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' },
  ],
};

const handleLogin = async () => {
  try {
    await loginFormRef.value.validate();
  } catch {
    return;
  }
  
  loading.value = true;
  
  try {
    const response = await fetch('/api/v1/super-admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: loginForm.username,
        password: loginForm.password,
      }),
    });
    
    const data = await response.json();
    
    if (data.code === 0 || data.success) {
      const token = data.data?.access_token;
      if (token) {
        userStore.setToken(token);
        ElMessage.success('登录成功');
        router.push('/');
      } else {
        ElMessage.error('登录失败：未获取到token');
      }
    } else {
      ElMessage.error(data.message || '登录失败');
    }
  } catch (error) {
    console.error('Login error:', error);
    ElMessage.error('网络错误或服务器无响应');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.login-title {
  text-align: center;
  font-size: 24px;
  color: #303133;
  margin: 0 0 8px;
}

.login-subtitle {
  text-align: center;
  font-size: 14px;
  color: #909399;
  margin: 0 0 32px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.login-footer p {
  color: #909399;
  font-size: 12px;
  margin: 0;
}
</style>
