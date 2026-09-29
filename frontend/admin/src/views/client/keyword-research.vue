/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="关键词热度查询 & 谷歌外贸热榜"
    subtitle="内嵌 SEMrush/Google 数据网关 · 零搜索量熔断拦截 · 谷歌外贸高热排行榜"
    surface="elevated"
    class="keyword-research-page"
  >
    <!-- 顶部操作区 -->
    <template #actions>
      <a-space>
        <a-button @click="router.push('/client/seo-keywords')">产业带词库</a-button>
        <a-button @click="router.push('/client/growth-tools')">增长跑盘台</a-button>
      </a-space>
    </template>

    <a-tabs v-model:activeKey="activeTab" class="keyword-research-tabs">
      <!-- TAB 1: 实时热度查询与零搜索量防护 -->
      <a-tab-pane key="search" tab="实时热度探测 & 零搜索量防护">
        <div class="space-y-6 pt-2">
          <!-- 搜索栏主卡片 -->
          <a-card class="search-hero-card" :bordered="false">
            <div class="max-w-4xl mx-auto py-2">
              <div class="flex flex-col sm:flex-row gap-3 items-center">
                <a-select
                  v-model:value="targetCountry"
                  style="width: 230px"
                  size="large"
                  :options="countryOptions"
                  @change="handleSearch"
                />
                <a-input-search
                  v-model:value="keywordInput"
                  placeholder="中国卖家可直接输入中文（如: 岩棉板、断桥铝、金属缠绕垫），系统全自动置换为目标国母语搜索词..."
                  enter-button="查询热度 & 自动置换"
                  size="large"
                  :loading="loading"
                  class="flex-1"
                  @search="handleSearch"
                />
              </div>

              <!-- 快速推荐热门词 -->
              <div class="mt-4 flex flex-wrap items-center gap-2 text-xs">
                <span class="text-gray-500 font-medium">推荐热搜：</span>
                <span
                  v-for="kw in quickKeywords"
                  :key="kw"
                  class="quick-kw-tag"
                  @click="pickQuickKeyword(kw)"
                >
                  {{ kw }}
                </span>
              </div>
            </div>
          </a-card>

          <!-- 查询中加载状态 -->
          <div v-if="loading" class="py-16 text-center">
            <a-spin size="large" tip="正在调取 SEMrush/Google 全球搜索数据与零搜索量安全门禁..." />
          </div>

          <!-- 分析结果面板 -->
          <div v-else-if="result" class="space-y-6">
            <!-- 🌐【海外母语智能置换提示牌】：中文意图 ➔ 目标国买家搜索词 -->
            <div
              v-if="result.transmutation?.is_transmuted"
              class="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-300 rounded-xl p-4 shadow-sm"
            >
              <div class="flex items-start gap-3">
                <GlobalOutlined class="text-emerald-600 text-xl mt-0.5" />
                <div class="flex-1">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="font-bold text-gray-900 text-sm">🌐【海外采购商母语自动置换成功】</span>
                      <a-tag color="success">系统全自动置换</a-tag>
                    </div>
                    <a-button type="link" size="small" class="text-emerald-700 font-bold p-0" @click="showMatrixModal = true">
                      查看全球 7 国母语置换矩阵 ➔
                    </a-button>
                  </div>
                  <p class="text-xs text-gray-700 mt-1.5 leading-relaxed">
                    {{ result.transmutation.transmutation_reason }}
                  </p>
                  <div class="mt-2.5 flex flex-wrap items-center gap-3 text-xs bg-white/90 p-2.5 rounded-lg border border-emerald-100">
                    <span class="text-gray-500">中国输入意图：<strong class="text-gray-900 font-bold">{{ result.transmutation.original_input }}</strong></span>
                    <span class="text-emerald-600 font-bold">➔ 自动置换目标国搜索词：</span>
                    <span class="bg-emerald-600 text-white font-bold px-2.5 py-0.5 rounded text-xs shadow-sm">
                      {{ result.transmutation.transmuted_keyword }}
                    </span>
                    <span class="text-gray-600 font-medium">({{ result.transmutation.target_country_name }} · {{ result.transmutation.target_language_name }})</span>
                    <span class="ml-auto text-emerald-800 font-bold">Google 当地月搜量：{{ formatNumber(result.search_volume) }} 次/月</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- 🚫【硬规则警告】：零搜索量死词熔断拦截卡片 -->
            <div
              v-if="result.zero_volume_guard?.is_prohibited"
              class="bg-rose-50 border-2 border-rose-400 rounded-xl p-5 shadow-sm"
            >
              <div class="flex items-start gap-3">
                <WarningOutlined class="text-rose-600 text-2xl mt-0.5" />
                <div class="flex-1">
                  <div class="flex items-center justify-between">
                    <h3 class="text-base font-bold text-rose-800">
                      {{ result.zero_volume_guard.title }}
                    </h3>
                    <a-tag color="error" class="font-bold">系统强行拦截</a-tag>
                  </div>
                  <p class="text-xs text-rose-700 mt-1 leading-relaxed">
                    {{ result.zero_volume_guard.message }}
                  </p>
                  <ul class="text-xs text-rose-600 mt-2 list-disc list-inside space-y-0.5">
                    <li v-for="(reason, idx) in result.zero_volume_guard.reasons" :key="idx">
                      {{ reason }}
                    </li>
                  </ul>

                  <!-- 推荐采纳的高热替代词 -->
                  <div class="mt-4 pt-3 border-t border-rose-200">
                    <p class="text-xs font-semibold text-rose-900 mb-2">
                      💡 严禁将死词设为核心推广词！为您自动推荐 Google 官方真实高热黄金词（点击即可一键采纳）：
                    </p>
                    <div class="flex flex-wrap gap-2">
                      <a-button
                        v-for="alt in result.zero_volume_guard.suggested_alternatives"
                        :key="alt.keyword"
                        size="small"
                        type="dashed"
                        class="border-rose-300 text-rose-800 hover:border-primary hover:text-primary"
                        @click="adoptAlternative(alt.keyword)"
                      >
                        {{ alt.keyword }} (月搜 {{ alt.search_volume.toLocaleString() }} · {{ alt.cpc }})
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据源透明标示牌 -->
            <div class="flex items-center justify-between px-1 text-xs text-gray-500">
              <div class="flex items-center gap-2">
                <span>权威数据源：</span>
                <a-tag color="green">{{ result.data_source_label }}</a-tag>
                <span v-if="result.zero_volume_guard?.is_prohibited" class="text-rose-600 font-medium">
                  [已熔断拦截零搜索量]
                </span>
                <span v-else class="text-emerald-600 font-medium">
                  [Google 搜索量真实合规]
                </span>
              </div>
              <span>分析时间：{{ formatDate(result.analyzed_at) }}</span>
            </div>

            <!-- 四大核心指标卡片 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <!-- 热度指数 -->
              <div class="stat-card bg-white border border-gray-100 shadow-sm p-4 rounded-xl">
                <div class="flex items-center justify-between text-gray-500 text-sm">
                  <span>全网热度指数</span>
                  <FireOutlined class="text-rose-500 text-lg" />
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                  <span class="text-3xl font-bold text-gray-900">{{ result.heat_index }}</span>
                  <span class="text-xs text-gray-400">/ 100</span>
                  <a-tag :color="result.heat_index >= 70 ? 'red' : 'orange'" class="ml-auto">
                    {{ result.heat_index >= 70 ? '高热度需求' : (result.heat_index < 30 ? '极低热度' : '稳健关注') }}
                  </a-tag>
                </div>
              </div>

              <!-- 月度搜索量 -->
              <div class="stat-card bg-white border border-gray-100 shadow-sm p-4 rounded-xl">
                <div class="flex items-center justify-between text-gray-500 text-sm">
                  <span>Google 月度搜索需求</span>
                  <SearchOutlined class="text-primary text-lg" />
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                  <span class="text-3xl font-bold text-gray-900">{{ formatNumber(result.search_volume) }}</span>
                  <span class="text-xs text-gray-400">次/月</span>
                  <span v-if="result.search_volume > 0" class="text-xs text-emerald-600 font-medium ml-auto">真实采购寻源</span>
                  <span v-else class="text-xs text-rose-600 font-bold ml-auto">0 搜索量死词</span>
                </div>
              </div>

              <!-- 竞争激烈度 -->
              <div class="stat-card bg-white border border-gray-100 shadow-sm p-4 rounded-xl">
                <div class="flex items-center justify-between text-gray-500 text-sm">
                  <span>竞争激烈程度 (KD)</span>
                  <ThunderboltOutlined class="text-amber-500 text-lg" />
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                  <span class="text-3xl font-bold text-gray-900">{{ result.competition_index }}</span>
                  <span class="text-xs text-gray-400">/ 100</span>
                  <a-tag :color="getDifficultyColor(result.difficulty_level)" class="ml-auto">
                    {{ result.difficulty_label }}
                  </a-tag>
                </div>
              </div>

              <!-- 建议出价 CPC -->
              <div class="stat-card bg-white border border-gray-100 shadow-sm p-4 rounded-xl">
                <div class="flex items-center justify-between text-gray-500 text-sm">
                  <span>商业出价 (CPC)</span>
                  <DollarOutlined class="text-blue-500 text-lg" />
                </div>
                <div class="mt-2 flex items-baseline gap-2">
                  <span class="text-3xl font-bold text-gray-900">{{ result.cpc }}</span>
                  <span class="text-xs text-gray-400">/点击</span>
                  <a-tag color="blue" class="ml-auto">{{ result.cpc_value > 0 ? '高商业价值' : '无商业价值' }}</a-tag>
                </div>
              </div>
            </div>

            <!-- 趋势图与区域需求图表 -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <!-- 12 个月搜索热度趋势折线图 -->
              <div class="lg:col-span-7 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h3 class="text-base font-semibold text-gray-900">12个月 Google 搜索热度趋势</h3>
                    <p class="text-xs text-gray-400 mt-0.5">高亮外贸出海与采购旺季周期波动</p>
                  </div>
                  <a-tag color="cyan">外贸双旺季</a-tag>
                </div>
                <div class="h-64">
                  <v-chart :option="trendChartOption" autoresize />
                </div>
              </div>

              <!-- 核心需求市场与国家分布 -->
              <div class="lg:col-span-5 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h3 class="text-base font-semibold text-gray-900">核心采购国家 / 区域分布</h3>
                    <p class="text-xs text-gray-400 mt-0.5">主要海外买家所在地与增长势头</p>
                  </div>
                  <span class="text-xs text-gray-400">需求占比</span>
                </div>
                <div class="space-y-3.5 mt-2">
                  <div
                    v-for="item in result.regional_demand"
                    :key="item.code"
                    class="flex flex-col gap-1 text-sm"
                  >
                    <div class="flex justify-between items-center text-xs">
                      <span class="font-medium text-gray-800">{{ item.region }}</span>
                      <div class="flex items-center gap-2">
                        <span class="text-emerald-600 font-semibold">{{ item.growth }}</span>
                        <span class="text-gray-500 font-bold w-10 text-right">{{ item.share }}%</span>
                      </div>
                    </div>
                    <a-progress
                      :percent="item.share"
                      :show-info="false"
                      :stroke-color="'#4a9b8c'"
                      size="small"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 采购商长尾意图热词拓展表 -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
                <div>
                  <h3 class="text-base font-semibold text-gray-900">采购商长尾衍生热词挖掘</h3>
                  <p class="text-xs text-gray-400 mt-0.5">针对高转化搜索意图（工厂直采、批发寻源、出厂报价）精选推荐</p>
                </div>
                <a-space>
                  <a-button
                    type="primary"
                    :disabled="!selectedRowKeys.length"
                    :loading="savingLibrary"
                    @click="batchSaveToLibrary"
                  >
                    <PlusOutlined />
                    一键保存至我的专属词库 ({{ selectedRowKeys.length }})
                  </a-button>
                </a-space>
              </div>

              <a-table
                :columns="columns"
                :data-source="result.long_tail_keywords"
                :row-key="(r: LongTailKeyword) => r.keyword"
                :row-selection="rowSelection"
                :pagination="{ pageSize: 8, showTotal: (t: number) => `共 ${t} 个长尾拓展词` }"
                size="middle"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'keyword'">
                    <span class="font-medium text-gray-900">{{ record.keyword }}</span>
                  </template>
                  <template v-else-if="column.key === 'intent'">
                    <a-tag color="processing">{{ record.intent }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'search_volume'">
                    <span>{{ formatNumber(record.search_volume) }}</span>
                  </template>
                  <template v-else-if="column.key === 'heat_index'">
                    <div class="flex items-center gap-2">
                      <a-progress
                        :percent="record.heat_index"
                        :show-info="false"
                        :stroke-color="record.heat_index > 75 ? '#ef4444' : '#4a9b8c'"
                        size="small"
                        style="width: 70px"
                      />
                      <span class="text-xs font-semibold">{{ record.heat_index }}</span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'cpc'">
                    <span class="text-gray-700 font-medium">{{ record.cpc }}</span>
                  </template>
                  <template v-else-if="column.key === 'action'">
                    <a-button type="link" size="small" @click="saveSingle(record)">
                      加入词库
                    </a-button>
                  </template>
                </template>
              </a-table>
            </div>

            <!-- AI 商业获客与 SEO/GEO 策略洞察卡片 -->
            <div class="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-5 border border-emerald-100">
              <div class="flex items-center gap-2 mb-3">
                <BulbOutlined class="text-primary text-lg" />
                <h3 class="text-base font-semibold text-gray-900">AI 商业获客与 SEO / GEO 落地建议</h3>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed text-gray-700">
                <div class="bg-white p-3.5 rounded-lg border border-emerald-200/50">
                  <p class="font-semibold text-gray-900 mb-1">🎯 采购商画像与意图分析</p>
                  <p>{{ result.ai_insights.buyer_intent }}</p>
                </div>
                <div class="bg-white p-3.5 rounded-lg border border-emerald-200/50">
                  <p class="font-semibold text-gray-900 mb-1">🌐 独立站 SEO 页面布局建议</p>
                  <p>{{ result.ai_insights.seo_recommendation }}</p>
                </div>
                <div class="bg-white p-3.5 rounded-lg border border-emerald-200/50">
                  <p class="font-semibold text-gray-900 mb-1">🤖 GEO / AI 搜索引擎占位指南</p>
                  <p>{{ result.ai_insights.geo_recommendation }}</p>
                </div>
                <div class="bg-white p-3.5 rounded-lg border border-emerald-200/50">
                  <p class="font-semibold text-gray-900 mb-1">💬 社媒与 WhatsApp 破冰转化</p>
                  <p>{{ result.ai_insights.social_recommendation }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- TAB 2: 谷歌全球行业热门关键词排行榜 (直接抄大词) -->
      <a-tab-pane key="leaderboard" tab="🔥 谷歌全球外贸热门排行榜">
        <div class="space-y-6 pt-2">
          <!-- 行业切换筛选栏 -->
          <a-card :bordered="false" class="shadow-sm">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h3 class="text-base font-bold text-gray-900">谷歌全球行业热门采购词排行榜 (Top Benchmark)</h3>
                <p class="text-xs text-gray-400 mt-1">数据源：Google Ads Keyword Planner & SEMrush 核心数据，杜绝拍脑袋瞎造词</p>
              </div>
              <a-radio-group
                v-model:value="selectedLeaderboardCategory"
                button-style="solid"
                @change="loadLeaderboard"
              >
                <a-radio-button value="all">全行业总榜</a-radio-button>
                <a-radio-button value="insulation">绝热保温 (Rock Wool)</a-radio-button>
                <a-radio-button value="sealing">密封配件 (Gaskets)</a-radio-button>
                <a-radio-button value="tiles_stone">石材瓷砖 (Tiles/Stone)</a-radio-button>
                <a-radio-button value="doors_windows">门窗幕墙 (Doors/Windows)</a-radio-button>
              </a-radio-group>
            </div>
          </a-card>

          <!-- 排行榜表格 -->
          <a-card :bordered="false" class="shadow-sm">
            <a-table
              :columns="leaderboardColumns"
              :data-source="leaderboardData"
              :loading="loadingLeaderboard"
              row-key="keyword"
              :pagination="{ pageSize: 10 }"
              size="middle"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'rank'">
                  <div class="flex items-center justify-center font-bold">
                    <span v-if="record.rank === 1" class="text-amber-500 text-base">🥇 #1</span>
                    <span v-else-if="record.rank === 2" class="text-slate-400 text-base">🥈 #2</span>
                    <span v-else-if="record.rank === 3" class="text-amber-700 text-base">🥉 #3</span>
                    <span v-else class="text-gray-500">#{{ record.rank }}</span>
                  </div>
                </template>
                <template v-else-if="column.key === 'keyword'">
                  <div class="flex items-center gap-2">
                    <span class="font-bold text-gray-900">{{ record.keyword }}</span>
                    <a-tag size="small" color="blue">{{ record.category }}</a-tag>
                  </div>
                </template>
                <template v-else-if="column.key === 'search_volume'">
                  <span class="font-bold text-primary">{{ formatNumber(record.search_volume) }} 次/月</span>
                </template>
                <template v-else-if="column.key === 'kd'">
                  <span class="text-gray-700 font-semibold">{{ record.kd }} / 100</span>
                </template>
                <template v-else-if="column.key === 'growth'">
                  <span class="text-emerald-600 font-bold">{{ record.growth }}</span>
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="investigateKeyword(record.keyword)">
                      查详细热度
                    </a-button>
                    <a-button type="link" size="small" @click="saveSingle(record)">
                      加入词库
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
      </a-tab-pane>

      <!-- TAB 3: 🤖 旺财 × DeerFlow 2.0 自动深研托管（免调研模式） -->
      <a-tab-pane key="autopilot" tab="🤖 旺财 × DeerFlow 2.0 自动深研 (免调研模式)">
        <div class="space-y-6 pt-2">
          <!-- 托管 Hero 卡片 -->
          <div class="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-2xl p-6 text-white shadow-md">
            <div class="max-w-3xl">
              <div class="flex items-center gap-2 mb-2">
                <RobotOutlined class="text-2xl text-emerald-200" />
                <h3 class="text-xl font-bold text-white m-0">AI 助手旺财 × DeerFlow 2.0 深度研究托管</h3>
              </div>
              <p class="text-sm text-emerald-100 leading-relaxed">
                无需您亲自花时间调研 Google 多少人搜、多少询盘、多少成交转化率。
                只需告诉旺财您的产品名称，DeerFlow 2.0 智能体在后台全自动调研全球买家真实需求与询价意图，
                全自动提炼高转化黄金长尾词，并一键部署至独立站 SEO 与 GEO 矩阵，实现全流程托管！
              </p>
              <div class="mt-4 flex flex-col sm:flex-row gap-3 items-center">
                <a-select
                  v-model:value="autopilotCountry"
                  style="width: 230px"
                  size="large"
                  :options="countryOptions"
                />
                <a-input
                  v-model:value="autopilotInput"
                  placeholder="中国老板直接输入中文产品（如: 外墙岩棉保温板、断桥铝门窗系统、金属缠绕垫）..."
                  size="large"
                  class="flex-1 rounded-lg"
                  @pressEnter="handleRunAutopilot"
                />
                <a-button
                  type="primary"
                  size="large"
                  class="bg-emerald-400 hover:bg-emerald-300 text-gray-900 font-bold border-none h-10 px-6 rounded-lg shadow"
                  :loading="loadingAutopilot"
                  @click="handleRunAutopilot"
                >
                  <RobotOutlined />
                  启动 AI 全自动托管深研
                </a-button>
              </div>
            </div>
          </div>

          <!-- 加载中动画 -->
          <div v-if="loadingAutopilot" class="py-16 text-center bg-white rounded-xl border border-gray-100">
            <a-spin size="large" tip="旺财正调度 DeerFlow 2.0 在后台自动调研 Google 买家意图、询盘率与订单转化金额..." />
          </div>

          <!-- 研报交付面板 -->
          <div v-else-if="autopilotResult" class="space-y-6">
            <!-- 核心成效预测标牌 -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <p class="text-xs text-gray-500 font-medium">覆盖潜在海外买家</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ autopilotResult.metrics_projection.total_potential_buyers }}</p>
                <span class="text-xs text-emerald-600 font-medium">Google 全球买家池</span>
              </div>
              <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <p class="text-xs text-gray-500 font-medium">预估月捕获外贸询盘</p>
                <p class="text-2xl font-bold text-primary mt-1">{{ autopilotResult.metrics_projection.projected_inquiries_monthly }}</p>
                <span class="text-xs text-emerald-600 font-medium">高意向工程/分销商</span>
              </div>
              <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <p class="text-xs text-gray-500 font-medium">行业询盘成交转化率</p>
                <p class="text-2xl font-bold text-gray-900 mt-1">{{ autopilotResult.metrics_projection.historical_conversion_rate }}</p>
                <span class="text-xs text-gray-400">基于外贸 B2B 大模型推演</span>
              </div>
              <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <p class="text-xs text-gray-500 font-medium">预估年度潜在成交额</p>
                <p class="text-2xl font-bold text-blue-600 mt-1">{{ autopilotResult.metrics_projection.projected_deal_volume_usd }}</p>
                <span class="text-xs text-blue-500 font-medium">按平均订单核算</span>
              </div>
              <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                <p class="text-xs text-gray-500 font-medium">客户调研精力消耗</p>
                <p class="text-2xl font-bold text-emerald-600 mt-1">0%</p>
                <span class="text-xs text-emerald-600 font-bold">由旺财 AI 全程托管</span>
              </div>
            </div>

            <!-- 研报结论与全自动化部署状态 -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <!-- 左侧：AI 执行研报摘要 -->
              <div class="lg:col-span-7 bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
                <div class="flex items-center gap-2 mb-3">
                  <BulbOutlined class="text-primary text-lg" />
                  <h3 class="text-base font-bold text-gray-900 m-0">旺财 × DeerFlow 2.0 深度研究结论</h3>
                </div>
                <p class="text-xs text-gray-700 leading-relaxed bg-gray-50 p-3.5 rounded-lg border border-gray-100">
                  {{ autopilotResult.executive_summary }}
                </p>
                <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
                  <span>执行智能体：{{ autopilotResult.agent_name }}</span>
                  <span>底层引擎：{{ autopilotResult.engine }}</span>
                </div>
              </div>

              <!-- 右侧：四维全自动部署流水线 -->
              <div class="lg:col-span-5 bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
                <h3 class="text-base font-bold text-gray-900 mb-3">自动化部署流水线状态</h3>
                <div class="space-y-3">
                  <div class="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/70 border border-emerald-100">
                    <CheckCircleOutlined class="text-emerald-600 mt-0.5" />
                    <div>
                      <p class="text-xs font-bold text-gray-800">1. 租户专属词库注入</p>
                      <p class="text-xs text-gray-500">{{ autopilotResult.auto_deploy_status.tenant_library.message }}</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/70 border border-emerald-100">
                    <CheckCircleOutlined class="text-emerald-600 mt-0.5" />
                    <div>
                      <p class="text-xs font-bold text-gray-800">2. 独立站 SEO Meta 配置</p>
                      <p class="text-xs text-gray-500">{{ autopilotResult.auto_deploy_status.site_seo_meta.message }}</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/70 border border-emerald-100">
                    <CheckCircleOutlined class="text-emerald-600 mt-0.5" />
                    <div>
                      <p class="text-xs font-bold text-gray-800">3. GEO / AI 生成式问答占位</p>
                      <p class="text-xs text-gray-500">{{ autopilotResult.auto_deploy_status.geo_ai_answer_box.message }}</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-2.5 p-2 rounded-lg bg-emerald-50/70 border border-emerald-100">
                    <CheckCircleOutlined class="text-emerald-600 mt-0.5" />
                    <div>
                      <p class="text-xs font-bold text-gray-800">4. WhatsApp / 邮件拓客破冰</p>
                      <p class="text-xs text-gray-500">{{ autopilotResult.auto_deploy_status.outreach_radar.message }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 🌍 全球多国采购商母语自动置换矩阵表 -->
            <div v-if="autopilotResult.multilingual_matrix?.length" class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div class="flex justify-between items-center mb-4">
                <div>
                  <div class="flex items-center gap-2">
                    <GlobalOutlined class="text-primary text-base" />
                    <h3 class="text-base font-bold text-gray-900 m-0">全球 7 大出口国采购商母语自动置换矩阵</h3>
                  </div>
                  <p class="text-xs text-gray-400 mt-1">系统已将您的中文产品词自动置换为重点出口国家对应母语搜索词，杜绝死词并完成独立站多语种分站部署</p>
                </div>
                <a-tag color="cyan" class="font-bold">多国母语协同自动化</a-tag>
              </div>

              <a-table
                :columns="matrixColumns"
                :data-source="autopilotResult.multilingual_matrix"
                row-key="country_code"
                :pagination="false"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'country'">
                    <span class="font-bold">{{ record.flag }} {{ record.country_name }}</span>
                  </template>
                  <template v-if="column.key === 'language'">
                    <a-tag color="blue">{{ record.language_name }}</a-tag>
                  </template>
                  <template v-if="column.key === 'keyword'">
                    <span class="font-bold text-gray-900">{{ record.keyword }}</span>
                  </template>
                  <template v-if="column.key === 'longtail'">
                    <span class="text-xs text-gray-600">{{ record.longtail }}</span>
                  </template>
                  <template v-if="column.key === 'search_volume'">
                    <span class="font-bold text-primary">{{ formatNumber(record.search_volume) }} 次/月</span>
                  </template>
                  <template v-if="column.key === 'cpc'">
                    <span class="text-xs font-semibold text-gray-700">{{ record.cpc }}</span>
                  </template>
                  <template v-if="column.key === 'status'">
                    <a-tag color="success">{{ record.deployment_status }}</a-tag>
                  </template>
                </template>
              </a-table>
            </div>

            <!-- 自动精选的黄金长尾词簇表格 -->
            <div class="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <div class="flex justify-between items-center mb-4">
                <div>
                  <h3 class="text-base font-bold text-gray-900">AI 自动精选黄金长尾词簇 (已剔除0搜索量死词)</h3>
                  <p class="text-xs text-gray-400 mt-0.5">DeerFlow 2.0 根据海外采购商痛点模型提炼的高成交意图词</p>
                </div>
                <a-tag color="success" class="font-bold">已全量自动入库与应用</a-tag>
              </div>

              <a-table
                :columns="goldenColumns"
                :data-source="autopilotResult.golden_clusters"
                row-key="keyword"
                :pagination="{ pageSize: 8 }"
                size="middle"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'keyword'">
                    <div class="flex flex-col">
                      <span class="font-bold text-gray-900">{{ record.keyword }}</span>
                      <span v-if="record.country_name" class="text-xs text-gray-400">
                        {{ record.country_name }} ({{ record.language_name }})
                      </span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'buyer_intent'">
                    <a-tag color="cyan">{{ record.buyer_intent }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'search_volume'">
                    <span class="font-bold text-primary">{{ formatNumber(record.search_volume) }} 次/月</span>
                  </template>
                  <template v-else-if="column.key === 'conversion_score'">
                    <div class="flex items-center gap-2">
                      <a-progress
                        :percent="record.conversion_score"
                        :show-info="false"
                        stroke-color="#10b981"
                        size="small"
                        style="width: 70px"
                      />
                      <span class="text-xs font-bold text-emerald-600">{{ record.conversion_score }}分</span>
                    </div>
                  </template>
                  <template v-else-if="column.key === 'cpc'">
                    <span class="font-medium text-gray-700">{{ record.cpc }}</span>
                  </template>
                  <template v-else-if="column.key === 'recommended_page'">
                    <span class="text-xs text-gray-500">{{ record.recommended_page }}</span>
                  </template>
                </template>
              </a-table>
            </div>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 弹窗：全球多国采购商母语自动置换矩阵详情 -->
    <a-modal
      v-model:open="showMatrixModal"
      title="🌍 全球 7 大重点出口国采购商母语自动置换矩阵"
      width="960px"
      :footer="null"
    >
      <div class="py-2">
        <p class="text-xs text-gray-500 mb-3 leading-relaxed">
          中国用户输入中文意图后，系统将自动映射为各国官方母语的本土工业采购高频词，并自动下发到各语言独立站分站与 GEO AI 问答矩阵中。
        </p>
        <a-table
          :columns="matrixColumns"
          :data-source="result?.multilingual_matrix || []"
          row-key="country_code"
          :pagination="false"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'country'">
              <span class="font-bold">{{ record.flag }} {{ record.country_name }}</span>
            </template>
            <template v-if="column.key === 'language'">
              <a-tag color="blue">{{ record.language_name }}</a-tag>
            </template>
            <template v-if="column.key === 'keyword'">
              <span class="font-bold text-gray-900">{{ record.keyword }}</span>
            </template>
            <template v-if="column.key === 'longtail'">
              <span class="text-xs text-gray-600">{{ record.longtail }}</span>
            </template>
            <template v-if="column.key === 'search_volume'">
              <span class="font-bold text-primary">{{ formatNumber(record.search_volume) }} 次/月</span>
            </template>
            <template v-if="column.key === 'cpc'">
              <span class="text-xs font-semibold text-gray-700">{{ record.cpc }}</span>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag color="success">{{ record.deployment_status }}</a-tag>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  FireOutlined,
  SearchOutlined,
  ThunderboltOutlined,
  DollarOutlined,
  BulbOutlined,
  PlusOutlined,
  WarningOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  GlobalOutlined,
} from '@ant-design/icons-vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';

import { YdPage } from '@/components/youding';
import {
  analyzeKeywordHeat,
  getGoogleLeaderboard,
  saveKeywordsToLibrary,
  getPopularPresets,
  runWangcaiAutopilotResearch,
  type KeywordResearchResult,
  type LongTailKeyword,
  type LeaderboardItem,
  type WangcaiAutopilotResult,
  type GoldenCluster,
  type MultilingualMatrixItem,
} from '@/api/keyword-research';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent]);

