/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="today-board client-dashboard tenant-theme">
    <!-- 顶部状态栏与导航 -->
    <header class="today-board__header">
      <div class="today-board__title-group">
        <div class="today-board__status-pill">
          <span class="status-dot"></span>
          <span>{{ greeting }} · 国际域名与询盘监听已就绪</span>
          <span v-if="payload.region_label" class="region-tag">{{ payload.region_label }}</span>
        </div>
        <h1 class="today-board__title">外贸出海经营总控大盘</h1>
        <p class="today-board__subtitle">
          {{ payload.headline || '外贸出海全链路闭环 · 覆盖独立站入站、社媒获客与全球买家履约' }}
        </p>
      </div>

      <div class="today-board__header-actions">
        <a-button class="action-btn-ghost" :loading="isRefreshing" @click="handleRefresh">
          <template #icon><SyncOutlined :spin="isRefreshing" /></template>
          刷新实况
        </a-button>
        <a-button class="action-btn-secondary" @click="router.push('/client/site-editor')">
          <template #icon><GlobalOutlined /></template>
          独立站配置
        </a-button>
        <a-button type="primary" class="action-btn-primary" @click="router.push('/client/dashboard')">
          <template #icon><AppstoreOutlined /></template>
          完整工作台 →
        </a-button>
      </div>
    </header>

    <!-- UniStore 风格 2×2 核心业务矩阵大盘 (Overview Performance Grid) -->
    <section class="today-board__kpi-matrix" aria-label="核心经营指标矩阵">
      <!-- KPI 1: 活跃询盘与商机 -->
      <div class="kpi-card" @click="router.push('/client/inquiries')">
        <div class="kpi-card__header">
          <span class="kpi-card__label">海外买家活跃询盘</span>
          <span class="kpi-card__badge kpi-badge--positive">
            <RiseOutlined /> +{{ stats.active_inquiries_growth }}%
          </span>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">
            {{ stats.active_inquiries }}
            <span class="kpi-card__unit">封</span>
          </div>
          <p class="kpi-card__hint">
            <strong>{{ stats.pending_response }}</strong> 封待及时响应 · 建议 30 分钟内 WhatsApp 直连
          </p>
        </div>
        <div class="kpi-card__footer">
          <div class="progress-bar">
            <div class="progress-bar__fill" :style="{ width: `${progressPct}%` }" />
          </div>
          <span class="progress-bar__text">今日履约三步完成 {{ payload.done_count ?? 0 }}/{{ payload.total_steps ?? 3 }}</span>
        </div>
      </div>

      <!-- KPI 2: 意向商机总估值 -->
      <div class="kpi-card" @click="router.push('/client/inquiries')">
        <div class="kpi-card__header">
          <span class="kpi-card__label">商机管道总预估值 (USD)</span>
          <span class="kpi-card__badge kpi-badge--info">
            <GlobalOutlined /> 覆盖 {{ stats.countries_count }} 国
          </span>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value tabular-nums">
            ${{ Number(stats.pipeline_value_usd).toLocaleString() }}
          </div>
          <p class="kpi-card__hint">
            综合转化率 <strong>{{ stats.conversion_rate }}%</strong> · 重点客群：海湾GCC与北美工程承包商
          </p>
        </div>
        <div class="kpi-card__footer">
          <span class="kpi-card__meta-link">查看外贸 7 步履约流水 →</span>
        </div>
      </div>

      <!-- KPI 3: 全网多渠道触达 -->
      <div class="kpi-card" @click="router.push('/client/distribute')">
        <div class="kpi-card__header">
          <span class="kpi-card__label">全网多渠道出海曝光</span>
          <span class="kpi-card__badge kpi-badge--indigo">
            <SendOutlined /> {{ stats.platforms_count }} 平台同步
          </span>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value tabular-nums">
            {{ Number(stats.multichannel_reach).toLocaleString() }}
            <span class="kpi-card__unit">次</span>
          </div>
          <p class="kpi-card__hint">
            支持 12 语种原声音色克隆与毫米级口型对齐，本周已排期 15 条
          </p>
        </div>
        <div class="kpi-card__footer">
          <span class="kpi-card__meta-link">前往社媒分发总控中心 →</span>
        </div>
      </div>

      <!-- KPI 4: 履约交付与单证 -->
      <div class="kpi-card" @click="router.push('/client/inquiries')">
        <div class="kpi-card__header">
          <span class="kpi-card__label">外贸履约与单证流</span>
          <span class="kpi-card__badge kpi-badge--warning">
            <ClockCircleOutlined /> {{ stats.production_count }} 笔排产中
          </span>
        </div>
        <div class="kpi-card__body">
          <div class="kpi-card__value">
            {{ stats.active_fulfillment_orders }}
            <span class="kpi-card__unit">笔在单</span>
          </div>
          <p class="kpi-card__hint">
            形式发票(PI) 2 笔待签章 · 商业发票与装箱单 1 笔合规生成
          </p>
        </div>
        <div class="kpi-card__footer">
          <span class="kpi-card__meta-link">单证一键套打中枢 →</span>
        </div>
      </div>
    </section>

    <!-- 中部双翼协同：左翼外贸三步行动闭环 + 右翼 UniStore 签名就绪度罗盘 -->
    <section class="today-board__middle-grid">
      <!-- 左翼：外贸启航与每日履约关键三步 -->
      <div class="action-pipeline-card">
        <div class="section-heading">
          <div>
            <span class="section-kicker">EXECUTION PIPELINE</span>
            <h2 class="section-title">外贸启航与每日履约闭环</h2>
          </div>
          <span class="pipeline-progress-badge">
            闭环进度：{{ progressPct }}%
          </span>
        </div>

        <div class="steps-flow">
          <div
            v-for="(step, idx) in steps"
            :key="step.id"
            class="step-item"
            :class="{
              'step-item--done': step.done,
              'step-item--active': step.id === payload.next_step_id && !step.done,
              'step-item--waiting': step.id !== payload.next_step_id && !step.done,
            }"
          >
            <!-- 步骤标志序号 -->
            <div class="step-marker">
              <CheckOutlined v-if="step.done" />
              <span v-else>0{{ step.order }}</span>
            </div>

            <!-- 步骤正文 -->
            <div class="step-content">
              <div class="step-header">
                <div>
                  <h3 class="step-title">
                    {{ step.title }}
                    <span v-if="step.done" class="step-status-tag step-status-tag--done">已就绪</span>
                    <span v-else-if="step.id === payload.next_step_id" class="step-status-tag step-status-tag--active">建议推进</span>
                  </h3>
                  <p class="step-subtitle">{{ step.subtitle }}</p>
                </div>
                <div class="step-actions">
                  <a-button
                    size="small"
                    :type="step.id === payload.next_step_id ? 'primary' : 'default'"
                    class="step-primary-btn"
                    @click="router.push(step.route)"
                  >
                    {{ step.cta }}
                  </a-button>
                  <a-button
                    v-if="step.alt_route"
                    size="small"
                    type="link"
                    class="step-alt-btn"
                    @click="router.push(step.alt_route)"
                  >
                    {{ altLinkLabel(step) }}
                  </a-button>
                </div>
              </div>
              <p class="step-hint">{{ step.hint }}</p>
            </div>

            <!-- 连线 -->
            <div v-if="idx < steps.length - 1" class="step-connector" />
          </div>
        </div>
      </div>

      <!-- 右翼：UniStore 签名半圆外贸就绪度罗盘 (Global Trade Readiness Compass) -->
      <div class="readiness-compass-card">
        <div class="section-heading">
          <div>
            <span class="section-kicker">READINESS INDEX</span>
            <h2 class="section-title">外贸出海就绪度</h2>
          </div>
          <span class="grade-badge">L-PRO 认证</span>
        </div>

        <!-- 半圆 SVG 仪表盘 -->
        <div class="compass-chart-wrap">
          <svg class="compass-svg" viewBox="0 0 200 120">
            <!-- 底轨灰弧 -->
            <path
              d="M 25 105 A 75 75 0 0 1 175 105"
              fill="none"
              stroke="#e2e8f0"
              stroke-width="14"
              stroke-linecap="round"
            />
            <!-- 高光主弧（平台薄荷 #4a9b8c） -->
            <path
              d="M 25 105 A 75 75 0 0 1 175 105"
              fill="none"
              stroke="#4a9b8c"
              stroke-width="14"
              stroke-linecap="round"
              stroke-dasharray="235.6"
              :stroke-dashoffset="compassOffset"
              class="compass-fill-arc"
            />
          </svg>
          <div class="compass-center-info">
            <span class="compass-score tabular-nums">{{ stats.readiness_score }}%</span>
            <span class="compass-score-label">全链路健康度</span>
          </div>
        </div>

        <!-- 细分市场渗透与分布条 -->
        <div class="market-shares">
          <div class="market-item">
            <div class="market-item__head">
              <span class="market-item__name">🇪🇺 🇺🇸 北美与欧洲市场</span>
              <span class="market-item__pct">42% · $119,500</span>
            </div>
            <div class="market-item__bar">
              <div class="market-item__fill" style="width: 42%; background-color: #4a9b8c;" />
            </div>
          </div>

          <div class="market-item">
            <div class="market-item__head">
              <span class="market-item__name">🇦🇪 🇸🇦 中东及海湾市场 (GCC)</span>
              <span class="market-item__pct">35% · $99,500</span>
            </div>
            <div class="market-item__bar">
              <div class="market-item__fill" style="width: 35%; background-color: #5eb8a8;" />
            </div>
          </div>

          <div class="market-item">
            <div class="market-item__head">
              <span class="market-item__name">🇻🇳 🇧🇷 东南亚与新兴市场</span>
              <span class="market-item__pct">23% · $65,500</span>
            </div>
            <div class="market-item__bar">
              <div class="market-item__fill" style="width: 23%; background-color: #60a5fa;" />
            </div>
          </div>
        </div>

        <div class="compass-audit-note">
          <CheckCircleFilled class="audit-icon" />
          <span>独立站 SEO 国际排名称重与 WhatsApp 响应时效优于同行业 <strong>92%</strong> 卖家</span>
        </div>
      </div>
    </section>

    <!-- 底部：Ramp / Mercury 级高密度海外买家询盘与交易流水大表 -->
    <section class="today-board__inquiries-section">
      <div class="inquiries-card">
        <div class="inquiries-card__head">
          <div>
            <span class="section-kicker">LIVE INQUIRY STREAM</span>
            <h2 class="section-title">实盘海外买家询盘与商机流水</h2>
            <p class="inquiries-desc">
              来源于独立站入站、社媒矩阵及 WhatsApp 直通商机，支持一键双向翻译与 PI 套打
            </p>
          </div>

          <!-- 过滤器 Tab -->
          <div class="inquiries-filter-tabs">
            <button
              v-for="tab in filterTabs"
              :key="tab.key"
              type="button"
              class="filter-tab-btn"
              :class="{ 'filter-tab-btn--active': activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span class="filter-tab-count">{{ tab.count }}</span>
            </button>
          </div>
        </div>

        <!-- 高密度数据表 (Ramp / Mercury 极简细线表) -->
        <div class="inquiries-table-wrapper">
          <table class="inquiries-table">
            <thead>
              <tr>
                <th>采购商与国别</th>
                <th>询求建材品类与 22 参数规格</th>
                <th>预估金额 (USD)</th>
                <th>来源获客渠道</th>
                <th>商机履约阶段</th>
                <th class="text-right">极速行动</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredInquiries"
                :key="item.id"
                class="inquiry-row"
                :class="{ 'inquiry-row--unread': item.unread }"
              >
                <!-- 采购商 -->
                <td class="cell-buyer">
                  <div class="buyer-info">
                    <span class="buyer-flag">{{ item.flag }}</span>
                    <div>
                      <div class="buyer-name-line">
                        <span class="buyer-name">{{ item.buyer_name }}</span>
                        <span v-if="item.unread" class="unread-dot" title="未读商机"></span>
                      </div>
                      <span class="buyer-company">{{ item.company }}</span>
                    </div>
                  </div>
                </td>

                <!-- 品类规格 -->
                <td class="cell-spec">
                  <span class="category-name">{{ item.category }}</span>
                  <span class="spec-detail">{{ item.spec }}</span>
                </td>

                <!-- 金额 -->
                <td class="cell-amount tabular-nums">
                  ${{ item.est_value_usd.toLocaleString() }}
                </td>

                <!-- 渠道 -->
                <td class="cell-channel">
                  <span class="channel-pill" :class="`channel-pill--${item.channel}`">
                    <span v-if="item.channel === 'whatsapp'" class="channel-dot whatsapp-dot"></span>
                    <span v-else-if="item.channel === 'website'" class="channel-dot website-dot"></span>
                    <span v-else-if="item.channel === 'linkedin'" class="channel-dot linkedin-dot"></span>
                    <span v-else class="channel-dot other-dot"></span>
                    {{ channelLabel(item.channel) }}
                  </span>
                </td>

                <!-- 状态 -->
                <td class="cell-status">
                  <span class="status-badge" :class="`status-badge--${item.status}`">
                    {{ item.status_label }}
                  </span>
                  <span class="time-hint">{{ item.time }}</span>
                </td>

                <!-- 操作 -->
                <td class="cell-actions text-right">
                  <div class="actions-group">
                    <a-button
                      size="small"
                      class="btn-action-whatsapp"
                      @click="handleWhatsApp(item)"
                    >
                      <svg class="whatsapp-icon" viewBox="0 0 24 24" width="13" height="13" fill="currentColor">
                        <path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2m.01 1.67c4.54 0 8.24 3.7 8.24 8.24 0 2.2-.86 4.27-2.42 5.82a8.196 8.196 0 0 1-5.82 2.41c-1.46 0-2.89-.39-4.14-1.12l-.3-.18-3.12.82.83-3.04-.2-.31a8.216 8.216 0 0 1-1.26-4.4c0-4.54 3.7-8.24 8.24-8.24m4.54 11.66c-.25-.13-1.47-.72-1.7-.81-.23-.08-.39-.13-.56.13-.17.25-.64.81-.79.97-.14.17-.29.19-.54.06-.25-.13-1.06-.39-2.02-1.25-.75-.67-1.26-1.5-1.41-1.75-.14-.25-.02-.39.11-.51.11-.11.25-.29.37-.44.13-.14.17-.25.25-.42.08-.17.04-.31-.02-.44-.06-.13-.56-1.34-.76-1.84-.2-.49-.4-.42-.56-.43h-.48c-.17 0-.44.06-.67.31-.23.25-.88.86-.88 2.1 0 1.24.9 2.45 1.03 2.62.13.17 1.77 2.7 4.29 3.79.6.26 1.07.41 1.44.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.15-1.18-.06-.11-.23-.17-.48-.29" />
                      </svg>
                      WhatsApp 直连
                    </a-button>
                    <a-button
                      size="small"
                      class="btn-action-quote"
                      @click="router.push('/client/inquiries')"
                    >
                      核价 / 开 PI
                    </a-button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 底部提示与跳转 -->
        <div class="inquiries-card__foot">
          <span class="honesty-label">
            {{ payload.weekly_inquiries?.honest_note || '真实入库海外买家询盘流；系统 7×24 小时全天候多渠道监听中。' }}
          </span>
          <a-button type="link" class="btn-all-inquiries" @click="router.push('/client/inquiries')">
            查看全部 {{ stats.active_inquiries }} 封历史询盘与外贸 7 步履约单证 →
          </a-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  AppstoreOutlined,
  CheckCircleFilled,
  CheckOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  RiseOutlined,
  SendOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

