<template>
  <div class="capability-hub">
    <div class="page-head">
      <div>
        <h2 class="title">主站能力导航与路线图</h2>
        <p class="sub">
          本页属于
          <strong>SEO 矩阵后台</strong>
          ，用于跳转到
          <strong>优丁主管理后台（frontend/admin）</strong>
          中已实现的路线图子模块。 与侧栏「矩阵业务」分工：矩阵侧负责地域词 / 发布 /
          收录；主站侧负责超管套件、审计日志、代码与自动化工作台等。
        </p>
      </div>
      <el-button type="primary" link @click="goBack">返回矩阵看板</el-button>
    </div>

    <el-alert
      v-if="!adminOrigin"
      type="warning"
      show-icon
      :closable="false"
      class="mb-4"
      title="未配置主后台地址"
      description="本地若主后台与矩阵后台不在同一端口，请在 seo-admin 目录新建 .env.development，写入 VITE_MAIN_ADMIN_ORIGIN（无末尾斜杠）。矩阵端已取消独立登录页，须先在主管理后台登录以写入 admin_token。"
    />

    <el-row :gutter="16">
      <el-col v-for="block in blocks" :key="block.title" :xs="24" :lg="12" class="mb-4">
        <el-card shadow="never">
          <template #header>
            <span class="card-title">{{ block.title }}</span>
          </template>
          <p class="blurb">
            {{ block.blurb }}
          </p>
          <el-divider />
          <div class="link-list">
            <div
              v-for="l in block.links"
              :key="`${block.title}-${l.path}-${l.label}`"
              class="link-row"
            >
              <template v-if="l.requireOrigin && !adminOrigin">
                <span class="link-disabled">{{ l.label }}</span>
                <el-tag size="small" type="info">需配置主站地址</el-tag>
                <span class="hint">{{ l.hint }}</span>
              </template>
              <template v-else>
                <el-link
                  type="primary"
                  :underline="false"
                  :href="adminHref(l.path)"
                  @click.prevent="openAdmin(l.path)"
                >
                  {{ l.label }}
                </el-link>
                <el-tag v-if="l.tag" size="small" class="tag">
                  {{ l.tag }}
                </el-tag>
                <span class="hint">{{ l.hint }}</span>
              </template>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const adminOrigin = (import.meta.env.VITE_MAIN_ADMIN_ORIGIN || '').replace(/\/$/, '');

const adminHref = path => (adminOrigin ? `${adminOrigin}${path}` : path);

function openAdmin(path) {
  const url = adminHref(path);
  if (url.startsWith('http')) {
    window.open(url, '_blank', 'noopener,noreferrer');
  } else {
    window.location.assign(url);
  }
}

function goBack() {
  router.push('/dashboard');
}

const blocks = [
  {
    title: '安全（超管侧）',
    blurb: '与 SEO 广告法合规不同：侧重运维登记与操作审计。',
    links: [
      { path: '/admin/security', label: '安全概览', hint: '总览', tag: '' },
      {
        path: '/admin/security/vulnerability',
        label: '漏洞扫描',
        hint: '审计 + 本地待修复项',
        tag: '混合',
      },
      { path: '/admin/security/audit', label: '安全审计', hint: 'OperationLog', tag: '后端' },
      {
        path: '/admin/security/compliance',
        label: '合规检查',
        hint: '内控 + 外链 SEO 合规',
        tag: '混合',
      },
    ],
  },
  {
    title: '文件管理',
    blurb: '扫描登记、收藏检索、审计时间线（非云盘中心）。',
    links: [
      { path: '/admin/file-manager', label: '文件概览', hint: '', tag: '' },
      { path: '/admin/file-manager/scan', label: '扫描', hint: '本地登记', tag: '本地' },
      { path: '/admin/file-manager/search', label: '全局检索', hint: '收藏内过滤', tag: '本地' },
      { path: '/admin/file-manager/history', label: '历史记录', hint: '审计', tag: '后端' },
    ],
  },
  {
    title: '代码工具',
    blurb: '格式化 / 调试 / 重构工作台；生成与扫描为既有页。',
    links: [
      { path: '/admin/code-tools', label: '工具概览', hint: '', tag: '' },
      { path: '/admin/code-tools/format', label: '格式化', hint: 'JSON 等', tag: '本地' },
      { path: '/admin/code-tools/debug', label: '调试', hint: '日志分行', tag: '本地' },
      { path: '/admin/code-tools/refactor', label: '重构', hint: '备忘', tag: '本地' },
      { path: '/admin/code-tools/scanner', label: '代码扫描', hint: '', tag: '' },
    ],
  },
  {
    title: 'AI 引擎与调度',
    blurb: 'AI 分析仪表盘 + 本地任务看板；与调度中心分工。',
    links: [
      { path: '/admin/ai-engine', label: 'AI 概览', hint: '', tag: '' },
      {
        path: '/admin/ai-engine/analytics',
        label: 'AI 分析',
        hint: 'SEO 仪表盘 + 备忘',
        tag: '混合',
      },
      { path: '/admin/ai-engine/tasks', label: '任务管理', hint: '本地看板', tag: '本地' },
      { path: '/admin/scheduler-hub', label: '调度中心', hint: '', tag: '' },
    ],
  },
  {
    title: '自动化',
    blurb: '脚本 / 工作流 / Cron 备忘（本地）+ 调度中心。',
    links: [
      { path: '/admin/automation', label: '自动化概览', hint: '', tag: '' },
      { path: '/admin/automation/scripts', label: '脚本管理', hint: '', tag: '本地' },
      { path: '/admin/automation/workflows', label: '工作流', hint: '', tag: '本地' },
      { path: '/admin/automation/scheduler', label: '任务调度备忘', hint: '', tag: '本地' },
    ],
  },
  {
    title: '系统与总览',
    blurb: '主站系统日志、能力导航总页、数据看板。',
    links: [
      { path: '/admin/capability-hub', label: '能力导航（主站）', hint: '路线图总页', tag: '' },
      { path: '/admin/system/logs', label: '系统日志', hint: '审计', tag: '后端' },
      {
        path: '/dashboard',
        label: '主站数据概览',
        hint: '与矩阵「数据看板」不同；未配置主站地址时勿点',
        tag: '主站',
        requireOrigin: true,
      },
    ],
  },
];
</script>

<style scoped lang="scss">
.capability-hub {
  max-width: 1200px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.sub {
  margin: 8px 0 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.mb-4 {
  margin-bottom: 16px;
}

.card-title {
  font-weight: 600;
}

.blurb {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.link-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.tag {
  flex-shrink: 0;
}

.link-disabled {
  color: #c0c4cc;
  font-size: 14px;
}

.hint {
  font-size: 12px;
  color: #909399;
}
</style>