const router = useRouter();

const activeTab = ref('search');
const keywordInput = ref('岩棉保温板');
const market = ref('global');
const targetCountry = ref('US');
const autopilotCountry = ref('US');
const showMatrixModal = ref(false);
const loading = ref(false);
const savingLibrary = ref(false);
const result = ref<KeywordResearchResult | null>(null);

const countryOptions = [
  { label: '🇺🇸 全球 / 美国 (English)', value: 'US' },
  { label: '🇩🇪 德国 / 欧洲 (Deutsch)', value: 'DE' },
  { label: '🇸🇦 沙特 / 中东 (العربية)', value: 'SA' },
  { label: '🇪🇸 西班牙 / 拉美 (Español)', value: 'ES' },
  { label: '🇫🇷 法国 / 欧洲 (Français)', value: 'FR' },
  { label: '🇷🇺 俄罗斯 / 独联体 (Русский)', value: 'RU' },
  { label: '🇻🇳 越南 / 东南亚 (Tiếng Việt)', value: 'VN' },
];

const matrixColumns = [
  { title: '目标国家/市场', key: 'country', width: 170 },
  { title: '官方母语', key: 'language', width: 110 },
  { title: '自动置换本地采购词', key: 'keyword', width: 220 },
  { title: '本地高热黄金长尾词', key: 'longtail', width: 260 },
  { title: 'Google 当地月搜量', key: 'search_volume', width: 150 },
  { title: '商业出价 (CPC)', key: 'cpc', width: 120 },
  { title: '自动化部署状态', key: 'status', width: 200 },
];

