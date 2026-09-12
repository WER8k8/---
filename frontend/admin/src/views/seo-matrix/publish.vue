<template>
  <YdPage title="多平台分发" subtitle="AI 生成内容 · 选择平台 · 一键群发" surface="elevated">
  <div class="publish-page">
    <a-alert
      v-if="tokenQuota.balance != null"
      type="info"
      show-icon
      class="token-quota-bar"
      :message="`AI 流量：剩余 ${tokenQuota.balance} 点 · 本月已用 ${tokenQuota.quota_used ?? 0} 点`"
    >
      <template #description>
        <span v-if="lastTokenUsage > 0">最近一次 AI 操作消耗 {{ lastTokenUsage }} Token。</span>
        <a @click.prevent="router.push('/client/tokens')">查看明细与充值 →</a>
      </template>
    </a-alert>
    <!-- ========== 1. AI 内容生成区 ========== -->
    <div class="panel ai-panel">
      <h3 class="pt pt-with-icon"><RobotOutlined /> AI 内容生成</h3>

      <a-row :gutter="16" class="ai-controls">
        <a-col :span="6">
          <span class="ctrl-label">内容类型</span>
          <a-select v-model:value="aiForm.contentType" style="width:100%">
            <a-select-option value="news">新闻稿</a-select-option>
            <a-select-option value="product">产品介绍</a-select-option>
            <a-select-option value="industry">行业资讯</a-select-option>
            <a-select-option value="seo">SEO 文章</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <span class="ctrl-label">风格</span>
          <a-select v-model:value="aiForm.style" style="width:100%">
            <a-select-option value="formal">正式</a-select-option>
            <a-select-option value="professional">专业</a-select-option>
            <a-select-option value="friendly">亲和</a-select-option>
            <a-select-option value="marketing">营销</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <span class="ctrl-label">语言</span>
          <a-select v-model:value="aiForm.language" style="width:100%">
            <a-select-option value="zh-CN">中文</a-select-option>
            <a-select-option value="en">English</a-select-option>
            <a-select-option value="ja">日本語</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <span class="ctrl-label">字数</span>
          <a-select v-model:value="aiForm.wordCount" style="width:100%">
            <a-select-option value="300">300 字左右</a-select-option>
            <a-select-option value="500">500 字左右</a-select-option>
            <a-select-option value="1000">1000 字左右</a-select-option>
            <a-select-option value="2000">2000 字左右</a-select-option>
          </a-select>
        </a-col>
      </a-row>

      <div class="ai-topic-row">
        <span class="ctrl-label">主题 / 关键词</span>
        <a-input
          v-model:value="aiForm.topic"
          placeholder="输入文章主题或关键词，例如：绿色建材、低碳环保、装配式建筑..."
          size="large"
        />
      </div>

      <div class="ai-actions">
        <a-button type="primary" ghost size="large" @click="generateContent" :loading="aiGenerating" class="ai-btn-gen">
          <template #icon><BulbOutlined /></template>
          生成内容
        </a-button>
        <a-button size="large" @click="optimizeContent" :disabled="!generatedContent" :loading="aiOptimizing">
          <template #icon><ToolOutlined /></template>
          优化
        </a-button>
        <a-button size="large" @click="openDraftModal">
          <template #icon><FolderOpenOutlined /></template>
          草稿箱
        </a-button>
        <a-button size="large" @click="clearContent" :disabled="!generatedContent">
          <template #icon><DeleteOutlined /></template>
          清空
        </a-button>
      </div>

      <!-- 内容预览 -->
      <div class="ai-preview" v-if="generatedContent">
        <div class="preview-toolbar">
          <span class="preview-label">
            内容预览
            <a-tag color="blue" class="ml-2">{{ contentTypeLabel }}</a-tag>
          </span>
          <span class="word-count">共 {{ contentWordCount }} 字</span>
        </div>
        <a-textarea
          v-model:value="generatedContent"
          :rows="10"
          class="preview-textarea"
          placeholder="AI 生成的内容将显示在这里，您可以手动编辑..."
        />
        <div class="preview-actions">
          <a-button @click="saveDraft" :disabled="!generatedContent">
            <template #icon><SaveOutlined /></template>
            保存到草稿
          </a-button>
          <a-button
            type="primary"
            @click="quickDistribute"
            :disabled="!generatedContent || selectedPlatforms.length === 0"
            class="btn-distribute"
          >
            <template #icon><SendOutlined /></template>
            一键分发
          </a-button>
        </div>
      </div>
      <div class="ai-empty" v-else>
        <div class="empty-icon"><YdIllustration icon="EditOutlined" size="lg" /></div>
        <p>输入主题并点击「生成内容」，AI 将自动为您撰写文章</p>
      </div>
    </div>

    <!-- ========== 草稿选择弹窗 ========== -->
    <a-modal v-model:open="draftModalVisible" title="选择草稿" width="680px" :footer="null">
      <a-table :columns="draftCols" :data-source="drafts" row-key="id" :pagination="{pageSize:5}" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='type'"><a-tag>{{ record.typeLabel }}</a-tag></template>
          <template v-if="column.key==='time'">{{ record.time }}</template>
          <template v-if="column.key==='actions'">
            <a-button type="primary" size="small" ghost @click="loadDraft(record)">选用</a-button>
            <a-button size="small" danger @click="deleteDraft(record.id)">删除</a-button>
          </template>
        </template>
        <template #emptyText>
          <div style="padding:24px;text-align:center;color:#94a3b8">暂无草稿，请先生成内容</div>
        </template>
      </a-table>
    </a-modal>

    <!-- ========== 2. 视频绑号入口 + 选择发布平台 ========== -->
    <VideoPublishBindHub
      ref="videoBindHubRef"
      @connect="onVideoHubConnect"
    />

    <div class="panel platform-panel">
      <h3 class="pt pt-with-icon">
        <SendOutlined /> 选择发布平台
        <a-tag color="blue" class="ml-2">已选 {{ selectedPlatforms.length }} 个</a-tag>
        <a-tag v-if="intlPlatforms.length" color="purple" class="ml-2">海外 {{ intlPlatforms.length }}</a-tag>
      </h3>
      <p class="platform-hint">
        可从目录勾选任意平台；未收录的平台可在下方自填名称添加，无需事先锁定入口。
      </p>

      <a-alert
        v-if="!apiOnline"
        type="warning"
        show-icon
        style="margin-bottom:12px"
        message="后端 API 未连接（:8001）"
        description="平台为离线目录，连接/发布不可用。请在项目根目录运行：powershell -File scripts/start-dev-admin.ps1"
      />

      <SkeletonCard v-if="platformsLoading" variant="card" />
      <template v-else>

      <!-- 国内平台 -->
      <div class="platform-group">
        <div class="group-header" @click="cnExpanded = !cnExpanded">
          <svg :class="cnExpanded ? 'rotated' : ''" class="arrow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M9 6l6 6-6 6"/></svg>
          <span class="group-label"><EnvironmentOutlined /> 国内平台 ({{ chinaPlatforms.length }})</span>
          <span class="group-badge">{{ connectedCnCount }} 已连接</span>
        </div>
        <div v-show="cnExpanded" class="group-body">
          <div class="platform-grid">
            <div
              v-for="p in chinaPlatforms"
              :key="p.id"
              class="platform-card"
              :class="{
                selected: isPlatformSelected(p.id),
                connected: isPlatformConnected(p.id)
              }"
              @click="togglePlatform(p)"
            >
              <div class="pc-check" @click.stop>
                <a-checkbox
                  :checked="isPlatformSelected(p.id)"
                  @change="(e) => onPlatformCheckChange(p, e)"
                />
              </div>
              <YdNavIcon :name="p.iconKey" size="sm" class="pc-icon" />
              <span class="pc-name">{{ p.name }}</span>
              <span
                class="pc-status"
                :class="isPlatformConnected(p.id) ? 'on' : 'off'"
              >{{ isPlatformConnected(p.id) ? '已连接' : '未连接' }}</span>
              <a-button
                size="small"
                class="pc-connect"
                :type="isPlatformConnected(p.id) ? 'default' : 'primary'"
                @click.stop="openConnectModal(p)"
              >{{ isPlatformConnected(p.id) ? '管理' : '连接' }}</a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 国外平台 -->
      <div class="platform-group">
        <div class="group-header" @click="intlExpanded = !intlExpanded">
          <svg :class="intlExpanded ? 'rotated' : ''" class="arrow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M9 6l6 6-6 6"/></svg>
          <span class="group-label"><GlobalOutlined /> 国外平台 ({{ intlPlatforms.length }})</span>
          <span class="group-badge">{{ connectedIntlCount }} 已连接</span>
        </div>
        <div v-show="intlExpanded" class="group-body">
          <div class="platform-grid">
            <div
              v-for="p in intlPlatforms"
              :key="p.id"
              class="platform-card"
              :class="{
                selected: isPlatformSelected(p.id),
                connected: isPlatformConnected(p.id)
              }"
              @click="togglePlatform(p)"
            >
              <div class="pc-check" @click.stop>
                <a-checkbox
                  :checked="isPlatformSelected(p.id)"
                  @change="(e) => onPlatformCheckChange(p, e)"
                />
              </div>
              <YdNavIcon :name="p.iconKey" size="sm" class="pc-icon" />
              <span class="pc-name">{{ p.name }}</span>
              <span
                class="pc-status"
                :class="isPlatformConnected(p.id) ? 'on' : 'off'"
              >{{ isPlatformConnected(p.id) ? '已连接' : '未连接' }}</span>
              <a-button
                size="small"
                class="pc-connect"
                :type="isPlatformConnected(p.id) ? 'default' : 'primary'"
                @click.stop="openConnectModal(p)"
              >{{ isPlatformConnected(p.id) ? '管理' : '连接' }}</a-button>
            </div>
          </div>
        </div>
      </div>

      <div class="custom-platform-bar">
        <a-input
          v-model:value="customPlatformName"
          allow-clear
          placeholder="其他平台名称（目录里没有可自填，如行业垂直站、海外小众渠道）"
          @press-enter="addCustomPlatform"
        />
        <a-select v-model:value="customPlatformRegion" style="width: 112px">
          <a-select-option value="cn">国内</a-select-option>
          <a-select-option value="global">海外</a-select-option>
        </a-select>
        <a-button type="primary" ghost :loading="addingCustomPlatform" @click="addCustomPlatform">
          添加并选中
        </a-button>
      </div>

      <div v-if="customPlatforms.length" class="custom-platform-chips">
        <span class="custom-label">您添加的平台：</span>
        <a-tag
          v-for="p in customPlatforms"
          :key="p.id"
          :color="isPlatformSelected(p.id) ? 'green' : 'default'"
          class="custom-tag"
          @click="togglePlatform(p)"
        >
          {{ p.name }}
        </a-tag>
      </div>

      <div class="platform-bulk">
        <a-button size="small" @click="selectAllConnected">全选已连接</a-button>
        <a-button size="small" @click="selectAll">全选全部</a-button>
        <a-button size="small" @click="deselectAll">取消选择</a-button>
      </div>

      <a-button
        type="primary"
        size="large"
        :loading="publishing"
        :disabled="selectedPlatforms.length === 0 || publishing"
        class="mass-btn"
        @click="startMassPublish"
      >
        <template #icon><RocketOutlined /></template>
        {{ publishing ? `发布中 ${publishProgress.current}/${publishProgress.total}` : `一键群发 (${selectedPlatforms.length})` }}
      </a-button>
      </template>
    </div>

    <!-- ========== 3. 连接 / 登录 / 养号 / 指纹弹窗 ========== -->
    <a-modal
      v-model:open="connectModalVisible"
      :title="`${isPlatformConnected(connectPlatform?.id || '') ? '管理' : '连接'} — ${connectPlatform?.name || ''}`"
      width="640px"
      :ok-text="isPlatformConnected(connectPlatform?.id || '') ? '保存设置' : '登录并连接'"
      @ok="handleConnectOk"
    >
      <a-tabs v-model:active-key="connectTab">
        <a-tab-pane key="login" tab="登录凭据">
          <a-form layout="vertical" :model="connectForm">
            <a-alert
              v-if="!isPlatformConnected(connectPlatform?.id || '')"
              :message="getConnectAlertMessage(connectPlatform)"
              type="info"
              show-icon
              style="margin-bottom:16px"
            />

            <template v-if="connectLoginMode === 'wechat_api'">
              <a-form-item label="AppID（应用ID）">
                <a-input v-model:value="connectForm.appid" placeholder="wx 开头的 AppID" />
              </a-form-item>
              <a-form-item label="AppSecret（应用密钥）">
                <a-input-password v-model:value="connectForm.appsecret" placeholder="输入 AppSecret" />
              </a-form-item>
              <a-form-item label="公众号原始 ID">
                <a-input v-model:value="connectForm.username" placeholder="gh_ 开头（选填）" />
              </a-form-item>
            </template>

            <template v-else-if="connectLoginMode === 'oauth_token'">
              <a-form-item label="OAuth Client ID / App ID">
                <a-input v-model:value="connectForm.clientId" placeholder="开发者平台 Client ID" />
              </a-form-item>
              <a-form-item label="Client Secret">
                <a-input-password v-model:value="connectForm.clientSecret" placeholder="Client Secret" />
              </a-form-item>
              <a-form-item label="Access Token">
                <a-textarea v-model:value="connectForm.accessToken" placeholder="长期或短期 Access Token" :rows="2" />
              </a-form-item>
              <a-form-item label="Refresh Token（选填）">
                <a-input v-model:value="connectForm.refreshToken" placeholder="用于自动续期" />
              </a-form-item>
              <a-form-item label="绑定邮箱 / 账号名">
                <a-input v-model:value="connectForm.username" placeholder="平台登录邮箱或用户名" />
              </a-form-item>
            </template>

            <template v-else>
              <a-form-item :label="connectLoginMode === 'phone_password' ? '手机号' : '平台账号（用户名 / 邮箱）'">
                <a-input v-model:value="connectForm.username" placeholder="登录账号" />
              </a-form-item>
              <a-form-item label="密码">
                <a-input-password v-model:value="connectForm.password" placeholder="平台密码" />
              </a-form-item>
              <a-form-item label="Cookie / Session（选填）">
                <a-textarea v-model:value="connectForm.cookie" placeholder="浏览器 Cookie，用于模拟登录" :rows="3" />
              </a-form-item>
            </template>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="nurture" tab="养号规则">
          <a-alert
            message="海外平台建议启用 7～21 天养号期，逐步提升发帖/互动频率，降低封号风险。"
            type="warning"
            show-icon
            style="margin-bottom:12px"
          />
          <a-form layout="vertical">
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="养号周期（天）">
                  <a-input-number v-model:value="nurtureForm.warmup_days" :min="1" :max="90" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="状态">
                  <a-select v-model:value="nurtureForm.status" style="width:100%">
                    <a-select-option value="draft">草稿</a-select-option>
                    <a-select-option value="warming">养号中</a-select-option>
                    <a-select-option value="active">可正常发布</a-select-option>
                    <a-select-option value="cooling">冷却</a-select-option>
                    <a-select-option value="paused">暂停</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="每日发帖上限">
                  <a-input-number v-model:value="nurtureForm.daily_posts" :min="0" :max="20" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="每日点赞上限">
                  <a-input-number v-model:value="nurtureForm.daily_likes" :min="0" :max="100" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="每日评论上限">
                  <a-input-number v-model:value="nurtureForm.daily_comments" :min="0" :max="50" style="width:100%" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-button size="small" @click="loadNurtureDefaults">恢复平台默认规则</a-button>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="fingerprint" tab="指纹隔离">
          <a-alert
            :message="connectPlatform?.group === 'intl'
              ? '海外平台须绑定 global 区域静态 IP + 独立浏览器指纹，防止多账号关联。'
              : '国内平台建议绑定 cn 区域 IP 槽位与指纹环境。'"
            type="info"
            show-icon
            style="margin-bottom:12px"
          />
          <a-form layout="vertical">
            <a-form-item label="静态 IP 槽位">
              <a-select
                v-model:value="connectForm.egress_endpoint_id"
                allow-clear
                placeholder="选择出口 IP（未选则使用平台默认池）"
                style="width:100%"
                :loading="egressLoading"
              >
                <a-select-option
                  v-for="ep in filteredEgressEndpoints"
                  :key="ep.id"
                  :value="ep.id"
                >
                  {{ ep.region === 'global' ? '全球' : '国内' }} {{ ep.host }}:{{ ep.port || '-' }} ({{ ep.slot_status }})
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="浏览器指纹环境">
              <a-select
                v-model:value="connectForm.browser_profile_id"
                allow-clear
                placeholder="选择已创建的指纹 Profile"
                style="width:100%"
                :loading="egressLoading"
              >
                <a-select-option v-for="pf in browserProfiles" :key="pf.id" :value="pf.id">
                  {{ pf.name }} {{ pf.egress_endpoint_id ? '· 已绑 IP' : '' }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-button size="small" type="link" @click="openEgressAdmin">前往静态 IP / 指纹管理 →</a-button>
          </a-form>
        </a-tab-pane>
      </a-tabs>
    </a-modal>

    <!-- ========== 5. 发布队列与历史 ========== -->
    <div class="panel">
      <h3 class="pt pt-with-icon"><OrderedListOutlined /> 发布队列与历史</h3>

      <!-- 实时进度 -->
      <div v-if="publishing" class="pub-progress">
        <a-progress :percent="publishProgress.percent" :stroke-color="['#00b894','#00cec9']" />
        <div class="pub-progress-items">
          <span v-for="d in publishProgress.details" :key="d.platformId" class="ppi">
            <span :class="'ppi-'+d.status">{{ getPlatformName(d.platformId) }}: {{ statusLabel(d.status) }}</span>
          </span>
        </div>
      </div>

      <a-table
        :columns="historyCols"
        :data-source="publishHistory"
        row-key="id"
        :pagination="{pageSize:5}"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='contentPrev'">
            <a-tooltip :title="record.content"><span class="content-prev">{{ record.content.substring(0,36) }}...</span></a-tooltip>
          </template>
          <template v-if="column.key==='results'">
            <div class="result-tags">
              <a-tag
                v-for="r in record.results"
                :key="r.platformId"
                :color="isVerifiedPubResult(r) ? 'green' : 'red'"
                style="margin:2px"
              >{{ getPlatformName(r.platformId) }} — {{ isVerifiedPubResult(r) ? '成功' : '失败' }}</a-tag>
            </div>
          </template>
          <template v-if="column.key==='actions'">
            <a-button
              v-if="record.results.some((r:any)=>!r.success)"
              size="small"
              type="primary"
              ghost
              @click="retryFailed(record)"
            >重试失败</a-button>
            <a-button size="small" @click="viewDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 历史详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="发布详情" width="600px" :footer="null">
      <a-descriptions v-if="detailRecord" :column="1" bordered size="small">
        <a-descriptions-item label="发布时间">{{ detailRecord.time }}</a-descriptions-item>
        <a-descriptions-item label="内容">
          <div style="max-height:200px;overflow:auto;white-space:pre-wrap;font-size:.85rem">{{ detailRecord.content }}</div>
        </a-descriptions-item>
        <a-descriptions-item label="发布结果">
          <div v-for="r in detailRecord.results" :key="r.platformId" style="margin:4px 0">
            <a-tag :color="isVerifiedPubResult(r) ? 'green' : 'red'">
              {{ getPlatformName(r.platformId) }} — {{ isVerifiedPubResult(r) ? '发布成功' : '发布失败' }}
            </a-tag>
            <span v-if="r.message" style="font-size:12px;color:#64748b;margin-left:8px">{{ r.message }}</span>
          </div>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { YdIllustration, YdNavIcon, YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { seoPlatformIconName } from '@/constants/iconCatalog'
import {
  BulbOutlined,
  DeleteOutlined,
  EditOutlined,
  EnvironmentOutlined,
  FolderOpenOutlined,
  GlobalOutlined,
  RobotOutlined,
  RocketOutlined,
  SaveOutlined,
  OrderedListOutlined,
  SendOutlined,
  ToolOutlined,
} from '@ant-design/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import VideoPublishBindHub from '@/components/tenant/VideoPublishBindHub.vue'
import { getAuthToken } from '@/utils/api'
import { consumePublishPrefill } from '@/utils/onboardingAutopilot'
import { unwrapFetchedJson } from '@/api'

const router = useRouter()
const route = useRoute()
const videoBindHubRef = ref<InstanceType<typeof VideoPublishBindHub> | null>(null)

const tokenQuota = reactive<{ balance: number | null; quota_used: number | null }>({
  balance: null,
  quota_used: null,
})
const lastTokenUsage = ref(0)

async function loadTokenQuota() {
  try {
    const res = await fetch('/api/v1/token/my-quota', { headers: authHeaders() })
    if (!res.ok) return
    const body = await res.json()
    const data = unwrapFetchedJson<{ balance?: number; quota_used?: number }>(body)
    tokenQuota.balance = data?.balance ?? null
    tokenQuota.quota_used = data?.quota_used ?? null
  } catch {
    /* 超管或未绑定租户时不展示 */
  }
}

function authHeaders(extra: Record<string, string> = {}) {
  const tk = getAuthToken()
  return { ...(tk ? { Authorization: `Bearer ${tk}` } : {}), ...extra }
}

/* ============================================================
   平台定义 — 从 API 加载（40 平台 catalog）
   ============================================================ */
interface PlatformDef {
  id: string
  name: string
  iconKey: string
  group: 'cn' | 'intl'
  login_hint?: string
  custom?: boolean
}

const allPlatforms = ref<PlatformDef[]>([])
const platformsLoading = ref(false)
const apiOnline = ref(true)

const FALLBACK_CN_NAMES = [
  '微信公众号', '抖音', '快手', '小红书', '百家号', '微博', '哔哩哔哩', '知乎', '头条号', '企鹅号',
  '网易号', '搜狐号', '一点资讯', '大鱼号', '简书', '脉脉', '微信视频号', '淘宝逛逛', '1688', '慧聪网',
]
const FALLBACK_GLOBAL_NAMES = [
  'YouTube', 'TikTok', 'LinkedIn', 'Facebook', 'Instagram', 'X', 'Pinterest', 'Reddit', 'Snapchat', 'WhatsApp',
  'Medium', 'Tumblr', 'Telegram Channel', 'LINE Official', 'Zalo', 'VK', 'Quora', 'Blogger', 'WordPress.com', 'Amazon Seller', 'Alibaba.com',
]

function iconForPlatform(name: string) {
  return seoPlatformIconName(name)
}

function mapApiPlatform(p: Record<string, unknown>): PlatformDef {
  const region = String(p.region || 'cn')
  const ptype = String(p.platform_type || '')
  return {
    id: String(p.id),
    name: String(p.name),
    iconKey: iconForPlatform(String(p.name)),
    group: region === 'global' ? 'intl' : 'cn',
    login_hint: p.login_hint ? String(p.login_hint) : undefined,
    custom: ptype === 'custom',
  }
}

function buildFallbackPlatforms(): PlatformDef[] {
  const cn = FALLBACK_CN_NAMES.map((name) => ({
    id: `offline-cn-${name}`,
    name,
    iconKey: iconForPlatform(name),
    group: 'cn' as const,
  }))
  const gl = FALLBACK_GLOBAL_NAMES.map((name) => ({
    id: `offline-gl-${name}`,
    name,
    iconKey: iconForPlatform(name),
    group: 'intl' as const,
    login_hint: 'oauth_token',
  }))
  return [...cn, ...gl]
}

function parsePlatformRows(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) return data as Record<string, unknown>[]
  if (data && typeof data === 'object' && Array.isArray((data as { items?: unknown[] }).items)) {
    return (data as { items: Record<string, unknown>[] }).items
  }
  return []
}

async function fetchPlatformRows(url: string): Promise<Record<string, unknown>[]> {
  const res = await fetch(url, { headers: authHeaders() })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = unwrapFetchedJson<unknown>(await res.json())
  return parsePlatformRows(data)
}

async function loadPlatforms() {
  platformsLoading.value = true
  apiOnline.value = true
  try {
    let rows = await fetchPlatformRows('/api/v1/seo-matrix/platforms')
    if (!rows.length) rows = await fetchPlatformRows('/api/v1/platforms')
    if (!rows.length) throw new Error('empty')
    allPlatforms.value = rows.map((r) => mapApiPlatform(r))
  } catch {
    apiOnline.value = false
    allPlatforms.value = buildFallbackPlatforms()
    message.warning('后端 API (:8001) 未连接，已显示离线目录。请运行 scripts/start-dev-admin.ps1 后刷新')
  } finally {
    platformsLoading.value = false
  }
}

const chinaPlatforms = computed(() =>
  allPlatforms.value.filter((p) => p.group === 'cn' && !p.custom),
)
const intlPlatforms = computed(() =>
  allPlatforms.value.filter((p) => p.group === 'intl' && !p.custom),
)
const customPlatforms = computed(() => allPlatforms.value.filter((p) => p.custom))

function getPlatformName(id: string) {
  const p = allPlatforms.value.find((x) => x.id === id)
  return p ? p.name : id
}

/* ============================================================
   已连接账号
   ============================================================ */
interface NurtureCfg {
  warmup_days: number
  daily_posts: number
  daily_likes: number
  daily_comments: number
  status: string
}

interface Account {
  id: string
  platform: string
  username: string
  status: 'active' | 'offline'
  lastLogin: string
  cookie?: string
  appid?: string
  browser_profile_id?: string
  egress_endpoint_id?: string
  nurture?: NurtureCfg
}

const savedAccounts = ref<Account[]>([])

function isPlatformConnected(id: string): boolean {
  return savedAccounts.value.some((a) => a.platform === id && a.status === 'active')
}

function getConnectAlertMessage(platform: PlatformDef | null): string {
  if (!platform) return '请填写平台登录信息'
  if (platform.login_hint === 'wechat_api') {
    return '微信公众号：在微信公众平台「开发 > 基本配置」获取 AppID / AppSecret'
  }
  if (platform.login_hint === 'oauth_token') {
    return `${platform.name}：请填写 OAuth Client ID / Secret 或 Access Token（海外平台建议使用独立指纹环境）`
  }
  if (platform.group === 'intl') {
    return `${platform.name}：海外账号请同时配置「养号规则」与「指纹隔离」Tab，降低关联封号风险`
  }
  return `请输入 ${platform.name} 账号信息；凭据加密存储，仅用于自动发布。`
}

const connectedCnCount = computed(() => chinaPlatforms.value.filter((p) => isPlatformConnected(p.id)).length)
const connectedIntlCount = computed(() => intlPlatforms.value.filter((p) => isPlatformConnected(p.id)).length)

/* ============================================================
   展开/折叠 — 国外平台默认展开
   ============================================================ */
const cnExpanded = ref(true)
const intlExpanded = ref(true)

/* ============================================================
   选中平台
   ============================================================ */
const selectedPlatforms = ref<PlatformDef[]>([])

function isPlatformSelected(id: string) {
  return selectedPlatforms.value.some((p) => p.id === id)
}

function togglePlatform(p: PlatformDef) {
  const i = selectedPlatforms.value.findIndex((x) => x.id === p.id)
  if (i >= 0) selectedPlatforms.value.splice(i, 1)
  else selectedPlatforms.value.push(p)
}

function onPlatformCheckChange(p: PlatformDef, e: { target: { checked: boolean } }) {
  const checked = e.target.checked
  const selected = isPlatformSelected(p.id)
  if (checked && !selected) selectedPlatforms.value.push(p)
  if (!checked && selected) {
    const i = selectedPlatforms.value.findIndex((x) => x.id === p.id)
    if (i >= 0) selectedPlatforms.value.splice(i, 1)
  }
}

const customPlatformName = ref('')
const customPlatformRegion = ref<'cn' | 'global'>('cn')
const addingCustomPlatform = ref(false)

async function addCustomPlatform() {
  const name = customPlatformName.value.trim()
  if (!name) {
    message.warning('请输入平台名称')
    return
  }
  const existing = allPlatforms.value.find((p) => p.name === name)
  if (existing) {
    if (!isPlatformSelected(existing.id)) selectedPlatforms.value.push(existing)
    message.info(`「${name}」已在列表中，已为您选中`)
    customPlatformName.value = ''
    return
  }
  if (!apiOnline.value) {
    message.warning('请先启动后端 API (:8001) 后再添加自定义平台')
    return
  }
  addingCustomPlatform.value = true
  try {
    const res = await fetch('/api/v1/seo-matrix/platforms', {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ name, region: customPlatformRegion.value }),
    })
    const body = await res.json()
    if (!res.ok) throw new Error(body.message || body.detail || '添加失败')
    const data = unwrapFetchedJson<Record<string, unknown>>(body)
    const row = data && typeof data === 'object' ? data : (body.data as Record<string, unknown>)
    const plat = mapApiPlatform(row)
    plat.custom = true
    allPlatforms.value.push(plat)
    selectedPlatforms.value.push(plat)
    customPlatformName.value = ''
    message.success(`已添加「${name}」，发布前请点击「连接」绑定账号`)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '添加平台失败')
  } finally {
    addingCustomPlatform.value = false
  }
}