import { useClientTodayThree } from '@/composables/useClientTodayThree';
import type { TodayThreeStep, TradeInquiryItem } from '@/composables/useClientTodayThree';

const router = useRouter();
const { payload, steps, progressPct, tradeStats, recentInquiries, load, refresh } = useClientTodayThree();

const isRefreshing = ref(false);
const activeTab = ref<'all' | 'pending' | 'quoted' | 'production'>('all');

const stats = computed(() => tradeStats.value);

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return '上午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

// 半圆罗盘偏移量计算：周长 235.6，根据就绪度百分比计算 dashoffset
const compassOffset = computed(() => {
  const score = Math.max(0, Math.min(100, stats.value.readiness_score || 88));
  const fullLength = 235.6;
  return fullLength - (fullLength * score) / 100;
});

const filterTabs = computed(() => {
  const list = recentInquiries.value;
  return [
    { key: 'all' as const, label: '全部询盘', count: list.length },
    { key: 'pending' as const, label: '待响应 RFQ', count: list.filter((i) => i.status === 'new').length },
    { key: 'quoted' as const, label: '已核价 / 发 PI', count: list.filter((i) => i.status === 'quoted' || i.status === 'pi_sent').length },
    { key: 'production' as const, label: '排产履约中', count: list.filter((i) => i.status === 'in_production').length },
  ];
});

