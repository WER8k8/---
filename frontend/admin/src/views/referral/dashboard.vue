/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
  <div class="referral-dashboard">
    <!-- ===== 顶部 Banner ===== -->
    <div class="rd-banner">
      <div class="rd-banner-bg"></div>
      <div class="rd-banner-content">
        <h1 class="rd-banner-title">呼朋唤友计划</h1>
        <p class="rd-banner-slogan">推荐好友，双双有礼</p>
        <p class="rd-banner-sub">邀请好友注册并使用优丁建材 AI SaaS，您和好友均可获得丰厚奖励</p>
      </div>
    </div>

    <!-- ===== 统计数据行 ===== -->
    <a-row :gutter="[16, 16]" class="rd-stats">
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="rd-stat-card rd-stat-card--primary">
          <div class="rd-stat-label">我的邀请码</div>
          <div class="rd-stat-code-row">
            <span class="rd-stat-code">YD{{ referralCode }}</span>
            <a-button type="primary" size="small" class="rd-copy-btn" @click="copyCode">
              <template #icon><CopyOutlined /></template>
              复制
            </a-button>
          </div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <div class="rd-stat-card">
          <div class="rd-stat-label">已邀请人数</div>
          <div class="rd-stat-value">{{ stats.invitedCount }}</div>
          <div class="rd-stat-trend" v-if="stats.trend > 0">较上月 +{{ stats.trend }}</div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <div class="rd-stat-card">
          <div class="rd-stat-label">已获得奖励</div>
          <div class="rd-stat-value rd-stat-value--gold">¥{{ stats.reward }}</div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <div class="rd-stat-card">
          <div class="rd-stat-label">排行榜排名</div>
          <div class="rd-stat-value">#{{ stats.rank || '-' }}</div>
          <div class="rd-stat-trend" v-if="stats.rank">前 {{ stats.percent }}%</div>
        </div>
      </a-col>
    </a-row>

    <!-- ===== 分享方式 ===== -->
    <a-card class="rd-section rd-share" title="邀请方式" :bordered="false">
      <a-row :gutter="[16, 16]">
        <a-col :xs="12" :sm="12" :md="6">
          <div class="rd-share-item" @click="copyWechat">
            <div class="rd-share-icon rd-share-icon--wechat">
              <WechatOutlined />
            </div>
            <div class="rd-share-label">微信分享</div>
            <div class="rd-share-desc">微信号: youding-builder</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="12" :md="6">
          <div class="rd-share-item" @click="copyLink">
            <div class="rd-share-icon rd-share-icon--link">
              <LinkOutlined />
            </div>
            <div class="rd-share-label">复制链接</div>
            <div class="rd-share-desc">分享注册链接给好友</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="12" :md="6">
          <div class="rd-share-item" @click="shareQQ">
            <div class="rd-share-icon rd-share-icon--qq">
              <QQOutlined />
            </div>
            <div class="rd-share-label">QQ 分享</div>
            <div class="rd-share-desc">分享到 QQ 好友或群</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="12" :md="6">
          <div class="rd-share-item" @click="shareSMS">
            <div class="rd-share-icon rd-share-icon--sms">
              <MessageOutlined />
            </div>
            <div class="rd-share-label">短信邀请</div>
            <div class="rd-share-desc">通过短信发送邀请</div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- ===== 奖励进度条 ===== -->
    <a-card class="rd-section rd-progress-card" :bordered="false">
      <template #title>
        <span class="rd-progress-title">奖励阶梯</span>
        <span class="rd-progress-subtitle">当前已邀请 {{ stats.invitedCount }} 人，继续加油！</span>
      </template>
      <div class="rd-progress-steps">
        <div
          v-for="(step, idx) in rewardSteps"
          :key="idx"
          class="rd-step"
          :class="{ 'rd-step--done': stats.invitedCount >= step.target, 'rd-step--current': stats.invitedCount < step.target && (idx === 0 || stats.invitedCount >= rewardSteps[idx - 1].target) }"
        >
          <div class="rd-step-marker">
            <CheckCircleFilled v-if="stats.invitedCount >= step.target" class="rd-step-icon rd-step-icon--done" />
            <LoadingOutlined v-else-if="stats.invitedCount < step.target && (idx === 0 || stats.invitedCount >= rewardSteps[idx - 1].target)" class="rd-step-icon rd-step-icon--current" />
            <div v-else class="rd-step-icon rd-step-icon--pending">{{ idx + 1 }}</div>
          </div>
          <div class="rd-step-info">
            <div class="rd-step-target">邀请 {{ step.target }} 人</div>
            <div class="rd-step-reward">奖励 <strong>¥{{ step.reward }}</strong></div>
          </div>
        </div>
      </div>
      <a-progress
        :percent="progressPercent"
        :stroke-color="progressGradient"
        :show-info="false"
        class="rd-progress-bar"
      />
    </a-card>

    <!-- ===== 邀请记录表格 ===== -->
    <a-card class="rd-section" title="邀请记录" :bordered="false">
      <a-table
        :columns="columns"
        :data-source="records"
        :pagination="{ pageSize: 10 }"
        row-key="id"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'rewarded' ? 'green' : 'orange'">
              {{ record.status === 'rewarded' ? '已奖励' : '待确认' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'reward'">
            <span class="text-emerald-600 font-semibold">¥{{ record.reward }}</span>
          </template>
        </template>
        <template #emptyText>
          <a-empty description="还没有邀请记录，快去邀请好友吧！" />
        </template>
      </a-table>
    </a-card>

    <!-- ===== 排行榜 Top10 ===== -->
    <a-card class="rd-section" title="邀请排行榜" :bordered="false">
      <div class="rd-rank-list">
        <div
          v-for="(item, idx) in ranking"
          :key="item.id"
          class="rd-rank-item"
          :class="{ 'rd-rank-item--top3': idx < 3, 'rd-rank-item--me': item.isMe }"
        >
          <div class="rd-rank-pos">
            <span v-if="idx === 0" class="rd-rank-medal rd-rank-medal--gold">1</span>
            <span v-else-if="idx === 1" class="rd-rank-medal rd-rank-medal--silver">2</span>
            <span v-else-if="idx === 2" class="rd-rank-medal rd-rank-medal--bronze">3</span>
            <span v-else class="rd-rank-num">{{ idx + 1 }}</span>
          </div>
          <div class="rd-rank-company">
            <span class="rd-rank-name">{{ item.company }}</span>
            <span v-if="item.isMe" class="rd-rank-badge">我</span>
          </div>
          <div class="rd-rank-count">
            <span class="rd-rank-count-num">{{ item.count }}</span>
            <span class="rd-rank-count-label">人</span>
          </div>
        </div>
      </div>
      <div v-if="ranking.length === 0" class="rd-rank-empty">
        <a-empty description="暂无排行数据，成为第一个邀请好友的人吧！" />
      </div>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  CopyOutlined,
  WechatOutlined,
  LinkOutlined,
  QqOutlined as QQOutlined,
  MessageOutlined,
  CheckCircleFilled,
  LoadingOutlined,
} from '@ant-design/icons-vue'
import { getAuthToken } from '@/utils/api'

// ===== API Headers helper =====
const tk = () => getAuthToken()
const headers = () => ({ Authorization: `Bearer ${tk()}` })

const referralCode = ref('')

const stats = reactive({
  invitedCount: 0,
  reward: 0,
  rank: 0,
  percent: 0,
  trend: 0,
})

const rewardSteps = [
  { target: 1, reward: 30 },
  { target: 3, reward: 60 },
  { target: 5, reward: 100 },
]

const progressPercent = computed(() =>
  Math.min(100, (stats.invitedCount / rewardSteps[rewardSteps.length - 1].target) * 100),
)

const progressGradient = { '0%': '#4a9b8c', '100%': '#22c55e' }

const columns = [
  { title: '好友姓名', dataIndex: 'friendName', key: 'friendName' },
  { title: '公司', dataIndex: 'company', key: 'company' },
  { title: '注册时间', dataIndex: 'registerTime', key: 'registerTime' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '奖励金额', dataIndex: 'reward', key: 'reward' },
]

const records = ref<any[]>([])

const ranking = ref<{ id: number; company: string; count: number; isMe: boolean }[]>([])

// ===== API 数据加载 =====
async function fetchMyCode() {
  try {
    const res = await fetch('/api/v1/referral/my-code', { headers: headers() })
    const body = await res.json()
    if (body.code === 0 && body.data?.code) {
      referralCode.value = body.data.code
    }
  } catch { /* empty state on failure */ }
}

async function fetchStats() {
  try {
    const res = await fetch('/api/v1/referral/stats', { headers: headers() })
    const body = await res.json()
    if (body.code === 0 && body.data) {
      const d = body.data
      stats.invitedCount = d.total_invited ?? d.invitedCount ?? stats.invitedCount
      stats.reward = d.estimated_discount ?? d.reward ?? stats.reward
      stats.rank = d.rank ?? stats.rank
      stats.percent = d.percent ?? stats.percent
      stats.trend = d.trend ?? stats.trend
    }
  } catch { /* empty state on failure */ }
}

async function fetchRecords() {
  try {
    const res = await fetch('/api/v1/referral/records', { headers: headers() })
    const body = await res.json()
    const raw = body.data?.items ?? body.data
    if (body.code === 0 && Array.isArray(raw)) {
      records.value = raw.map((r: any) => ({
        id: r.id,
        friendName: r.invited_name || r.friendName || '好友',
        company: r.invited_name || r.company || '-',
        registerTime: r.invited_at ? String(r.invited_at).slice(0, 10) : '-',
        status: r.status,
        reward: r.reward_amount ? (r.reward_amount >= 100 ? r.reward_amount / 100 : r.reward_amount) : 0,
      }))
    }
  } catch { /* empty state on failure */ }
}

async function fetchLeaderboard() {
  try {
    const res = await fetch('/api/v1/referral/leaderboard', { headers: headers() })
    const body = await res.json()
    const raw = body.data?.items ?? body.data
    if (body.code === 0 && Array.isArray(raw)) {
      ranking.value = raw.map((item: any, idx: number) => ({
        id: item.rank ?? idx + 1,
        company: item.company_name || item.company || '租户',
        count: item.invite_count ?? item.count ?? 0,
        isMe: item.isMe ?? false,
      }))
    }
  } catch { /* empty state on failure */ }
}

// ===== 操作方法 =====
const shareLink = computed(() => `${window.location.origin}/tenants/register?ref=${referralCode.value}`)

function copyCode() {
  navigator.clipboard.writeText(`YD${referralCode.value}`).then(() => {
    message.success('邀请码已复制')
  }).catch(() => {
    message.success(`邀请码: YD${referralCode.value}`)
  })
}

function copyWechat() {
  navigator.clipboard.writeText('youding-builder').then(() => {
    message.success('微信号已复制，请打开微信添加')
  }).catch(() => {
    message.warning('复制失败，微信号: youding-builder')
  })
}

function copyLink() {
  navigator.clipboard.writeText(shareLink.value).then(() => {
    message.success('邀请链接已复制')
  }).catch(() => {
    message.warning(`复制失败，邀请链接: ${shareLink.value}`)
  })
}

function shareQQ() {
  const qqUrl = `https://connect.qq.com/widget/shareqq/index.html?title=呼朋唤友计划&summary=推荐好友注册优丁建材AI%20SaaS，双双有礼！&url=${encodeURIComponent(shareLink.value)}`
  window.open(qqUrl, '_blank', 'width=720,height=600')
}

function shareSMS() {
  const smsBody = `推荐你使用优丁建材 AI SaaS，和我一起享受智能建站与营销服务！注册链接：${shareLink.value} 邀请码：YD${referralCode.value}`
  window.location.href = `sms:?body=${encodeURIComponent(smsBody)}`
}

onMounted(() => {
  fetchMyCode()
  fetchStats()
  fetchRecords()
  fetchLeaderboard()
})
</script>

<style scoped>
/* ===== 全局容器 ===== */
.referral-dashboard {
  max-width: 1060px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== Banner ===== */
.rd-banner {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 36px 32px;
  background: linear-gradient(135deg, #1e3a5f 0%, #1a4a3a 50%, #0d3b2e 100%);
}
.rd-banner-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(59, 130, 246, 0.25) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 30%, rgba(34, 197, 94, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 50%);
  pointer-events: none;
}
.rd-banner-content {
  position: relative;
  z-index: 1;
}
.rd-banner-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 4px;
  letter-spacing: 0.02em;
}
.rd-banner-slogan {
  font-size: 1.1rem;
  font-weight: 600;
  color: #86efac;
  margin: 0 0 8px;
}
.rd-banner-sub {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

/* ===== 统计数据 ===== */
.rd-stats {
  margin: 0 !important;
}
.rd-stat-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 18px 20px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  height: 100%;
}
.rd-stat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border-color: #bfdbfe;
}
.rd-stat-card--primary {
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  border-color: #bfdbfe;
}
.rd-stat-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 6px;
  font-weight: 500;
}
.rd-stat-code-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rd-stat-code {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #1e40af;
  font-family: 'Courier New', Courier, monospace;
}
.rd-copy-btn {
  flex-shrink: 0;
  font-weight: 600;
}
.rd-stat-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.2;
}
.rd-stat-value--gold {
  color: #d97706;
}
.rd-stat-trend {
  font-size: 0.7rem;
  color: #22c55e;
  margin-top: 2px;
}