function selectAll() {
  selectedPlatforms.value = [...allPlatforms.value]
}
function selectAllConnected() {
  selectedPlatforms.value = allPlatforms.value.filter((p) => isPlatformConnected(p.id))
}
function deselectAll() {
  selectedPlatforms.value = []
}

/* ============================================================
   连接弹窗 — 登录 / 养号 / 指纹
   ============================================================ */
const connectModalVisible = ref(false)
const connectPlatform = ref<PlatformDef | null>(null)
const connectTab = ref('login')
const connectForm = reactive({
  username: '',
  password: '',
  cookie: '',
  appid: '',
  appsecret: '',
  clientId: '',
  clientSecret: '',
  accessToken: '',
  refreshToken: '',
  browser_profile_id: undefined as string | undefined,
  egress_endpoint_id: undefined as string | undefined,
})

const nurtureForm = reactive<NurtureCfg>({
  warmup_days: 14,
  daily_posts: 1,
  daily_likes: 5,
  daily_comments: 2,
  status: 'warming',
})

const connectLoginMode = computed(() => {
  const p = connectPlatform.value
  if (!p) return 'username_password'
  if (p.login_hint === 'wechat_api' || p.name === '微信公众号') return 'wechat_api'
  if (p.login_hint === 'oauth_token' || p.group === 'intl') return 'oauth_token'
  if (p.login_hint === 'phone_password' || p.name === '小红书' || p.name === '微博') return 'phone_password'
  return 'username_password'
})