// 排行榜相关状态
const selectedLeaderboardCategory = ref('insulation');
const leaderboardData = ref<LeaderboardItem[]>([]);
const loadingLeaderboard = ref(false);

const quickKeywords = ref<string[]>([
  '岩棉保温板',
  '断桥铝门窗',
  '金属缠绕垫',
  'Ceramic Tiles',
  'Spiral Wound Gasket',
  'Marble Slabs',
]);

const marketOptions = [
  { label: '全球海外市场 (Google)', value: 'global' },
  { label: '中东与东南亚', value: 'me_sea' },
  { label: '欧美发达市场', value: 'us_eu' },
  { label: '国内全网市场', value: 'cn' },
];

const selectedRowKeys = ref<string[]>([]);

const columns = [
  { title: '衍生长尾词', key: 'keyword', width: 260 },
  { title: '买家核心意图', key: 'intent', width: 140 },
  { title: '月搜索量', key: 'search_volume', width: 120, sorter: (a: LongTailKeyword, b: LongTailKeyword) => a.search_volume - b.search_volume },
  { title: '热度指数', key: 'heat_index', width: 160, sorter: (a: LongTailKeyword, b: LongTailKeyword) => a.heat_index - b.heat_index },
  { title: '建议出价 (CPC)', key: 'cpc', width: 130 },
  { title: '操作', key: 'action', width: 110, align: 'center' as const },
];

