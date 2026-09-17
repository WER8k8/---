/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="cross-platform-dashboard">
    <a-page-header title="跨平台数据看板" sub-title="AiToEarn 全平台数据聚合">
      <template #extra>
        <a-space>
          <a-button @click="refreshData" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <AitoearnCapabilityBar ref="capabilityRef" class="mb-4" />

    <a-alert
      v-if="showEmptyHint"
      type="info"
      show-icon
      message="暂无跨平台账号数据"
      description="请确认 AiToEarn Key 已配置、超管已分配矩阵号，并在发布台完成平台绑号后刷新。"
      class="mb-4"
    />

    <template v-if="loading">
      <a-row :gutter="16" style="margin-bottom: 24px">
        <a-col v-for="i in 4" :key="`cp-skel-${i}`" :span="6">
          <SkeletonCard variant="kpi" />
        </a-col>
      </a-row>
      <SkeletonCard variant="table" :rows="5" />
    </template>
    <template v-else>
      <!-- 概览卡片 -->
      <a-row :gutter="16" style="margin-bottom: 24px">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总账号数"
              :value="overview.total_accounts || 0"
              style="margin-right: 50px"
            >
              <template #prefix><UserOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总粉丝数"
              :value="overview.total_followers || 0"
              style="margin-right: 50px"
            >
              <template #prefix><TeamOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总作品数"
              :value="overview.total_posts || 0"
              style="margin-right: 50px"
            >
              <template #prefix><VideoCameraOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总点赞数"
              :value="overview.total_likes || 0"
              style="margin-right: 50px"
            >
              <template #prefix><LikeOutlined /></template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- 平台分布 -->
      <a-card title="平台分布" style="margin-bottom: 24px">
        <a-table
          :columns="platformColumns"
          :data-source="overview.platforms || []"
          :pagination="false"
          row-key="platform"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'platform'">
              <a-tag :color="getPlatformColor(record.platform)">
                {{ record.platform }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 养号效果 -->
      <a-card title="养号效果" style="margin-bottom: 24px">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic
              title="养号周期总数"
              :value="nurture.total_cycles || 0"
              style="margin-bottom: 16px"
            />
          </a-col>
          <a-col :span="8">
            <a-statistic
              title="平均进度"
              :value="nurture.avg_progress_pct || 0"
              suffix="%"
              style="margin-bottom: 16px"
            />
          </a-col>
          <a-col :span="8">
            <a-statistic
              title="总互动次数"
              :value="totalEngagements"
              style="margin-bottom: 16px"
            />
          </a-col>
        </a-row>
        <a-divider />
        <a-table
          :columns="nurtureColumns"
          :data-source="nurture.cycles || []"
          :pagination="false"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template v-if="column.key === 'progress'">
              <a-progress :percent="record.progress_pct || 0" size="small" />
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 发布效果 -->
      <a-card title="发布效果（最近 7 天）" style="margin-bottom: 24px">
        <a-row :gutter="16" style="margin-bottom: 16px">
          <a-col :span="6">
            <a-statistic title="总任务数" :value="publish.total_tasks || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="成功数" :value="publish.succeeded || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="失败数" :value="publish.failed || 0" />
          </a-col>
          <a-col :span="6">
            <a-statistic
              title="成功率"
              :value="publish.success_rate || 0"
              suffix="%"
            />
          </a-col>
        </a-row>
        <a-table
          :columns="publishColumns"
          :data-source="publish.recent_tasks || []"
          :pagination="false"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getPublishStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template v-if="column.key === 'published_url'">
              <a v-if="record.published_url" :href="record.published_url" target="_blank">
                查看作品
              </a>
              <span v-else>-</span>
            </template>
          </template>
        </a-table>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import {
  ReloadOutlined,
  UserOutlined,
  TeamOutlined,
  VideoCameraOutlined,
  LikeOutlined,
} from '@ant-design/icons-vue';
import api from '@/api';
import AitoearnCapabilityBar from '@/components/tenant/AitoearnCapabilityBar.vue';
import SkeletonCard from '@/components/common/SkeletonCard.vue';

const loading = ref(false);
const capabilityRef = ref<InstanceType<typeof AitoearnCapabilityBar> | null>(null);
const overview = ref<any>({});
const nurture = ref<any>({});
const publish = ref<any>({});

const showEmptyHint = computed(() => {
  if (loading.value) return false;
  return !(overview.value.total_accounts > 0);
});

const platformColumns = [
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '账号数', dataIndex: 'account_count', key: 'account_count' },
  { title: '粉丝总数', dataIndex: 'total_followers', key: 'total_followers' },
  { title: '作品总数', dataIndex: 'total_posts', key: 'total_posts' },
  { title: '点赞总数', dataIndex: 'total_likes', key: 'total_likes' },
];

const nurtureColumns = [
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '账号', dataIndex: 'account_label', key: 'account_label' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '进度', dataIndex: 'progress_pct', key: 'progress' },
  { title: '点赞', dataIndex: ['stats', 'total_likes'], key: 'likes' },
  { title: '评论', dataIndex: ['stats', 'total_comments'], key: 'comments' },
  { title: '关注', dataIndex: ['stats', 'total_follows'], key: 'follows' },
];

const publishColumns = [
  { title: '平台', dataIndex: 'platform', key: 'platform' },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '发布时间', dataIndex: 'published_at', key: 'published_at' },
  { title: '作品链接', dataIndex: 'published_url', key: 'published_url' },
];

const totalEngagements = computed(() => {
  const eng = nurture.value.total_engagements || {};
  return (eng.likes || 0) + (eng.comments || 0) + (eng.follows || 0);
});

function getPlatformColor(platform: string): string {
  const colors: Record<string, string> = {
    douyin: '#000000',
    kuaishou: '#FF4906',
    bilibili: '#00A1D6',
    xiaohongshu: '#FE2C55',
    wxchannels: '#07C160',
    tiktok: '#000000',
    youtube: '#FF0000',
    instagram: '#E4405F',
    facebook: '#1877F2',
    threads: '#000000',
    twitter: '#1DA1F2',
    linkedin: '#0A66C2',
    pinterest: '#E60023',
  };
  return colors[platform] || '#1890ff';
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'default',
    warming: 'processing',
    active: 'success',
    cooling: 'warning',
    paused: 'default',
    archived: 'default',
  };
  return colors[status] || 'default';
}

function getPublishStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'default',
    dispatched: 'processing',
    published: 'success',
    failed: 'error',
    cancelled: 'default',
  };
  return colors[status] || 'default';
}

async function refreshData() {
  loading.value = true;
  try {
    const [overviewRes, nurtureRes, publishRes] = await Promise.all([
      api.get('/cross-platform-dashboard/overview'),
      api.get('/cross-platform-dashboard/nurture'),
      api.get('/cross-platform-dashboard/publish?days=7'),
    ]);
    overview.value = overviewRes.data?.data || {};
    nurture.value = nurtureRes.data?.data || {};
    publish.value = publishRes.data?.data || {};
  } catch (error: any) {
    message.error('获取数据失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
    void capabilityRef.value?.reload?.();
  }
}

onMounted(() => {
  refreshData();
});
</script>

<style scoped>
.cross-platform-dashboard {
  padding: 24px;
}
.mb-4 {
  margin-bottom: 16px;
}
</style>