const egressLoading = ref(false)
const egressEndpoints = ref<Array<{ id: string; region: string; host: string; port?: number; slot_status: string }>>([])
const browserProfiles = ref<Array<{ id: string; name: string; egress_endpoint_id?: string }>>([])

const filteredEgressEndpoints = computed(() => {
  const want = connectPlatform.value?.group === 'intl' ? 'global' : 'cn'
  return egressEndpoints.value.filter((e) => e.region === want || e.slot_status === 'available')
})

async function loadEgressResources() {
  egressLoading.value = true
  try {
    const [epRes, pfRes] = await Promise.all([
      fetch('/api/v1/egress/endpoints', { headers: authHeaders() }),
      fetch('/api/v1/egress/profiles', { headers: authHeaders() }),
    ])
    const epData = unwrapFetchedJson<typeof egressEndpoints.value>(await epRes.json())
    const pfData = unwrapFetchedJson<typeof browserProfiles.value>(await pfRes.json())
    egressEndpoints.value = Array.isArray(epData) ? epData : []
    browserProfiles.value = Array.isArray(pfData) ? pfData : []
  } catch {
    /* 非超管可能 403，静默 */
  } finally {
    egressLoading.value = false
  }
}

async function loadNurtureDefaults() {
  const p = connectPlatform.value
  if (!p) return
  try {
    const q = new URLSearchParams({
      platform: p.name,
      region: p.group === 'intl' ? 'global' : 'cn',
    })
    const res = await fetch(`/api/v1/social-nurture/rules?${q}`, { headers: authHeaders() })
    const data = unwrapFetchedJson<{ rules?: NurtureCfg }>(await res.json())
    if (data?.rules) Object.assign(nurtureForm, data.rules)
  } catch {
    Object.assign(nurtureForm, p.group === 'intl'
      ? { warmup_days: 14, daily_posts: 1, daily_likes: 5, daily_comments: 2, status: 'warming' }
      : { warmup_days: 7, daily_posts: 2, daily_likes: 10, daily_comments: 3, status: 'warming' })
  }
}