const leaderboardColumns = [
  { title: '谷歌排名', key: 'rank', width: 110, align: 'center' as const },
  { title: '行业核心热门词', key: 'keyword', width: 280 },
  { title: 'Google 全球月搜索量', key: 'search_volume', width: 180, sorter: (a: LeaderboardItem, b: LeaderboardItem) => a.search_volume - b.search_volume },
  { title: '竞争难度 (KD)', key: 'kd', width: 130 },
  { title: '建议出价 (CPC)', key: 'cpc', width: 130 },
  { title: '月度增长率', key: 'growth', width: 120 },
  { title: '采购商意图', key: 'intent', width: 140 },
  { title: '操作', key: 'action', width: 170, align: 'center' as const },
];

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys as string[];
  },
}));

function formatNumber(num: number): string {
  return (num || 0).toLocaleString();
}

function formatDate(iso: string): string {
  if (!iso) return '';
  return iso.substring(0, 19).replace('T', ' ');
}

function getDifficultyColor(level: string): string {
  if (level === 'low') return 'green';
  if (level === 'high') return 'red';
  return 'orange';
}

const trendChartOption = computed(() => {
  if (!result.value?.trends) return {};
  const labels = result.value.trends.map((t) => t.month);
  const values = result.value.trends.map((t) => t.volume);

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      formatter: (params: any) => {
        const item = params[0];
        return `<div><p class="font-semibold text-gray-800">${item.name}</p><p class="text-xs text-primary">Google 预估搜索量: ${item.value.toLocaleString()} 次</p></div>`;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '8%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series: [
      {
        data: values,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#4a9b8c' },
        lineStyle: { width: 3, color: '#4a9b8c' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(74, 155, 140, 0.35)' },
              { offset: 1, color: 'rgba(74, 155, 140, 0.02)' },
            ],
          },
        },
      },
    ],
  };
});

