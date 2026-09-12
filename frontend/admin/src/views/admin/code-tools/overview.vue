<template>
  <YdPage title="代码工具" subtitle="代码编辑、生成和重构工具管理" surface="elevated">
    <YdHonestDataBanner
      level="mock"
      title="实验室模块 · 无上游使用统计"
      description="下方工具入口可本地试用；「使用次数/生成行数」等统计未接真实 API，不可对外报数。"
    />
  <div class="code-tools-overview">
    <div class="tools-grid">
      <div
        class="tool-card"
        v-for="tool in tools"
        :key="tool.name"
        @click="navigateTo(tool.path)"
      >
        <div
          class="tool-icon"
          :class="tool.iconBg"
        >
          <component :is="tool.icon" />
        </div>
        <h3 class="tool-name">
          {{ tool.name }}
        </h3>
        <p class="tool-desc">
          {{ tool.description }}
        </p>
        <div class="tool-stats">
          <span class="stat">实验室入口</span>
        </div>
      </div>
    </div>

    <div v-if="!tools.length" class="empty-hint">暂无已注册工具（请检查路由配置）</div>

    <div v-else class="row">
      <div class="col-2">
        <div class="panel">
          <h3 class="panel-title">能力状态</h3>
          <p class="panel-note">统计面板待接 developer API；当前仅展示入口导航。</p>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import {
  CodeOutlined,
  SyncOutlined,
  BugOutlined,
  ClusterOutlined,
  CheckCircleOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';
import { YdHonestDataBanner, YdPage } from '@/components/youding';
import { useRouter } from 'vue-router';

const tools = ref([
  { name: '代码生成', path: '/admin/code-tools/generator', icon: CodeOutlined, iconBg: 'bg-blue', description: '按场景生成代码片段' },
  { name: '代码重构', path: '/admin/code-tools/refactor', icon: SyncOutlined, iconBg: 'bg-green', description: '结构优化建议' },
  { name: '调试助手', path: '/admin/code-tools/debug', icon: BugOutlined, iconBg: 'bg-amber', description: '错误定位与修复提示' },
  { name: '代码格式化', path: '/admin/code-tools/format', icon: ClusterOutlined, iconBg: 'bg-purple', description: '统一代码风格' },
  { name: '代码扫描', path: '/admin/code-tools/scanner', icon: SearchOutlined, iconBg: 'bg-cyan', description: '静态问题扫描' },
  { name: '代码审查', path: '/admin/code-tools/review', icon: CheckCircleOutlined, iconBg: 'bg-indigo', description: '变更审查清单' },
]);

const router = useRouter();

onMounted(async () => {
  try {
    await apiGet('/developer');
  } catch {
    /* 实验室：developer API 未接满时仍展示入口 */
  }
});

const navigateTo = (path: string) => {
  router.push(path);
};
</script>

<style scoped lang="scss">
.code-tools-overview {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .page-desc {
    font-size: 14px;
    color: #6b7280;
    margin-top: 4px;
  }
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;

  .tool-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition:
      transform 0.2s,
      box-shadow 0.2s;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }

    .tool-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;
      margin-bottom: 12px;

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-purple {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      }
      &.bg-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-orange {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      }
      &.bg-teal {
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
      }
    }

    .tool-name {
      font-size: 15px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
      margin-bottom: 6px;
    }

    .tool-desc {
      font-size: 13px;
      color: #6b7280;
      margin: 0;
      margin-bottom: 12px;
    }

    .tool-stats {
      .stat {
        font-size: 12px;
        color: #9ca3af;
        background: #f3f4f6;
        padding: 4px 8px;
        border-radius: 4px;
      }
    }
  }
}

.row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .panel-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
  }
}

.stats-chart {
  padding: 20px;

  .chart-info {
    display: flex;
    justify-content: space-between;
    margin-top: 12px;
    font-size: 14px;
    color: #6b7280;

    .value {
      font-weight: 600;
      color: #1f2937;
    }
  }
}

.hot-features {
  .feature-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f3f4f6;

    &:last-child {
      border-bottom: none;
    }

    .feature-rank {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #4a9b8c;
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .feature-info {
      flex: 1;
      display: flex;
      justify-content: space-between;

      .feature-name {
        font-size: 14px;
        color: #1f2937;
      }

      .feature-count {
        font-size: 13px;
        color: #6b7280;
      }
    }
  }
}

@media (max-width: 1024px) {
  .tools-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .tools-grid {
    grid-template-columns: 1fr;
  }
}
</style>