function openEgressAdmin() {
  router.push('/admin/finance/ip-pool')
}

function onVideoHubConnect(platform: { id: string; name: string }) {
  const existing = allPlatforms.value.find((x) => x.id === platform.id || x.name === platform.name)
  if (existing) {
    openConnectModal(existing)
    return
  }
  const group = FALLBACK_GLOBAL_NAMES.includes(platform.name) ? 'intl' : 'cn'
  openConnectModal({
    id: platform.id,
    name: platform.name,
    iconKey: iconForPlatform(platform.name),
    group,
  })
}

function openConnectModal(p: PlatformDef) {
  connectPlatform.value = p
  connectTab.value = 'login'
  const existing = savedAccounts.value.find((a) => a.platform === p.id)
  connectForm.username = existing?.username || ''
  connectForm.password = ''
  connectForm.cookie = existing?.cookie || ''
  connectForm.appid = existing?.appid || ''
  connectForm.appsecret = ''
  connectForm.clientId = ''
  connectForm.clientSecret = ''
  connectForm.accessToken = ''
  connectForm.refreshToken = ''
  connectForm.browser_profile_id = existing?.browser_profile_id || undefined
  connectForm.egress_endpoint_id = existing?.egress_endpoint_id || undefined
  if (existing?.nurture) Object.assign(nurtureForm, existing.nurture)
  else loadNurtureDefaults()
  loadEgressResources()
  connectModalVisible.value = true
}

