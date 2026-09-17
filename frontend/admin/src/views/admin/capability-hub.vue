/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    class="hub space-y-6"
    title="能力导航与路线图"
    subtitle="各子页已区分：后端已接入（审计日志、SEO 仪表盘等）与本地工作台（备忘、脚本、扫描登记）。超管侧「安全合规」与 SEO「广告法合规」为不同入口。"
    surface="elevated"
  >
    <template #actions>
      <a-button type="primary" @click="goAdminHome">
        返回超管首页
      </a-button>
    </template>

    <a-alert
      type="info"
      show-icon
      message="说明"
      description="带「后端」标记的列表来自 `/api/v1/system/audit/logs`（OperationLog）。其余表格与脚本库仅保存在本机浏览器 localStorage，便于排期与演示；可后续替换为真实 API。"
    />

    <a-row :gutter="[16, 16]">
      <a-col
        v-for="block in blocks"
        :key="block.title"
        :xs="24"
        :lg="12"
      >
        <a-card
          :title="block.title"
          size="small"
        >
          <p class="muted">
            {{ block.blurb }}
          </p>
          <a-divider style="margin: 12px 0" />
          <div class="link-grid">
            <router-link
              v-for="l in block.links"
              :key="`${block.title}-${l.path}-${l.label}`"
              v-slot="{ href, navigate }"
              :to="l.path"
              custom
            >
              <a
                :href="href"
                class="link-chip"
                @click.prevent="navigate"
              >
                <span class="chip-title">{{ l.label }}</span>
                <a-tag
                  v-if="l.tag"
                  size="small"
                >{{ l.tag }}</a-tag>
                <span class="chip-desc">{{ l.hint }}</span>
              </a>
            </router-link>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { YdPage } from '@/components/youding';
import { apiGet } from '@/utils/api';

const router = useRouter();

onMounted(async () => {
  try { await apiGet('/hub') } catch { /* 空状态 */ }
});

function goAdminHome() {
  router.push('/admin');
}

const blocks = [
  {
    title: '安全（超管侧）',
    blurb: '与 SEO 广告法合规不同：此处侧重运维/安全登记与审计追溯。',
    links: [
      { path: '/admin/security', label: '安全概览', hint: '总览', tag: '' },
      {
        path: '/admin/security/vulnerability',
        label: '漏洞扫描',
        hint: '审计 + 本地待修复项',
        tag: '混合',
      },
      { path: '/admin/security/audit', label: '安全审计', hint: '全量操作审计', tag: '后端' },
      {
        path: '/admin/security/compliance',
        label: '合规检查',
        hint: '内控清单 + 跳转 SEO 合规',
        tag: '混合',
      },
    ],
  },
  {
    title: '产品图片空间',
    blurb: '概览页聚合入口；子页为扫描登记、收藏检索、审计时间线，不是云盘中心。',
    links: [
      { path: '/admin/file-manager', label: '产品图片空间', hint: '上传 · 复制链接 · 建站', tag: '核心' },
      { path: '/admin/video-space', label: '视频空间', hint: '租户视频 · 共用七牛/R2', tag: '核心' },
      {
        path: '/admin/file-manager/scan',
        label: '扫描',
        hint: '本地发现项 + 代码扫描',
        tag: '本地',
      },
      {
        path: '/admin/file-manager/search',
        label: '全局检索',
        hint: '收藏路径内检索',
        tag: '本地',
      },
      { path: '/admin/file-manager/history', label: '历史记录', hint: '操作审计', tag: '后端' },
    ],
  },
  {
    title: '代码工具',
    blurb: '格式化 / 调试 / 重构为本地工作台；生成与扫描走既有页面。',
    links: [
      { path: '/admin/code-tools', label: '工具概览', hint: '', tag: '' },
      { path: '/admin/code-tools/format', label: '格式化', hint: 'JSON 美化与片段', tag: '本地' },
      { path: '/admin/code-tools/debug', label: '调试', hint: '日志分行与备忘', tag: '本地' },
      { path: '/admin/code-tools/refactor', label: '重构', hint: '重构备忘', tag: '本地' },
      { path: '/admin/code-tools/scanner', label: '代码扫描', hint: '已有能力', tag: '' },
    ],
  },
  {
    title: 'AI 引擎',
    blurb: '「AI 分析」拉 SEO 仪表盘指标；「任务管理」为本地任务看板，与调度中心分工。',
    links: [
      { path: '/admin/ai-engine', label: 'AI 概览', hint: '', tag: '' },
      { path: '/admin/ai-engine/analytics', label: 'AI 分析', hint: '仪表盘 + 备忘', tag: '混合' },
      { path: '/admin/ai-engine/tasks', label: '任务管理', hint: '本地看板', tag: '本地' },
      { path: '/admin/scheduler-hub', label: '调度中心', hint: '生产向定时任务', tag: '' },
    ],
  },
  {
    title: '自动化',
    blurb: '脚本、工作流、Cron 备忘为本地；与调度中心联动。',
    links: [
      { path: '/admin/automation', label: '自动化概览', hint: '', tag: '' },
      { path: '/admin/automation/scripts', label: '脚本管理', hint: '本地脚本库', tag: '本地' },
      { path: '/admin/automation/workflows', label: '工作流', hint: '本地步骤说明', tag: '本地' },
      {
        path: '/admin/automation/scheduler',
        label: '任务调度',
        hint: '本地 Cron 备忘',
        tag: '本地',
      },
      { path: '/admin/scheduler-hub', label: '调度中心', hint: '', tag: '' },
    ],
  },
  {
    title: '系统与日志',
    blurb: '系统日志页已对接同一审计接口。',
    links: [
      { path: '/admin/system/logs', label: '系统日志', hint: 'OperationLog', tag: '后端' },
      { path: '/analytics', label: '数据分析', hint: '全站统计入口', tag: '' },
    ],
  },
  {
    title: '渠道与代理',
    blurb: '按 L1～L5 为各级代理勾选工作台入口；与会话级别预览共用 localStorage。',
    links: [
      {
        path: '/admin/system/agent-capabilities',
        label: '代理能力划拨',
        hint: '勾选保存 · 工作台即时过滤',
        tag: '本地',
      },
    ],
  },
];
</script>

<style scoped lang="scss">
.muted {
  color: #64748b;
  font-size: 13px;
  margin: 0;
}

.link-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-chip {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 2px 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  text-decoration: none;
  color: inherit;
  transition:
    border-color 0.15s,
    background 0.15s;

  &:hover {
    border-color: rgb(85 119 143 / 0.35);
    background: #faf5ff;
  }
}

.chip-title {
  font-weight: 600;
  color: #0f172a;
}

.chip-desc {
  grid-column: 1 / -1;
  font-size: 12px;
  color: #64748b;
}
</style>