async function handleSearch() {
  const kw = keywordInput.value.trim();
  if (!kw) {
    message.warning('请输入要查询的关键词');
    return;
  }
  loading.value = true;
  selectedRowKeys.value = [];
  try {
    result.value = await analyzeKeywordHeat({
      keyword: kw,
      market: market.value,
      target_country: targetCountry.value,
    });
  } catch (err: any) {
    message.error(err?.message || '关键词热度分析失败');
  } finally {
    loading.value = false;
  }
}

function pickQuickKeyword(kw: string) {
  keywordInput.value = kw;
  handleSearch();
}

function adoptAlternative(kw: string) {
  keywordInput.value = kw;
  message.success(`已采纳推荐词「${kw}」并执行合规分析！`);
  handleSearch();
}

function investigateKeyword(kw: string) {
  activeTab.value = 'search';
  keywordInput.value = kw;
  handleSearch();
}

async function loadLeaderboard() {
  loadingLeaderboard.value = true;
  try {
    const res = await getGoogleLeaderboard(selectedLeaderboardCategory.value);
    leaderboardData.value = res.leaderboard || [];
  } catch (err: any) {
    message.error(err?.message || '获取排行榜失败');
  } finally {
    loadingLeaderboard.value = false;
  }
}

async function onMarketChange() {
  try {
    const res = await getPopularPresets(market.value);
    const words: string[] = [];
    res.categories.forEach((c) => {
      c.keywords.forEach((k) => words.push(k));
    });
    if (words.length > 0) {
      quickKeywords.value = words.slice(0, 8);
    }
  } catch {
    // 降级使用现有词
  }
  handleSearch();
}

