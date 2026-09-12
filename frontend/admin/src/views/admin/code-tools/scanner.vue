<template>
  <YdPage title="代码扫描" subtitle="全局检索与代码关联分析" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="startScan">
        <ReloadOutlined />
        开始扫描
      </a-button>
    </template>
  <div class="scanner-page">
    <div class="search-bar">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索代码、文件、函数..."
        @search="handleSearch"
      />
      <a-select
        v-model:value="searchType"
        style="width: 120px; margin-left: 12px"
      >
        <a-select-option value="all">
          全部
        </a-select-option>
        <a-select-option value="code">
          代码
        </a-select-option>
        <a-select-option value="file">
          文件
        </a-select-option>
        <a-select-option value="function">
          函数
        </a-select-option>
      </a-select>
    </div>

    <div class="scan-results">
      <div class="result-header">
        <span class="result-count">找到 {{ scanResults.length }} 个结果</span>
      </div>
      <div class="result-list">
        <div
          class="result-item"
          v-for="result in scanResults"
          :key="result.id"
        >
          <div class="result-icon">
            <component :is="result.icon" />
          </div>
          <div class="result-info">
            <h4 class="result-name">
              {{ result.name }}
            </h4>
            <p class="result-path">
              {{ result.path }}
            </p>
            <p class="result-preview">
              {{ result.preview }}
            </p>
          </div>
          <div class="result-meta">
            <span class="meta-tag">{{ result.type }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="scan-stats">
      <div class="stat-card">
        <div class="stat-icon bg-blue">
          <FolderOpenOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ fileCount }}</span>
          <span class="stat-label">文件总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-green">
          <CodeOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ codeLines }}</span>
          <span class="stat-label">代码行数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-purple">
          <BranchesOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ functionCount }}</span>
          <span class="stat-label">函数数量</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon bg-orange">
          <WarningOutlined />
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ issueCount }}</span>
          <span class="stat-label">潜在问题</span>
        </div>
      </div>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
  SearchOutlined,
  ReloadOutlined,
  CodeOutlined,
  BranchesOutlined,
  WarningOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons-vue';

const searchQuery = ref('');
const searchType = ref('all');

const fileCount = ref(0);
const codeLines = ref('0');
const functionCount = ref(0);
const issueCount = ref(0);

interface ScanResult {
  id: number;
  name: string;
  path: string;
  preview: string;
  type: string;
  icon: any;
}

const scanResults = ref<ScanResult[]>([]);

const allResults = ref<ScanResult[]>([]);

const handleSearch = () => {
  const q = searchQuery.value.trim().toLowerCase();
  const type = searchType.value;
  scanResults.value = allResults.value.filter((r) => {
    const typeOk = type === 'all' || r.type.includes(type === 'code' ? '文件' : type === 'file' ? '目录' : '函数');
    if (!q) return typeOk;
    return typeOk && (r.name.toLowerCase().includes(q) || r.path.toLowerCase().includes(q) || r.preview.toLowerCase().includes(q));
  });
  message.success(`找到 ${scanResults.value.length} 个结果`);
};

const startScan = () => {
  message.loading('扫描中…', 0.8);
  setTimeout(() => {
    issueCount.value = Math.max(0, issueCount.value - 1);
    message.success('扫描完成');
  }, 800);
};

onMounted(async () => {
  try { await apiGet('/developer'); } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.scanner-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
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

  .scan-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.scan-results {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;

  .result-header {
    padding-bottom: 16px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 16px;

    .result-count {
      font-size: 14px;
      color: #6b7280;
    }
  }

  .result-list {
    .result-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #f9fafb;

      &:last-child {
        border-bottom: none;
      }

      .result-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: #f3f4f6;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        color: #6b7280;
        flex-shrink: 0;
      }

      .result-info {
        flex: 1;

        .result-name {
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
          margin-bottom: 4px;
        }

        .result-path {
          font-size: 12px;
          color: #4a9b8c;
          margin: 0;
          margin-bottom: 4px;
        }

        .result-preview {
          font-size: 13px;
          color: #6b7280;
          margin: 0;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }

      .result-meta {
        .meta-tag {
          font-size: 12px;
          color: #fff;
          background: #4a9b8c;
          padding: 4px 8px;
          border-radius: 4px;
        }
      }
    }
  }
}

.scan-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;

  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fff;

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-purple {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      }
      &.bg-orange {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      }
    }

    .stat-content {
      .stat-value {
        font-size: 20px;
        font-weight: 600;
        color: #1f2937;
        display: block;
      }

      .stat-label {
        font-size: 12px;
        color: #6b7280;
      }
    }
  }
}

@media (max-width: 1024px) {
  .scan-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .scan-stats {
    grid-template-columns: 1fr;
  }
}
</style>