async function ensurePlatformIdForConnect(p: PlatformDef): Promise<string | null> {
  if (!p.id.startsWith('offline-')) return p.id
  if (!apiOnline.value) return null
  const res = await fetch('/api/v1/seo-matrix/platforms', {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ name: p.name, region: p.group === 'intl' ? 'global' : 'cn' }),
  })
  const body = await res.json()
  if (!res.ok) return null
  const row = unwrapFetchedJson<Record<string, unknown>>(body) as Record<string, unknown>
  const mapped = mapApiPlatform(row)
  mapped.custom = true
  const idx = allPlatforms.value.findIndex((x) => x.name === p.name)
  if (idx >= 0) allPlatforms.value[idx] = mapped
  else allPlatforms.value.push(mapped)
  connectPlatform.value = mapped
  return mapped.id
}

async function handleConnectOk() {
  if (!connectPlatform.value) return
  if (!apiOnline.value) {
    message.error('后端未连接，请先运行 scripts/start-dev-admin.ps1 启动 API :8001')
    return
  }
  let platformId = connectPlatform.value.id
  if (platformId.startsWith('offline-')) {
    const resolved = await ensurePlatformIdForConnect(connectPlatform.value)
    if (!resolved) {
      message.error('无法注册该平台，请检查平台名称后重试')
      return
    }
    platformId = resolved
  }
  const mode = connectLoginMode.value

  if (mode === 'wechat_api') {
    if (!connectForm.appid.trim()) { message.warning('请输入 AppID'); return }
    if (!connectForm.appsecret.trim()) { message.warning('请输入 AppSecret'); return }
  } else if (mode === 'oauth_token') {
    if (!connectForm.username.trim() && !connectForm.accessToken.trim()) {
      message.warning('请填写账号或 Access Token'); return
    }
  } else if (!connectForm.username.trim()) {
    message.warning('请输入账号'); return
  }

  const payload: Record<string, unknown> = {
    platform: platformId,
    platform_name: connectPlatform.value.name,
    username: connectForm.username,
    password: connectForm.password,
    cookie: connectForm.cookie,
    nurture: { ...nurtureForm },
    browser_profile_id: connectForm.browser_profile_id,
    egress_endpoint_id: connectForm.egress_endpoint_id,
  }

  if (mode === 'wechat_api') {
    payload.configs = { appid: connectForm.appid.trim(), appsecret: connectForm.appsecret.trim() }
  } else if (mode === 'oauth_token') {
    payload.configs = {
      client_id: connectForm.clientId.trim(),
      client_secret: connectForm.clientSecret.trim(),
      access_token: connectForm.accessToken.trim(),
      refresh_token: connectForm.refreshToken.trim(),
    }
    payload.token_data = { access_token: connectForm.accessToken.trim() }
  }

  fetch('/api/v1/seo-matrix/accounts', {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  }).then(async (res) => {
    const body = await res.json()
    if (!res.ok) throw new Error(body.message || body.detail || 'Save account failed')
    const data = unwrapFetchedJson<Account & { nurture?: NurtureCfg; browser_profile_id?: string }>(body)
    const platId = platformId
    if (data?.nurture) Object.assign(nurtureForm, data.nurture)
    if (data?.browser_profile_id) connectForm.browser_profile_id = data.browser_profile_id
    const existing = savedAccounts.value.find((a) => a.platform === platId)
    const merged: Account = {
      id: String((data as Account)?.id || existing?.id || ''),
      platform: platId,
      username: connectForm.username,
      status: 'active',
      lastLogin: new Date().toISOString(),
      cookie: connectForm.cookie,
      appid: connectForm.appid,
      browser_profile_id: data?.browser_profile_id || connectForm.browser_profile_id,
      egress_endpoint_id: connectForm.egress_endpoint_id,
      nurture: data?.nurture ? { ...data.nurture } : { ...nurtureForm },
    }
    if (existing) Object.assign(existing, merged)
    else savedAccounts.value.push(merged)
    message.success(`「${connectPlatform.value!.name}」连接成功`)
    connectModalVisible.value = false
    void videoBindHubRef.value?.reload?.()
  }).catch((e: Error) => {
    message.error(e.message || '保存账号信息失败')
  })
}