/* ===== 分享方式 ===== */
.rd-section {
  border-radius: 12px;
}
.rd-share-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 12px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}
.rd-share-item:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
  transform: translateY(-2px);
}
.rd-share-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  margin-bottom: 10px;
}
.rd-share-icon--wechat {
  background: #dcfce7;
  color: #16a34a;
}
.rd-share-icon--link {
  background: #dbeafe;
  color: var(--uj-brand, #4a9b8c);
}
.rd-share-icon--qq {
  background: #e0e7ff;
  color: #6366f1;
}
.rd-share-icon--sms {
  background: #fef3c7;
  color: #d97706;
}
.rd-share-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}
.rd-share-desc {
  font-size: 0.7rem;
  color: #94a3b8;
}

/* ===== 奖励进度 ===== */
.rd-progress-card {
  background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%);
}
.rd-progress-title {
  font-size: 1rem;
  font-weight: 700;
}
.rd-progress-subtitle {
  margin-left: 12px;
  font-size: 0.78rem;
  color: #64748b;
  font-weight: 400;
}
.rd-progress-steps {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  gap: 12px;
}
.rd-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  flex: 1;
  transition: all 0.2s;
}
.rd-step--done {
  border-color: #86efac;
  background: #f0fdf4;
}
.rd-step--current {
  border-color: #93c5fd;
  background: #eff6ff;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}
.rd-step-marker {
  flex-shrink: 0;
}
.rd-step-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}
.rd-step-icon--done {
  font-size: 1.3rem;
  color: #22c55e;
}
.rd-step-icon--current {
  font-size: 1.1rem;
  color: var(--uj-brand, #4a9b8c);
  animation: rd-spin 1s linear infinite;
}
.rd-step-icon--pending {
  background: #e2e8f0;
  color: #94a3b8;
}
@keyframes rd-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.rd-step-info {
  min-width: 0;
}
.rd-step-target {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
}
.rd-step-reward {
  font-size: 0.75rem;
  color: #64748b;
}
.rd-step-reward strong {
  color: #d97706;
}
.rd-progress-bar {
  margin-top: 4px;
}

/* ===== 排行榜 ===== */
.rd-rank-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rd-rank-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  transition: background 0.15s;
}
.rd-rank-item:hover {
  background: #f8fafc;
}
.rd-rank-item--top3 {
  background: linear-gradient(90deg, rgba(255, 215, 0, 0.06) 0%, transparent 100%);
}
.rd-rank-item--me {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.08) 0%, transparent 100%);
  border: 1px solid rgba(59, 130, 246, 0.15);
}
.rd-rank-pos {
  width: 36px;
  text-align: center;
  flex-shrink: 0;
}
.rd-rank-medal {
  display: inline-flex;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 800;
  color: #ffffff;
}
.rd-rank-medal--gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}
.rd-rank-medal--silver {
  background: linear-gradient(135deg, #94a3b8, #64748b);
}
.rd-rank-medal--bronze {
  background: linear-gradient(135deg, #cd7f32, #a0522d);
}
.rd-rank-num {
  font-size: 0.85rem;
  font-weight: 600;
  color: #94a3b8;
}
.rd-rank-company {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.rd-rank-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
}
.rd-rank-badge {
  font-size: 0.6rem;
  padding: 1px 8px;
  border-radius: 6px;
  background: #dbeafe;
  color: var(--uj-brand, #4a9b8c);
  font-weight: 600;
  flex-shrink: 0;
}
.rd-rank-count {
  flex-shrink: 0;
  text-align: right;
}
.rd-rank-count-num {
  font-size: 1rem;
  font-weight: 700;
  color: var(--uj-brand, #4a9b8c);
}
.rd-rank-count-label {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-left: 2px;
}
.rd-rank-empty {
  padding: 24px 0;
}

/* ===== Ant Design Overrides (deep) ===== */
.rd-section :deep(.ant-card-head) {
  border-bottom: 1px solid #f1f5f9;
  min-height: unset;
  padding: 14px 20px;
}
.rd-section :deep(.ant-card-head-title) {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
  padding: 0;
}
.rd-section :deep(.ant-card-body) {
  padding: 20px;
}
</style>