const filteredInquiries = computed(() => {
  const list = recentInquiries.value;
  if (activeTab.value === 'pending') {
    return list.filter((i) => i.status === 'new');
  }
  if (activeTab.value === 'quoted') {
    return list.filter((i) => i.status === 'quoted' || i.status === 'pi_sent');
  }
  if (activeTab.value === 'production') {
    return list.filter((i) => i.status === 'in_production');
  }
  return list;
});

function altLinkLabel(step: TodayThreeStep) {
  if (step.id === 'product') return '产业带候选导入 →';
  if (step.id === 'content') return '多平台矩阵排期 →';
  return '履约单证中枢 →';
}

function channelLabel(channel: string) {
  switch (channel) {
    case 'whatsapp':
      return 'WhatsApp 直达';
    case 'website':
      return '独立站 Google SEO';
    case 'linkedin':
      return 'LinkedIn 采购商';
    case 'tiktok':
      return 'TikTok 矩阵出海';
    default:
      return '国际买家直通';
  }
}

async function handleRefresh() {
  isRefreshing.value = true;
  try {
    await refresh();
    message.success('大盘数据已同步至最新状态');
  } catch {
    message.warning('已加载本地经营大盘缓存');
  } finally {
    isRefreshing.value = false;
  }
}

function handleWhatsApp(item: TradeInquiryItem) {
  if (item.whatsapp_number) {
    const cleanNum = item.whatsapp_number.replace(/[^0-9]/g, '');
    const text = encodeURIComponent(
      `Hello ${item.buyer_name}, this is regarding your inquiry about ${item.category} (${item.spec}). We have prepared the official specification sheet and quotation.`,
    );
    window.open(`https://wa.me/${cleanNum}?text=${text}`, '_blank');
  } else {
    router.push('/client/inquiries');
  }
}