async function batchSaveToLibrary() {
  if (!result.value || !selectedRowKeys.value.length) return;
  const targets = result.value.long_tail_keywords.filter((item) =>
    selectedRowKeys.value.includes(item.keyword)
  );

  savingLibrary.value = true;
  try {
    const res = await saveKeywordsToLibrary(targets);
    message.success(`已成功保存 ${res.saved_count} 个词到您的专属词库 (重复 ${res.duplicate_count} 个)`);
  } catch (err: any) {
    message.error(err?.message || '保存到词库失败');
  } finally {
    savingLibrary.value = false;
  }
}

async function saveSingle(record: any) {
  savingLibrary.value = true;
  try {
    const res = await saveKeywordsToLibrary([record]);
    if (res.saved_count > 0) {
      message.success(`「${record.keyword}」已加入专属词库`);
    } else {
      message.info('该词已在专属词库中');
    }
  } catch (err: any) {
    message.error(err?.message || '保存失败');
  } finally {
    savingLibrary.value = false;
  }
}

const goldenColumns = [
  { title: '黄金长尾核心词', key: 'keyword', width: 280 },
  { title: '买家核心意图', key: 'buyer_intent', width: 140 },
  { title: 'Google 月搜索量', key: 'search_volume', width: 160 },
  { title: '转化评分', key: 'conversion_score', width: 140 },
  { title: '商业出价 (CPC)', key: 'cpc', width: 130 },
  { title: '推荐部署落地页', key: 'recommended_page', width: 220 },
];