/* ============================================================
   AI 内容生成
   ============================================================ */
const aiForm = reactive({
  contentType: 'news',
  style: 'formal',
  language: 'zh-CN',
  wordCount: '500',
  topic: '',
})

const aiGenerating  = ref(false)
const aiOptimizing  = ref(false)
const generatedContent = ref('')

const contentTypeLabel = computed(() => ({ news:'新闻稿', product:'产品介绍', industry:'行业资讯', seo:'SEO文章' }[aiForm.contentType] || aiForm.contentType))
const contentWordCount = computed(() => generatedContent.value.replace(/\s/g,'').length)

function generateContent() {
  const topic = aiForm.topic.trim()
  if (!topic) { message.warning('请输入主题或关键词'); return }
  aiGenerating.value = true
  fetch('/api/v1/seo-matrix/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
    body: JSON.stringify({ topic, contentType: aiForm.contentType, style: aiForm.style, language: aiForm.language, wordCount: aiForm.wordCount }),
  }).then(async res => {
    if (!res.ok) throw new Error('Generate failed')
    const body = await res.json()
    const data = unwrapFetchedJson<{ content?: string; text?: string; token_usage?: number }>(body)
    generatedContent.value = data?.content || data?.text || JSON.stringify(data)
    lastTokenUsage.value = Number(data?.token_usage || 0)
    void loadTokenQuota()
    message.success(
      lastTokenUsage.value > 0
        ? `内容生成完成（消耗 ${lastTokenUsage.value} Token）`
        : '内容生成完成',
    )
  }).catch(() => {
    message.error('AI 生成失败，请稍后重试')
  }).finally(() => {
    aiGenerating.value = false
  })
}

function optimizeContent() {
  if (!generatedContent.value) return
  aiOptimizing.value = true
  fetch('/api/v1/seo-matrix/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
    body: JSON.stringify({ content: generatedContent.value, style: aiForm.style }),
  }).then(async res => {
    if (!res.ok) throw new Error('Optimize failed')
    const body = await res.json()
    const data = unwrapFetchedJson<{ content?: string; text?: string; token_usage?: number }>(body)
    generatedContent.value = data?.content || data?.text || String(data)
    lastTokenUsage.value = Number(data?.token_usage || 0)
    void loadTokenQuota()
    message.success(
      lastTokenUsage.value > 0
        ? `内容优化完成（消耗 ${lastTokenUsage.value} Token）`
        : '内容优化完成',
    )
  }).catch(() => {
    message.error('优化失败，请稍后重试')
  }).finally(() => {
    aiOptimizing.value = false
  })
}