onMounted(() => {
  void load();
});

onActivated(() => {
  void refresh();
});
</script>

<style scoped lang="scss">
/* ==========================================================================
   UniStore + Ramp 顶流现代高质感视觉体系
   单一主强调色：平台薄荷 (#4a9b8c，DESIGN-TOKEN-LOCK 单真源)
   排版底色：Mercury/Apple 白底 (#FFFFFF) + 极简发丝细边 (#E2E8F0)
   零粗暴大阴影 · 零脏毛玻璃 · 零渐变大字
   ========================================================================== */

$brand-blue: var(--color-primary, #4a9b8c);
$brand-blue-hover: var(--color-primary-dark, #2a6b60);
$brand-blue-light: var(--color-primary-light, #e8faf4);
$brand-blue-border: #d3ede6;

$accent-orange: #ea580c;
$accent-orange-light: #fff7ed;
$accent-orange-border: #ffedd5;

$accent-emerald: #10b981;
$accent-emerald-light: #ecfdf5;

$text-primary: #0f172a;
$text-secondary: #334155;
$text-muted: #64748b;
$text-light: #94a3b8;

$surface: #ffffff;
$page-bg: #f8fafc;
$border-color: #e2e8f0;
$border-subtle: #f1f5f9;

.today-board {
  width: 100%;
  min-height: 100%;
  padding: 24px 28px 48px;
  background-color: $page-bg;
  color: $text-primary;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  box-sizing: border-box;
}

/* 顶部状态栏 */
.today-board__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.today-board__status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #ffffff;
  border: 1px solid $border-color;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  color: $text-muted;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: $accent-emerald;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }

  .region-tag {
    padding: 1px 6px;
    background: $border-subtle;
    border-radius: 4px;
    font-size: 11px;
    color: $text-secondary;
  }
}

.today-board__title {
  margin: 10px 0 0;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: $text-primary;
  line-height: 1.2;
}

.today-board__subtitle {
  margin: 6px 0 0;
  font-size: 13.5px;
  color: $text-muted;
  line-height: 1.5;
}

.today-board__header-actions {
  display: flex;
  align-items: center;
  gap: 10px;

  .action-btn-ghost {
    background: #ffffff;
    border-color: $border-color;
    color: $text-secondary;
    font-weight: 500;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);

    &:hover {
      color: $brand-blue;
      border-color: $brand-blue;
    }
  }

  .action-btn-secondary {
    background: #ffffff;
    border-color: $border-color;
    color: $text-primary;
    font-weight: 500;
    border-radius: 8px;

    &:hover {
      color: $brand-blue;
      border-color: $brand-blue;
    }
  }

  .action-btn-primary {
    background-color: $brand-blue !important;
    border-color: $brand-blue !important;
    font-weight: 600;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(37, 99, 235, 0.25);

    &:hover {
      background-color: $brand-blue-hover !important;
      border-color: $brand-blue-hover !important;
    }
  }
}

