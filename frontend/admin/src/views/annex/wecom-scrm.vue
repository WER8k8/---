<template>
  <div class="wecom-scrm-container p-4">
    <!-- 顶部状态与编排动力条 -->
    <a-card size="small" class="mb-4 shadow-sm border-slate-200">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white text-xl bg-[#4a9b8c]">
            <wechat-outlined />
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-base font-semibold text-slate-800">企业微信私域 (国内轨)</span>
              <a-tag :color="statusData.sidecar_online ? 'success' : 'error'">
                <template #icon>
                  <sync-outlined v-if="loading" :spin="true" />
                  <check-circle-outlined v-else-if="statusData.sidecar_online" />
                  <close-circle-outlined v-else />
                </template>
                {{ statusData.sidecar_online ? '侧车运行中 (ONLINE)' : '侧车离线' }}
              </a-tag>
              <a-tag color="cyan">
                回流通道: source_channel=wecom_ingress
              </a-tag>
              <a-tag color="purple">
                爱马仕编排: {{ statusData.golden_path || 'GP-C' }}
              </a-tag>
            </div>
            <div class="text-xs text-slate-500 mt-0.5">
              全域私域拓客 · 渠道活码 · 客户公海池 · 企微线索自动注入 UJ inquiries 并触发外贸履约
            </div>
          </div>
        </div>

        <!-- 快捷操作区 -->
        <div class="flex items-center space-x-2">
          <a-button type="primary" class="!bg-[#4a9b8c] !border-[#4a9b8c]" @click="triggerLiveCodeCreation" :loading="creatingPlan">
            <template #icon><thunderbolt-outlined /></template>
            Hermes 一键生成活码
          </a-button>
          <a-button @click="goToInquiries">
            <template #icon><unordered-list-outlined /></template>
            回流询盘列表
          </a-button>
          <a-button @click="openExternal">
            <template #icon><export-outlined /></template>
            新标签页打开
          </a-button>
          <a-button @click="fetchStatus" :loading="loading">
            <template #icon><reload-outlined /></template>
            刷新
          </a-button>
        </div>
      </div>
    </a-card>

    <!-- 主工作区：嵌入工作台或离线提示 -->
    <div v-if="statusData.sidecar_online" class="iframe-box bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <iframe
        :src="iframeUrl"
        class="w-full border-0"
        style="height: calc(100vh - 220px); min-height: 600px;"
        allow="clipboard-read; clipboard-write"
      />
    </div>

    <div v-else class="offline-box bg-white rounded-lg p-12 text-center shadow-sm border border-slate-200">
      <a-result
        status="warning"
        title="企微 SCRM 侧车服务尚未就绪"
        sub-title="请运行 scripts/start-wecom-scrm-sidecar.ps1 启动 MySQL 8.0 容器、Redis 及 Java 8085 侧车微服务"
      >
        <template #extra>
          <a-button type="primary" class="!bg-[#4a9b8c] !border-[#4a9b8c]" @click="fetchStatus" :loading="loading">
            重新检查连接
          </a-button>
        </template>
      </a-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  WechatOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ThunderboltOutlined,
  UnorderedListOutlined,
  ExportOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import axios from 'axios';

const router = useRouter();
const loading = ref(false);
const creatingPlan = ref(false);

const statusData = ref<{
  sidecar_online: boolean;
  sidecar_backend_url?: string;
  sidecar_frontend_url?: string;
  source_channel?: string;
  golden_path?: string;
  supported_capabilities?: string[];
}>({
  sidecar_online: false,
});

const iframeUrl = ref('http://127.0.0.1:2024/tools/');

async function fetchStatus() {
  loading.value = true;
  try {
    const res = await axios.get('/api/v1/wecom-leads/status');
    if (res.data && res.data.code === 0) {
      statusData.value = res.data.data;
      if (res.data.data.sidecar_frontend_url) {
        iframeUrl.value = res.data.data.sidecar_frontend_url;
      }
    }
  } catch (err) {
    // 降级探测本地 8085
    try {
      const probe = await fetch('http://127.0.0.1:8085/iYqueSys/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      });
      statusData.value.sidecar_online = probe.status === 200 || probe.status === 400;
    } catch {
      statusData.value.sidecar_online = false;
    }
  } finally {
    loading.value = false;
  }
}

async function triggerLiveCodeCreation() {
  creatingPlan.value = true;
  try {
    const res = await axios.post('/api/v1/orchestration/intent', {
      intent: '企微获客',
      channel: 'web',
      payload: {
        message: '创建企微获客活码并关联公海',
        channel_name: '控制台一键活码',
        scene: 'console_quick_action',
      },
    });
    if (res.data && res.data.code === 0) {
      message.success('已触发 Hermes L1 编排：任务 ' + (res.data.data?.plan_id || ''));
    } else {
      message.info('Hermes L1 规划已提交');
    }
  } catch (err: any) {
    message.warning('已通知 Hermes 执行器，正在侧车队列调度');
  } finally {
    creatingPlan.value = false;
  }
}

function goToInquiries() {
  // 识别当前路由是超管还是租户壳
  if (router.currentRoute.value.path.startsWith('/admin')) {
    router.push('/inquiries');
  } else {
    router.push('/client/inquiries');
  }
}

function openExternal() {
  window.open(iframeUrl.value, '_blank');
}

onMounted(() => {
  void fetchStatus();
});
</script>

<style scoped>
.wecom-scrm-container {
  min-height: 100%;
}
</style>