function clearContent() { generatedContent.value = '' }

/* ============================================================
   草稿系统
   ============================================================ */
interface Draft { id: string; title: string; content: string; type: string; typeLabel: string; time: string }
const drafts = ref<Draft[]>([])
const draftModalVisible = ref(false)
const draftCols = [
  { title:'标题', dataIndex:'title', width:200 },
  { title:'类型', key:'type', width:90 },
  { title:'时间', key:'time', width:150 },
  { title:'操作', key:'actions', width:130 },
]

function openDraftModal() { draftModalVisible.value = true }

function loadDraft(d: any) {
  generatedContent.value = d.content
  aiForm.topic = d.title
  aiForm.contentType = d.type
  draftModalVisible.value = false
  message.success('已加载草稿')
}

function deleteDraft(id: string) {
  drafts.value = drafts.value.filter(d => d.id !== id)
  message.success('草稿已删除')
}

function saveDraft() {
  if (!generatedContent.value) return
  fetch('/api/v1/seo-matrix/drafts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
    body: JSON.stringify({
      title: (aiForm.topic || '未命名草稿').substring(0, 30),
      content: generatedContent.value,
      type: aiForm.contentType,
    }),
  }).then(async res => {
    if (!res.ok) throw new Error('Save draft failed')
    const body = await res.json()
    const data = body.data || body
    if (data.id) drafts.value.unshift(data)
    message.success('已保存到草稿')
  }).catch(() => {
    message.error('保存草稿失败')
  })
}

/* ============================================================
   一键群发
   ============================================================ */
interface PubDetail { platformId: string; status: 'pending' | 'publishing' | 'success' | 'failed' }
interface PubResult { platformId: string; success: boolean; verified?: boolean; platform_post_url?: string; message?: string }

function isVerifiedPubResult(r: PubResult) {
  if (r.verified === false) return false
  const url = (r.platform_post_url || r.message || '').trim()
  if (url.startsWith('http')) return r.success === true || r.verified === true
  return false
}
interface PubRecord { id: string; time: string; content: string; type: string; results: PubResult[] }

const publishing = ref(false)
const publishProgress = reactive({ current:0, total:0, percent:0, details:[] as PubDetail[] })

const publishHistory = ref<PubRecord[]>([])

function quickDistribute() { if (generatedContent.value && selectedPlatforms.value.length > 0) startMassPublish() }