/* ==========================================================================
   2×2 核心业务矩阵大盘 (UniStore 签名版)
   ========================================================================== */
.today-board__kpi-matrix {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 1100px) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.kpi-card {
  background: $surface;
  border: 1px solid $border-color;
  border-radius: 14px;
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  &:hover {
    border-color: #cbd5e1;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
  }

  &__label {
    font-size: 13px;
    font-weight: 600;
    color: $text-muted;
  }

  &__badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
  }

  .kpi-badge--positive {
    background-color: $accent-emerald-light;
    color: #047857;
  }

  .kpi-badge--info {
    background-color: $brand-blue-light;
    color: $brand-blue;
  }

  .kpi-badge--indigo {
    background-color: #f5f3ff;
    color: #6366f1;
  }

  .kpi-badge--warning {
    background-color: $accent-orange-light;
    color: #c2410c;
  }

  &__value {
    font-size: 30px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: $text-primary;
    line-height: 1.15;
  }

  &__unit {
    font-size: 14px;
    font-weight: 500;
    color: $text-muted;
    margin-left: 2px;
  }

  &__hint {
    margin: 8px 0 0;
    font-size: 12px;
    color: $text-muted;
    line-height: 1.45;

    strong {
      color: $text-primary;
    }
  }

  &__footer {
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid $border-subtle;
  }

  &__meta-link {
    font-size: 12px;
    font-weight: 500;
    color: $brand-blue;

    &:hover {
      text-decoration: underline;
    }
  }
}