const autopilotInput = ref('外墙岩棉保温板');
const loadingAutopilot = ref(false);
const autopilotResult = ref<WangcaiAutopilotResult | null>(null);

async function handleRunAutopilot() {
  const topic = autopilotInput.value.trim();
  if (!topic) {
    message.warning('请输入您的主营产品名称');
    return;
  }
  loadingAutopilot.value = true;
  try {
    autopilotResult.value = await runWangcaiAutopilotResearch({
      product_or_topic: topic,
      target_market: 'global',
      target_country: autopilotCountry.value,
      auto_apply: true,
    });
    message.success('旺财 × DeerFlow 2.0 深度研究已完成，多国母语矩阵已全自动部署至建站系统！');
  } catch (err: any) {
    message.error(err?.message || 'AI 深度研究托管执行失败');
  } finally {
    loadingAutopilot.value = false;
  }
}

onMounted(() => {
  handleSearch();
  loadLeaderboard();
  handleRunAutopilot();
});
</script>

<style scoped>
.quick-kw-tag {
  cursor: pointer;
  padding: 2px 8px;
  background-color: #f1f5f9;
  border-radius: 4px;
  color: #334155;
  transition: all 0.2s ease;
}
.quick-kw-tag:hover {
  background-color: #e2e8f0;
  color: #4a9b8c;
}
</style>