function startMassPublish() {
  if (publishing.value) return
  if (!generatedContent.value) { message.warning('请先生成内容或从草稿箱加载'); return }

  publishing.value = true
  const targets = [...selectedPlatforms.value]
  publishProgress.total   = targets.length
  publishProgress.current = 0
  publishProgress.percent = 0
  publishProgress.details = targets.map(p => ({ platformId: p.id, status: 'pending' as const }))

  fetch('/api/v1/seo-matrix/publish', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getAuthToken()}` },
    body: JSON.stringify({
      content: generatedContent.value,
      contentType: aiForm.contentType,
      platforms: targets.map(p => p.id),
    }),
  }).then(async res => {
    const body = await res.json()
    const data = body.data || body
    const results: PubResult[] = (data.results || data.platforms || []).map((r: any) => {
      const url = r.platform_post_url || (typeof r.message === 'string' && r.message.startsWith('http') ? r.message : '')
      const verified = r.verified !== false && !!url
      const ok = verified && (r.success ?? false)
      return {
        platformId: r.platformId || r.platform_id || r.id,
        success: ok,
        verified: ok,
        platform_post_url: url || undefined,
        message: r.message || (ok ? url : '发布失败'),
      }
    })
    const ok = results.filter(r => isVerifiedPubResult(r)).length
    // Update publish progress details from results
    targets.forEach((t, i) => {
      const r = results.find(rs => rs.platformId === t.id)
      if (r) {
        publishProgress.details[i] = { platformId: t.id, status: isVerifiedPubResult(r) ? 'success' : 'failed' }
      }
    })
    publishProgress.current = targets.length
    publishProgress.percent = 100
    message.success(`发布完成：${ok}/${targets.length} 个平台成功`)
    publishHistory.value.unshift({
      id: `pub-${Date.now()}`,
      time: new Date().toLocaleString('zh-CN'),
      content: generatedContent.value,
      type: aiForm.contentType,
      results,
    })
  }).catch(() => {
    message.error('发布请求失败，请稍后重试')
  }).finally(() => {
    publishing.value = false
  })
}

function retryFailed(record: any) {
  const failed = record.results.filter((r: { success: boolean; platformId: string }) => !r.success).map((r: { platformId: string }) => r.platformId)
  if (!failed.length) { message.warning('没有失败的发布'); return }
  selectedPlatforms.value = allPlatforms.value.filter(p => failed.includes(p.id))
  generatedContent.value = record.content
  message.success(`已选中 ${failed.length} 个失败平台，可重新发布`)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function getPubStatus(id: string) { return publishProgress.details.find(d => d.platformId === id)?.status || 'none' }
function getPubTagColor(id: string) {
  const m: Record<string,string> = { success:'green', failed:'red', publishing:'blue' }
  return m[getPubStatus(id)] || 'default'
}
function statusLabel(s: string) {
  const m: Record<string,string> = { pending:'等待中', publishing:'发布中...', success:'已发布', failed:'失败' }
  return m[s] || s
}

/* ============================================================
   历史详情
   ============================================================ */
const detailVisible = ref(false)
const detailRecord  = ref<PubRecord | null>(null)
function viewDetail(r: any) { detailRecord.value = r; detailVisible.value = true }

const historyCols = [
  { title:'发布时间', dataIndex:'time', width:150 },
  { title:'内容预览', key:'contentPrev', width:240 },
  { title:'发布结果', key:'results', width:300 },
  { title:'操作', key:'actions', width:140 },
]

// ── Load remote data on mount ──
onMounted(async () => {
  void loadTokenQuota()
  await loadPlatforms()
  const connectId = route.query.connect
  const connectName = route.query.connect_name
  if (typeof connectId === 'string' && connectId) {
    const p = allPlatforms.value.find((x) => x.id === connectId)
    if (p) openConnectModal(p)
    else if (typeof connectName === 'string') {
      openConnectModal({
        id: connectId,
        name: connectName,
        iconKey: iconForPlatform(connectName),
        group: FALLBACK_GLOBAL_NAMES.includes(connectName) ? 'intl' : 'cn',
      })
    }
  } else if (route.query.mode === 'video') {
    setTimeout(() => {
      document.querySelector('.video-bind-hub')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 300)
  }
  const prefill = consumePublishPrefill()
  if (prefill?.body) {
    generatedContent.value = prefill.body
    aiForm.topic = prefill.product || prefill.title || ''
    aiForm.contentType = 'product'
    aiForm.language = 'en'
    message.success('已载入一键开业生成的首篇草稿，选好平台即可发布')
  }
  const h = authHeaders()
  fetch('/api/v1/seo-matrix/accounts', { headers: h })
    .then(async (r) => {
      const d = unwrapFetchedJson<Account[]>(await r.json())
      if (Array.isArray(d)) savedAccounts.value = d
    })
    .catch(() => {})
  fetch('/api/v1/seo-matrix/drafts', { headers: h })
    .then(async (r) => {
      const d = unwrapFetchedJson<Draft[]>(await r.json())
      if (Array.isArray(d)) drafts.value = d
    })
    .catch(() => {})
  fetch('/api/v1/seo-matrix/publish-history', { headers: h })
    .then(async (r) => {
      const d = unwrapFetchedJson<PubRecord[]>(await r.json())
      if (Array.isArray(d)) publishHistory.value = d
    })
    .catch(() => {})
})
</script>

<style scoped lang="scss">
/* ========== Page ========== */
.publish-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-bottom: 100px;
}

.head {
  padding: 1.25rem 1.5rem;
  background: rgba(255,255,255,0.55);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  .title { margin:0; font-size:1.5rem; font-weight:700; }
  .sub   { margin-top:4px; color:#64748b; font-size:.85rem; }
}

.panel {
  padding: 1.25rem 1.5rem;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  .pt { margin:0 0 14px; font-size:1.05rem; font-weight:600; display:flex; align-items:center; gap:6px; }
}

.ml-2 { margin-left:8px; }

/* ========== AI Panel ========== */
.ai-panel {
  background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%);
  border: 1px solid rgba(0,184,148,0.15);
}

.ai-controls { margin-bottom:14px; }
.ctrl-label {
  display:block; font-size:.82rem; color:#475569; margin-bottom:4px; font-weight:500;
}
.ai-topic-row { margin-bottom:14px; }

.ai-actions {
  display:flex; gap:10px; margin-bottom:16px;
}

.ai-preview {
  border-top:1px solid #e2e8f0; padding-top:16px;
}
.preview-toolbar {
  display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;
  .preview-label { font-weight:600; font-size:.9rem; }
  .word-count    { font-size:.8rem; color:#94a3b8; }
}
.preview-textarea {
  resize:vertical; font-size:.88rem; line-height:1.7; border-radius:10px;
}
.preview-actions {
  display:flex; gap:10px; margin-top:12px;
}
.btn-distribute {
  background: linear-gradient(135deg, #00b894, #00cec9);
  border: none;
  &:hover { background: linear-gradient(135deg, #00a381, #00b8b5); }
}

.ai-empty {
  text-align:center; padding:40px 20px; color:#94a3b8;
  .empty-icon { font-size:42px; display:block; margin-bottom:12px; }
  p { margin:0; font-size:.9rem; }
}

/* ========== Platform Grid ========== */
.platform-group {
  margin-bottom:14px; border:1px solid #eef2f6; border-radius:12px; overflow:hidden;
}
.group-header {
  display:flex; align-items:center; gap:8px; padding:12px 16px;
  cursor:pointer; user-select:none; background:#f8fafc;
  transition:background .2s;
  &:hover { background:#f1f5f9; }
  .arrow-svg { width:12px; height:12px; color:#94a3b8; transition:transform .25s; flex-shrink:0; &.rotated { transform:rotate(90deg); } }
  .group-label { font-weight:600; font-size:.95rem; flex:1; }
  .group-badge { font-size:.75rem; color:#64748b; background:#e2e8f0; padding:1px 10px; border-radius:10px; }
}
.group-body { padding:14px; border-top:1px solid #eef2f6; }

.platform-grid {
  display:grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap:10px;
}

.platform-card {
  display:flex; flex-direction:column; align-items:center; gap:5px;
  padding:14px 8px 10px;
  border:1.5px solid #e2e8f0; border-radius:12px;
  cursor:pointer; transition:all .2s; position:relative;

  &:hover { border-color:#00b894; box-shadow:0 2px 8px rgba(0,184,148,0.12); }
  &.selected {
    border-color:#00b894;
    background:rgba(0,184,148,0.04);
    box-shadow:0 0 0 1px rgba(0,184,148,0.2);
    .pc-check { opacity:1; }
  }
  &.connected { border-color:#00b894; }

  .pc-check { position:absolute; top:6px; left:8px; opacity:0.3; transition:opacity .2s; }
  .pc-icon   { font-size:22px; line-height:1; }
  .pc-name   { font-size:.82rem; font-weight:600; text-align:center; line-height:1.3; }
  .pc-status {
    font-size:.68rem; padding:1px 10px; border-radius:8px;
    &.on  { color:#059669; background:rgba(5,150,105,0.1); }
    &.off { color:#94a3b8; background:rgba(148,163,184,0.1); }
  }
  .pc-connect { font-size:.7rem; height:24px; padding:0 8px; margin-top:2px; }
}

.token-quota-bar {
  margin-bottom: 12px;
}
.platform-hint {
  margin: 0 0 12px;
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.5;
}
.custom-platform-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0 8px;
  align-items: center;
}
.custom-platform-bar .ant-input {
  flex: 1;
  min-width: 200px;
}
.custom-platform-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.custom-label {
  font-size: 0.78rem;
  color: #64748b;
}
.custom-tag {
  cursor: pointer;
}
.platform-bulk { display:flex; gap:8px; margin-top:4px; }

/* ========== Publish Bar ========== */
.publish-bar {
  position:fixed; bottom:0; left:0; right:0;
  background:rgba(255,255,255,0.95);
  box-shadow:0 -4px 20px rgba(0,0,0,0.08);
  z-index:999; backdrop-filter:blur(8px);
  .publish-bar-inner {
    max-width:1200px; margin:0 auto;
    padding:12px 24px;
    display:flex; align-items:center; justify-content:space-between; gap:16px;
  }
}
.pb-left {
  display:flex; align-items:center; gap:8px; flex:1; min-width:0;
  .pb-label { font-size:.85rem; font-weight:600; white-space:nowrap; color:#334155; }
  .pb-tags  { display:flex; flex-wrap:wrap; gap:4px; flex:1; min-width:0; }
}
.mass-btn {
  font-weight:600; height:44px; font-size:1rem;
  padding:0 28px;
  background:linear-gradient(135deg,#00b894,#00cec9);
  border:none; white-space:nowrap;
  &:hover { background:linear-gradient(135deg,#00a381,#00b8b5); }
}

/* ========== Progress ========== */
.pub-progress { padding:12px 0; }
.pub-progress-items {
  display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;
  .ppi { font-size:.8rem; }
  .ppi-success    { color:#059669; }
  .ppi-failed     { color:#dc2626; }
  .ppi-publishing { color:var(--uj-brand, #4a9b8c); }
  .ppi-pending    { color:#94a3b8; }
}

/* ========== History ========== */
.content-prev { cursor:pointer; color:#475569; }
.result-tags  { display:flex; flex-wrap:wrap; gap:2px; }
</style>