.progress-bar {
  width: 100%;
  height: 5px;
  background-color: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;

  &__fill {
    height: 100%;
    background-color: $brand-blue;
    border-radius: 9999px;
    transition: width 0.3s ease;
  }

  &__text {
    display: block;
    margin-top: 6px;
    font-size: 11px;
    font-weight: 500;
    color: $text-muted;
  }
}

/* ==========================================================================
   中部双翼协同网格
   ========================================================================== */
.today-board__middle-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin-bottom: 24px;

  @media (min-width: 980px) {
    grid-template-columns: 1fr 340px;
  }

  @media (min-width: 1280px) {
    grid-template-columns: 1fr 380px;
  }
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.section-kicker {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: $brand-blue;
  text-transform: uppercase;
}

.section-title {
  margin: 4px 0 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: $text-primary;
}

/* 左翼：三步行动闭环卡片 */
.action-pipeline-card {
  background: $surface;
  border: 1px solid $border-color;
  border-radius: 14px;
  padding: 22px 24px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.pipeline-progress-badge {
  display: inline-block;
  padding: 3px 10px;
  background-color: $brand-blue-light;
  border: 1px solid $brand-blue-border;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: $brand-blue;
}

.steps-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.step-item {
  position: relative;
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  background-color: #fafbfc;
  transition: all 0.2s ease;

  &--active {
    background-color: #ffffff;
    border-color: $brand-blue-border;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);

    .step-marker {
      background-color: $brand-blue;
      color: #ffffff;
      border-color: $brand-blue;
    }
  }

  &--done {
    background-color: #f8fafc;

    .step-marker {
      background-color: $accent-emerald-light;
      color: #047857;
      border-color: #a7f3d0;
    }
  }

  &--waiting {
    opacity: 0.85;
  }
}

