<template>
  <YdPage title="自动化概览" subtitle="调度、代码工具与脚本编排集中入口" surface="elevated">
  <div class="auto-overview p-6 space-y-6">
    <a-row :gutter="[16, 16]">
      <a-col
        :xs="24"
        :md="8"
      >
        <a-card
          title="调度中心"
          size="small"
        >
          <p class="card-desc">
            维护定时任务与执行记录
          </p>
          <router-link to="/admin/scheduler-hub">
            <a-button
              type="primary"
              block
            >
              打开调度中心
            </a-button>
          </router-link>
        </a-card>
      </a-col>
      <a-col
        :xs="24"
        :md="8"
      >
        <a-card
          title="代码生成"
          size="small"
        >
          <p class="card-desc">
            从需求描述生成代码片段
          </p>
          <router-link to="/admin/code-tools/generator">
            <a-button
              type="primary"
              block
            >
              打开生成器
            </a-button>
          </router-link>
        </a-card>
      </a-col>
      <a-col
        :xs="24"
        :md="8"
      >
        <a-card
          title="系统日志"
          size="small"
        >
          <p class="card-desc">
            排查自动化相关异常
          </p>
          <router-link to="/admin/system/logs">
            <a-button block>
              查看日志
            </a-button>
          </router-link>
        </a-card>
      </a-col>
    </a-row>

    <a-card
      title="运维备忘（仅保存在本浏览器）"
      size="small"
    >
      <a-textarea
        v-model:value="note"
        :rows="5"
        placeholder="记录临时脚本参数、Cron 表达式、联系人等；不会上传到服务器。"
        show-count
        :maxlength="4000"
        @change="persist"
      />
      <p class="hint">
        上次保存：{{ savedAt || '尚未保存' }}
      </p>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';

const STORAGE_KEY = 'admin-automation-overview-note';
const STORAGE_TS = 'admin-automation-overview-note-ts';

const note = ref('');
const savedAt = ref('');

function persist() {
  localStorage.setItem(STORAGE_KEY, note.value);
  const t = new Date().toLocaleString('zh-CN');
  localStorage.setItem(STORAGE_TS, t);
  savedAt.value = t;
}

onMounted(async () => {
  try { await apiGet('/ops-jobs'); } catch { /* 空状态 */ }
  note.value = localStorage.getItem(STORAGE_KEY) || '';
  savedAt.value = localStorage.getItem(STORAGE_TS) || '';
});
</script>

<style scoped lang="scss">
.card-desc {
  color: #64748b;
  font-size: 13px;
  margin: 0 0 12px;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