.step-marker {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background-color: #ffffff;
  border: 1px solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: $text-muted;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.step-connector {
  position: absolute;
  left: 35px;
  top: 56px;
  bottom: -16px;
  width: 2px;
  background-color: #e2e8f0;
  z-index: 1;
}

.step-content {
  min-width: 0;
}

.step-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.step-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: $text-primary;
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-status-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;

  &--done {
    background-color: $accent-emerald-light;
    color: #047857;
  }

  &--active {
    background-color: $accent-orange-light;
    color: #c2410c;
  }
}

.step-subtitle {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: $text-secondary;
  line-height: 1.45;
}

.step-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 8px;

  .step-primary-btn {
    font-weight: 600;
    border-radius: 6px;
  }

  .step-alt-btn {
    color: $brand-blue !important;
    font-size: 12px;
    padding: 0 4px;
  }
}

/* 右翼：UniStore 签名半圆就绪度罗盘 */
.readiness-compass-card {
  background: $surface;
  border: 1px solid $border-color;
  border-radius: 14px;
  padding: 22px 20px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.grade-badge {
  padding: 2px 8px;
  background-color: #f1f5f9;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: $text-secondary;
}

.compass-chart-wrap {
  position: relative;
  width: 100%;
  max-width: 220px;
  margin: 4px auto 14px;
  text-align: center;
}

.compass-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.compass-fill-arc {
  transition: stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.compass-center-info {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.compass-score {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: $text-primary;
  line-height: 1;
}

.compass-score-label {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 600;
  color: $text-muted;
}

.market-shares {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0 16px;
}

.market-item {
  &__head {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 4px;
  }

  &__name {
    font-weight: 500;
    color: $text-secondary;
  }

  &__pct {
    font-weight: 600;
    color: $text-muted;
    font-variant-numeric: tabular-nums;
  }

  &__bar {
    width: 100%;
    height: 6px;
    background-color: #f1f5f9;
    border-radius: 9999px;
    overflow: hidden;
  }

  &__fill {
    height: 100%;
    border-radius: 9999px;
    transition: width 0.4s ease;
  }
}

.compass-audit-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid $border-subtle;
  font-size: 11.5px;
  line-height: 1.45;
  color: $text-muted;

  .audit-icon {
    color: $accent-emerald;
    font-size: 13px;
    margin-top: 2px;
    shrink: 0;
  }

  strong {
    color: $text-primary;
  }
}

/* ==========================================================================
   底部：Ramp / Mercury 级高密度海外买家询盘流水大表
   ========================================================================== */
.today-board__inquiries-section {
  width: 100%;
}

.inquiries-card {
  background: $surface;
  border: 1px solid $border-color;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  overflow: hidden;

  &__head {
    padding: 20px 24px 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid $border-color;
  }
}

.inquiries-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: $text-muted;
}

.inquiries-filter-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
}

.filter-tab-btn {
  border: none;
  background: transparent;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 500;
  color: $text-muted;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;

  &:hover {
    color: $text-primary;
  }

  &--active {
    background-color: #ffffff;
    color: $brand-blue;
    font-weight: 600;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  }

  .filter-tab-count {
    padding: 1px 5px;
    background-color: rgba(15, 23, 42, 0.06);
    border-radius: 9999px;
    font-size: 11px;
  }

  &--active .filter-tab-count {
    background-color: $brand-blue-light;
    color: $brand-blue;
  }
}

/* 高密度数据表样式 */
.inquiries-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.inquiries-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;

  thead th {
    padding: 12px 20px;
    font-size: 11.5px;
    font-weight: 600;
    color: $text-muted;
    background-color: #f8fafc;
    border-bottom: 1px solid $border-color;
    white-space: nowrap;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  tbody tr {
    border-bottom: 1px solid $border-color;
    transition: background-color 0.15s ease;

    &:hover {
      background-color: #f8fafc;
    }

    &:last-child {
      border-bottom: none;
    }
  }

  tbody td {
    padding: 14px 20px;
    vertical-align: middle;
  }
}

.cell-buyer {
  .buyer-info {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .buyer-flag {
    font-size: 20px;
    line-height: 1;
  }

  .buyer-name-line {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .buyer-name {
    font-weight: 600;
    color: $text-primary;
  }

  .unread-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: $brand-blue;
  }

  .buyer-company {
    display: block;
    font-size: 11.5px;
    color: $text-muted;
    margin-top: 2px;
  }
}

.cell-spec {
  max-width: 260px;

  .category-name {
    display: block;
    font-weight: 600;
    color: $text-primary;
  }

  .spec-detail {
    display: block;
    font-size: 11.5px;
    color: $text-muted;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.cell-amount {
  font-weight: 700;
  font-size: 14px;
  color: $text-primary;
  letter-spacing: -0.01em;
}

.cell-channel {
  .channel-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 500;
  }

  .channel-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  .channel-pill--whatsapp {
    background-color: #f0fdf4;
    color: #166534;
    border: 1px solid #dcfce7;
    .whatsapp-dot { background-color: #22c55e; }
  }

  .channel-pill--website {
    background-color: $brand-blue-light;
    color: $brand-blue;
    border: 1px solid $brand-blue-border;
    .website-dot { background-color: $brand-blue; }
  }

  .channel-pill--linkedin {
    background-color: #f5f3ff;
    color: #5b21b6;
    border: 1px solid #ede9fe;
    .linkedin-dot { background-color: #7c3aed; }
  }

  .channel-pill--tiktok {
    background-color: #f8fafc;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    .other-dot { background-color: #0f172a; }
  }
}

.cell-status {
  .status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }

  .status-badge--new {
    background-color: $accent-orange-light;
    color: #c2410c;
  }

  .status-badge--quoted {
    background-color: $brand-blue-light;
    color: $brand-blue;
  }

  .status-badge--pi_sent {
    background-color: #f5f3ff;
    color: #6366f1;
  }

  .status-badge--in_production {
    background-color: $accent-emerald-light;
    color: #047857;
  }

  .time-hint {
    display: block;
    margin-top: 3px;
    font-size: 11px;
    color: $text-light;
  }
}

.cell-actions {
  white-space: nowrap;

  .actions-group {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .btn-action-whatsapp {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background-color: #22c55e;
    border-color: #22c55e;
    color: #ffffff;
    font-weight: 600;
    border-radius: 6px;

    &:hover {
      background-color: #16a34a !important;
      border-color: #16a34a !important;
      color: #ffffff !important;
    }

    .whatsapp-icon {
      fill: currentColor;
    }
  }

  .btn-action-quote {
    font-weight: 500;
    border-radius: 6px;
    border-color: $border-color;
    color: $text-secondary;

    &:hover {
      color: $brand-blue;
      border-color: $brand-blue;
    }
  }
}

.inquiries-card__foot {
  padding: 14px 20px;
  background-color: #f8fafc;
  border-top: 1px solid $border-color;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  .honesty-label {
    font-size: 12px;
    color: $text-muted;
  }

  .btn-all-inquiries {
    color: $brand-blue !important;
    font-weight: 600;
    font-size: 12.5px;
    padding: 0;
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.text-right {
  text-align: right;
}

@media (max-width: 640px) {
  .today-board {
    padding: 16px 14px 32px;
  }

  .today-board__title {
    font-size: 22px;
  }

  .today-board__header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .step-item {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .step-connector {
    display: none;
  }
}
</style>
