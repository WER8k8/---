<template>
  <YdPage title="开通向导" subtitle="跟着做就行：先开店 → 再让人看见 → 最后销售能接单" surface="elevated">
    <main class="onboarding-page coachpro-tertiary coachpro-tertiary--client max-w-3xl mx-auto py-6 px-4" aria-label="新手指引向导">
      <a-spin :spinning="loading" aria-live="polite">
        <a-steps :current="currentStep" class="mb-8" size="small" aria-label="开户步骤">
          <a-step title="欢迎开户" />
          <a-step title="AI 智能建站" />
          <a-step title="即时通讯" />
          <a-step title="旺财预览" />
          <a-step title="发布首篇" />
          <a-step title="完成" />
        </a-steps>

        <!-- Step 0: 一键开业 -->
        <div v-if="currentStep === 0" class="wizard-panel coachpro-panel p-6" role="region" aria-label="欢迎开户">
          <div v-if="!autopilotRunning && !autopilotResult" class="text-center">
            <div class="wizard-icon" aria-hidden="true">🚀</div>
            <h2 class="text-xl font-bold text-slate-900 mt-2">恭喜，{{ companyName }} 开户成功</h2>
            <p class="text-slate-600 mt-2 max-w-lg mx-auto">
              填上您卖啥（比如岩棉板），点<strong>一键开业</strong>，系统自动帮您：做官网、看哪个国家好卖、写好第一篇稿子。
            </p>
            <OnboardingPlainRoadmap
              v-if="onboardingRoadmap.length"
              class="mt-6 text-left"
              :phases="onboardingRoadmap"
              title="开户后完整路线（可先收藏）"
              subtitle="做完向导还要继续下面几步，销售才能收到客户消息"
            />
            <JtbdSiteChecklist
              v-if="jtbdChecklist.length"
              class="mt-6 text-left"
              :items="jtbdChecklist"
            />
            <div class="mt-6 text-left">
              <h3 class="text-sm font-semibold text-slate-800 mb-2">云存储 & 第三方账号（注册 / 实名）</h3>
              <p class="text-xs text-slate-500 mb-3">
                产品图由平台代开七牛/R2；发视频、绑抖音/微信等需按清单去对应官网注册。
              </p>
              <OnboardingExternalAccountsPanel />
            </div>
            <label for="onboarding-product" class="block text-sm font-medium text-slate-700 mt-6 mb-1">
              主营产品
            </label>
            <a-input
              id="onboarding-product"
              v-model:value="productName"
              size="large"
              class="max-w-md mx-auto"
              placeholder="主营产品，如：硅酸铝纤维、橡塑保温板"
              allow-clear
              aria-describedby="onboarding-product-hint"
              @press-enter="startAutopilot"
            />
            <p id="onboarding-product-hint" class="text-xs text-slate-500 mt-1">必填，用于生成官网与蓝海建议</p>
            <div class="mt-6 flex flex-wrap gap-3 justify-center">
              <a-button
                type="primary"
                size="large"
                :loading="autopilotRunning"
                :disabled="!productName.trim()"
                @click="startAutopilot"
              >
                一键开业（Time-to-Value）
              </a-button>
              <a-button size="large" @click="goStep(1)">高级 · 分步操作</a-button>
            </div>
          </div>

          <div v-else-if="autopilotRunning">
            <h2 class="text-lg font-bold text-slate-900 mb-2">正在为您开业…</h2>
            <p class="text-sm text-slate-500 mb-4">
              注册后已在后台自动开业，通常 30–90 秒。您无需再点其他菜单。
            </p>
            <OnboardingAutopilotProgress
              :steps="autopilotSteps"
              :running="true"
              :active-id="autopilotActiveStep"
            />
          </div>

          <div v-else-if="autopilotResult" class="text-center">
            <div class="wizard-icon">✨</div>
            <h2 class="text-xl font-bold text-slate-900 mt-2">开业完成</h2>
            <p class="text-base text-teal-800 font-medium mt-3 max-w-lg mx-auto">
              {{ autopilotResult.headline }}
            </p>
            <OnboardingAutopilotProgress :steps="autopilotSteps" class="mt-6 text-left" />
            <div class="mt-8 flex flex-wrap gap-3 justify-center">
              <a-button type="primary" size="large" @click="router.push('/client/distribute')">
                进入内容分发
              </a-button>
              <a-button size="large" @click="openPlatformBind">绑第一个平台</a-button>
              <a-button size="large" @click="finishAfterAutopilot('/client/dashboard')">
                进入工作台
              </a-button>
              <a-button size="large" @click="openSitePreview">预览官网</a-button>
            </div>
          </div>
        </div>

        

        <!-- Step 1: AI Site Build -->
        <div v-else-if="currentStep === 1" class="wizard-panel coachpro-panel p-6">
          <h2 class="text-lg font-bold text-slate-900 mb-1">AI 智能建站</h2>
          <p class="text-sm text-slate-500 mb-5">
            输入主营产品即可；专业英文文案与页面结构由智能建站引擎生成。有产品白底图可一并上传，系统会自动挂到产品列表。
          </p>

          <div class="flex flex-col sm:flex-row gap-3 mb-3">
            <a-input
              v-model:value="productName"
              size="large"
              placeholder="如：硅酸铝纤维、橡胶保温板"
              allow-clear
              :disabled="generating || productImagesUploading"
              @press-enter="generateSite"
            />
            <a-button size="large" :disabled="generating || productImagesUploading" @click="productImagesInput?.click()">
              <template #icon><PictureOutlined /></template>
              产品图
            </a-button>
            <a-button type="primary" size="large" :loading="generating" :disabled="productImagesUploading" @click="generateSite">
              <template #icon><ThunderboltOutlined /></template>
              一键生成并保存
            </a-button>
          </div>
          <p v-if="generating" class="text-xs text-blue-600 mt-2 mb-0">
            正在 AI 生成官网文案与结构并保存，通常约 20–40 秒，请勿关闭页面…
          </p>
          <input
            ref="productImagesInput"
            type="file"
            accept="image/*"
            multiple
            style="display:none"
            @change="handleProductImagesPick"
          />
          <div v-if="productImages.length" class="flex flex-wrap gap-2 mb-4">
            <img
              v-for="img in productImages"
              :key="img.url"
              :src="img.url"
              :alt="img.name"
              class="w-12 h-12 object-contain border border-slate-200 rounded bg-white"
            />
          </div>

          <a-alert
            v-if="!siteBuilt && !generatedPreview"
            type="info"
            show-icon
            message="提示"
            description="生成后会自动保存。您只需提供产品名和可选的产品白底图，文案与页面结构由智能建站引擎生成。"
            class="mb-4"
          />

          <div v-if="generatedPreview" class="site-preview-card rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div class="flex items-center justify-between mb-3">
              <span class="text-sm font-semibold text-slate-800">生成预览</span>
              <a-tag :color="generateSource === 'ai' ? 'blue' : 'default'">
                {{ generateSource === 'ai' ? 'AI 生成' : '智能模板' }}
              </a-tag>
            </div>
            <div class="preview-row">
              <span class="preview-label">公司名称</span>
              <span>{{ generatedPreview.brand?.name || '—' }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">首页大标题</span>
              <span>{{ generatedPreview.pages?.home?.title || '—' }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">核心优势</span>
              <span>{{ (generatedPreview.pages?.home?.features || []).join(' · ') || '—' }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">产品列表</span>
              <span>{{ (generatedPreview.pages?.products?.products || []).join('、') || '—' }}</span>
            </div>
            <div v-if="sitePreviewUrl" class="mt-4">
              <a-alert type="success" show-icon>
                <template #message>
                  官网已生成，可预览
                  <a :href="sitePreviewUrl" target="_blank" rel="noopener" class="ml-2">打开租户站 →</a>
                </template>
              </a-alert>
            </div>
          </div>

          <div class="flex flex-wrap gap-3 mt-6 justify-end">
            <a-button v-if="sitePreviewUrl" @click="openSitePreview">预览官网</a-button>
            <a-button v-if="siteBuilt" @click="router.push({ path: '/client/site-editor', query: { side: 'gap' } })">补齐发布项</a-button>
            <a-button v-if="siteBuilt" type="primary" @click="goStep(2)">
              添加 WhatsApp / 微信
            </a-button>
          </div>
        </div>

        <!-- Step 2: IM contacts + 指引旺财 -->
        <div v-else-if="currentStep === 2" class="wizard-panel coachpro-panel p-6">
          <h2 class="text-lg font-bold text-slate-900 mb-1">留联系方式给客户</h2>
          <p class="text-sm text-slate-500 mb-4">
            填微信、电话、WhatsApp 等，会显示在官网「联系我们」。<strong>注意：</strong>这一步是让客户找得到你，还不是销售手机自动收消息（那在第 5 步后面弄）。
          </p>
          <OnboardingImContactsPanel @done="goStep(3)" />
        </div>

        <!-- Step 3: Wangcai + site preview -->
        <div v-else-if="currentStep === 3" class="wizard-panel coachpro-panel p-6">
          <h2 class="text-lg font-bold text-slate-900 mb-1">旺财 · 出口问答预览</h2>
          <p class="text-sm text-slate-500 mb-4">
            建站已完成。客户在官网右下角看到的 Trade Q&amp;A 与此一致；请先试问蓝海/出口问题。
          </p>
          <div v-if="sitePreviewUrl" class="mb-4">
            <a-alert type="success" show-icon>
              <template #message>
                官网预览
                <a :href="sitePreviewUrl" target="_blank" rel="noopener" class="ml-2">打开租户站 →</a>
              </template>
              <template #description>
                本地开发请同时运行 Nuxt（:3000）；生产域名为 {{ sitePreviewProduction || '—' }}
              </template>
            </a-alert>
          </div>
          <OnboardingWangcaiPanel
            :product-hint="productName"
            :site-preview-url="sitePreviewUrl"
            :preview-done="wangcaiPreviewDone"
            :initial-prompts="wangcaiPrompts"
            @done="goStep(4)"
          />
        </div>

        <!-- Step 4: First publish -->
        <div v-else-if="currentStep === 4" class="wizard-panel coachpro-panel p-6">
          <h2 class="text-lg font-bold text-slate-900 mb-1">发布首篇</h2>
          <p class="text-sm text-slate-500 mb-4">
            系统将根据主营产品生成英文引流稿，并入队到您的第一个平台位（未绑 OAuth 时需稍后在「多平台分发」补绑）。
          </p>
          <a-alert v-if="firstPublishPreview" type="info" show-icon class="mb-4">
            <template #message>{{ firstPublishPreview.title }}</template>
            <template #description>
              <pre class="publish-preview-text">{{ firstPublishPreview.preview }}</pre>
            </template>
          </a-alert>
          <div class="flex flex-wrap gap-3 justify-end">
            <a-button
              type="primary"
              size="large"
              :loading="publishing"
              :disabled="firstPublishDone"
              @click="runFirstPublish"
            >
              {{ firstPublishDone ? '首篇已入队' : '一键生成并入队' }}
            </a-button>
            <a-button size="large" @click="goStep(5)">跳过，稍后发布</a-button>
          </div>
        </div>

        <!-- Step 5: Next steps -->
        <div v-else-if="currentStep === 5" class="wizard-panel">
          <div
            v-if="salesChannelSteps.length"
            class="coachpro-panel p-5 mb-4"
            role="region"
            aria-label="七步第5步询盘IM"
          >
            <h2 class="text-base font-bold text-slate-900 mb-1">最重要：销售怎么收到客户</h2>
            <p class="text-xs text-slate-500 mb-4">
              顺序别乱：①客户留言能进系统 → ②销售企微能收到 → ③抖音评论自动抓。中间那步最容易漏。
            </p>
            <ul class="space-y-2">
              <li
                v-for="sub in salesChannelSteps"
                :key="sub.id"
                class="flex items-start justify-between gap-3 rounded-lg border border-slate-100 px-3 py-2 text-sm"
              >
                <div>
                  <span class="font-medium text-slate-800">{{ sub.id }} {{ sub.title }}</span>
                  <p class="text-xs text-slate-500 mt-0.5">{{ sub.detail }}</p>
                </div>
                <a-button
                  size="small"
                  :type="sub.done ? 'default' : 'primary'"
                  @click="router.push(sub.route)"
                >
                  {{ sub.done ? '查看' : '去配置' }}
                </a-button>
              </li>
            </ul>
          </div>

          <OnboardingPlainRoadmap
            v-if="onboardingRoadmap.length"
            class="mb-4"
            :phases="onboardingRoadmap"
          />

          <TenantOnboardingChecklist v-if="checklist.length" :checklist="checklist" title="逐项清单" />

          <div v-if="platforms.length" class="mt-4 coachpro-panel p-5">
            <h2 class="text-base font-bold text-slate-900 mb-3">已预置平台位</h2>
            <ul class="space-y-2">
              <li
                v-for="p in platforms"
                :key="p.platform_id || p.platform_name"
                class="flex flex-wrap items-center gap-2 text-sm"
              >
                <a-tag color="blue">{{ p.platform_name }}</a-tag>
                <span class="text-xs text-slate-500">{{ p.connect_hint || '待绑定' }}</span>
              </li>
            </ul>
            <p class="text-xs text-slate-500 mt-3">稍后在「平台绑定」中完成 OAuth 或 Cookie 绑定即可发布。</p>
          </div>

          <div class="mt-6 flex flex-wrap gap-3 justify-center">
            <a-button type="primary" size="large" @click="currentStep = 6">完成指引</a-button>
            <a-button size="large" @click="router.push('/client/queues/publish')">查看发布队列</a-button>
            <a-button size="large" @click="router.push({ path: '/client/distribute', query: { focus: 'bind' } })">绑定视频平台</a-button>
          </div>
        </div>

        <!-- Step 6: Done -->
        <div v-else class="wizard-panel coachpro-panel p-6 text-center">
          <div class="wizard-icon">✅</div>
          <h2 class="text-xl font-bold text-slate-900 mt-2">新手指引完成</h2>
          <p class="text-slate-500 mt-2">官网有了。接下来记得：绑抖音发视频 → 配销售收消息 → 天天看询盘。</p>
          <OnboardingPlainRoadmap
            v-if="onboardingRoadmap.length"
            class="mt-6 text-left"
            :phases="onboardingRoadmap"
            title="还没做完的在这里继续"
          />
          <div class="mt-8 flex flex-wrap gap-3 justify-center">
            <a-button type="primary" size="large" @click="finishWizard('/client/dashboard')">
              进工作台
            </a-button>
            <a-button size="large" @click="router.push('/client/distribute')">去绑抖音</a-button>
            <a-button size="large" @click="finishWizard('/client/site-editor')">改官网</a-button>
          </div>
        </div>

        <!-- 模态:平台绑定(放在向导链外部,避免打断 v-if/v-else-if) -->
        <OnboardingPlatformBind
          v-model:open="platformBindOpen"
          @bound="onPlatformBound"
          @skip="platformBindOpen = false"
        />
      </a-spin>
    </main>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { ThunderboltOutlined, PictureOutlined } from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost } from '@/utils/api';
import { runHermesSiteBuilder } from '@/utils/hermesSiteBuilder';
import {
  uploadSiteProductImages,
  productImageUrls,
  type UploadedProductImage,
} from '@/utils/siteProductImages';
import { refreshOnboardingPreviewUrl } from '@/utils/siteEditorLabSync';
import OnboardingWangcaiPanel from '@/components/tenant/OnboardingWangcaiPanel.vue';
import OnboardingImContactsPanel from '@/components/tenant/OnboardingImContactsPanel.vue';
import OnboardingAutopilotProgress from '@/components/tenant/OnboardingAutopilotProgress.vue';
import OnboardingPlatformBind from '@/components/tenant/OnboardingPlatformBind.vue';
import {
  runOnboardingAutopilot,
  sitePreviewHref,
  type AutopilotResult,
  type AutopilotStep,
} from '@/utils/onboardingAutopilot';
import OnboardingPlainRoadmap, {
  type RoadmapPhase,
} from '@/components/tenant/OnboardingPlainRoadmap.vue';
import OnboardingExternalAccountsPanel from '@/components/tenant/OnboardingExternalAccountsPanel.vue';
import JtbdSiteChecklist, {
  type JtbdChecklistItem,
} from '@/components/site-builder/JtbdSiteChecklist.vue';
import TenantOnboardingChecklist, {
  type ChecklistItem,
} from '@/components/tenant/TenantOnboardingChecklist.vue';

const ONBOARDING_PENDING_KEY = 'tenant_onboarding_pending';

const router = useRouter();
const route = useRoute();
const loading = ref(true);
const currentStep = ref(0);
const companyName = ref('您的企业');
const productName = ref('');
const generating = ref(false);
const productImagesUploading = ref(false);
const productImages = ref<UploadedProductImage[]>([]);
const productImagesInput = ref<HTMLInputElement>();
const siteBuilt = ref(false);
const wangcaiPreviewDone = ref(false);
const firstPublishDone = ref(false);
const sitePreviewUrl = ref('');
const sitePreviewProduction = ref('');
const wangcaiPrompts = ref<{ id: string; label: string }[]>([]);
const publishing = ref(false);
const firstPublishPreview = ref<{ title?: string; preview?: string } | null>(null);
const autopilotRunning = ref(false);
const autopilotResult = ref<AutopilotResult | null>(null);
const autopilotSteps = ref<AutopilotStep[]>([]);
const autopilotActiveStep = ref('hermes');
const platformBindOpen = ref(false);
const autopilotPollTimer = ref<ReturnType<typeof setInterval> | null>(null);
const generateSource = ref<'ai' | 'template'>('template');
const generatedPreview = ref<Record<string, any> | null>(null);
const checklist = ref<ChecklistItem[]>([]);
const onboardingRoadmap = ref<RoadmapPhase[]>([]);
const jtbdChecklist = ref<JtbdChecklistItem[]>([]);
const salesChannelSteps = ref<
  {
    id: string;
    key: string;
    title: string;
    detail: string;
    route: string;
    done: boolean;
  }[]
>([]);
const platforms = ref<
  {
    platform_id?: string;
    platform_name?: string;
    connect_hint?: string;
    admin_path?: string;
    status?: string;
  }[]
>([]);

function chainStepToIndex(step: string, wizardDone: boolean): number {
  if (wizardDone) return 6;
  const map: Record<string, number> = {
    welcome: 0,
    hermes: 1,
    im_contacts: 2,
    wangcai: 3,
    publish: 4,
    review: 5,
    done: 6,
  };
  return map[step] ?? 0;
}

function goStep(n: number) {
  currentStep.value = n;
}

async function loadOnboarding() {
  loading.value = true;
  try {
    const status = await apiGet<{
      site_built?: boolean;
      wizard_completed?: boolean;
      autopilot_completed?: boolean;
      primary_product?: string;
      company_name?: string;
      chain_step?: string;
      im_contacts_done?: boolean;
      wangcai_preview_done?: boolean;
      first_publish_done?: boolean;
      first_platform_bound?: boolean;
      site_preview_dev_url?: string;
      site_preview_url?: string;
      wangcai_prompts?: { id: string; label: string }[];
      autopilot?: AutopilotResult;
      autopilot_job?: { status?: string; headline?: string; error?: string };
      sales_channel_steps?: {
        id: string;
        key: string;
        title: string;
        detail: string;
        route: string;
        done: boolean;
      }[];
      checklist?: ChecklistItem[];
      onboarding_roadmap?: RoadmapPhase[];
    }>('/tenants/self/onboarding-status');

    salesChannelSteps.value = status?.sales_channel_steps || [];
    onboardingRoadmap.value = status?.onboarding_roadmap || [];
    if (status?.checklist?.length) {
      checklist.value = status.checklist;
    }

    companyName.value = status?.company_name || '您的企业';
    productName.value =
      String(route.query.product || status?.primary_product || '').trim();
    siteBuilt.value = Boolean(status?.site_built);
    wangcaiPreviewDone.value = Boolean(status?.wangcai_preview_done);
    firstPublishDone.value = Boolean(status?.first_publish_done);
    sitePreviewProduction.value = status?.site_preview_url || '';
    sitePreviewUrl.value =
      import.meta.env.DEV && status?.site_preview_dev_url
        ? status.site_preview_dev_url
        : status?.site_preview_url || status?.site_preview_dev_url || '';
    wangcaiPrompts.value = (status?.wangcai_prompts || []).map((p, i) => ({
      id: p.id || `p-${i}`,
      label: p.label || String(p),
    }));

    if (status?.wizard_completed || status?.autopilot_completed) {
      localStorage.removeItem(ONBOARDING_PENDING_KEY);
      if (status?.autopilot?.ok) {
        autopilotResult.value = status.autopilot as AutopilotResult;
        autopilotSteps.value = autopilotResult.value.steps || [];
        currentStep.value = 0;
        if (!status?.first_platform_bound) {
          platformBindOpen.value = true;
        }
      } else {
        currentStep.value = 6;
      }
    } else {
      const jobStatus = status?.autopilot_job?.status;
      if (jobStatus === 'running' || jobStatus === 'pending') {
        currentStep.value = 0;
        autopilotRunning.value = true;
        autopilotSteps.value = [
          { id: 'hermes', label: 'AI 智能建站' },
          { id: 'wangcai', label: '旺财 · 蓝海雷达' },
          { id: 'publish', label: '首篇引流稿' },
        ];
        startAutopilotPoll();
      } else if (
        (jobStatus === 'done' || jobStatus === 'partial') &&
        status?.autopilot?.ok
      ) {
        autopilotResult.value = status.autopilot as AutopilotResult;
        autopilotSteps.value = autopilotResult.value.steps || [];
        currentStep.value = 0;
        if (!status?.first_platform_bound) {
          platformBindOpen.value = true;
        }
      } else {
        currentStep.value = chainStepToIndex(status?.chain_step || 'welcome', false);
        if (currentStep.value === 0 && !siteBuilt.value) {
          localStorage.setItem(ONBOARDING_PENDING_KEY, '1');
        }
        const autostart =
          route.query.autostart === '1' || route.query.autostart === 'true';
        if (
          autostart &&
          productName.value.trim() &&
          !status?.autopilot_completed &&
          !jobStatus
        ) {
          void startAutopilot();
        }
      }
    }

    const data = await apiGet<{
      onboarding?: {
        checklist?: ChecklistItem[];
        roadmap?: RoadmapPhase[];
        platforms?: { platform_id?: string; platform_name?: string }[];
      };
    }>('/tenants/current');
    const ob = data?.onboarding;
    checklist.value = ob?.checklist || [];
    if (ob?.roadmap?.length) {
      onboardingRoadmap.value = ob.roadmap;
    }
    platforms.value = ob?.platforms || [];

    try {
      const guides = await apiGet<{ jtbd_checklist?: JtbdChecklistItem[] }>('/client/onboarding-guides');
      jtbdChecklist.value = guides?.jtbd_checklist || [];
    } catch {
      jtbdChecklist.value = [];
    }
  } catch {
    message.warning('无法加载开户信息，请稍后重试');
  } finally {
    loading.value = false;
  }
}

async function handleProductImagesPick(e: Event) {
  const input = e.target as HTMLInputElement;
  const files = input.files ? Array.from(input.files) : [];
  input.value = '';
  if (!files.length) return;
  productImagesUploading.value = true;
  try {
    const uploaded = await uploadSiteProductImages(files);
    productImages.value.push(...uploaded);
    message.success(`已上传 ${uploaded.length} 张产品图`);
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '产品图上传失败');
  } finally {
    productImagesUploading.value = false;
  }
}

function stopAutopilotPoll() {
  if (autopilotPollTimer.value) {
    clearInterval(autopilotPollTimer.value);
    autopilotPollTimer.value = null;
  }
}

function startAutopilotPoll() {
  stopAutopilotPoll();
  autopilotPollTimer.value = setInterval(async () => {
    try {
      const status = await apiGet<{
        autopilot_completed?: boolean;
        autopilot?: AutopilotResult;
        autopilot_job?: { status?: string };
        first_platform_bound?: boolean;
        site_preview_dev_url?: string;
        site_preview_url?: string;
      }>('/tenants/self/onboarding-status');
      const jobStatus = status?.autopilot_job?.status;
      if (jobStatus === 'running' || jobStatus === 'pending') return;
      stopAutopilotPoll();
      autopilotRunning.value = false;
      if (status?.autopilot?.ok || status?.autopilot_completed) {
        autopilotResult.value = (status.autopilot || {}) as AutopilotResult;
        autopilotSteps.value = autopilotResult.value.steps || [];
        siteBuilt.value = true;
        wangcaiPreviewDone.value = true;
        firstPublishDone.value = true;
        if (status.site_preview_dev_url || status.site_preview_url) {
          sitePreviewUrl.value =
            import.meta.env.DEV && status.site_preview_dev_url
              ? status.site_preview_dev_url
              : status.site_preview_url || status.site_preview_dev_url || '';
        }
        message.success(autopilotResult.value.headline || '一键开业完成');
        if (!status.first_platform_bound) {
          platformBindOpen.value = true;
        }
      } else if (jobStatus === 'failed') {
        message.warning('后台开业未完成，可手动一键开业或分步操作');
      }
    } catch {
      /* 静默轮询 */
    }
  }, 2500);
}

function openPlatformBind() {
  router.push({ path: '/client/distribute', query: { focus: 'bind' } });
}

function onPlatformBound(payload: { queued_task_id?: string | null }) {
  if (payload?.queued_task_id) {
    firstPublishDone.value = true;
  }
}

async function startAutopilot() {
  const name = productName.value.trim();
  if (!name) {
    message.warning('请先输入主营产品');
    return;
  }
  autopilotRunning.value = true;
  autopilotResult.value = null;
  autopilotSteps.value = [
    { id: 'hermes', label: 'AI 智能建站' },
    { id: 'wangcai', label: '旺财 · 蓝海雷达' },
    { id: 'publish', label: '首篇引流稿' },
  ];
  autopilotActiveStep.value = 'hermes';
  try {
    autopilotActiveStep.value = 'wangcai';
    const result = await runOnboardingAutopilot({
      productName: name,
      productImages: productImageUrls(productImages.value),
    });
    autopilotActiveStep.value = 'publish';
    autopilotSteps.value = result.steps || [];
    autopilotResult.value = result;
    siteBuilt.value = true;
    wangcaiPreviewDone.value = true;
    firstPublishDone.value = true;
    if (result.site_preview_dev_url || result.site_preview_url) {
      sitePreviewUrl.value = sitePreviewHref(result);
    }
    if (result.ok) {
      message.success(result.headline || '一键开业完成');
      localStorage.setItem('tenant_autopilot_headline', result.headline || '');
      if (!platformBindOpen.value) {
        platformBindOpen.value = true;
      }
    } else {
      message.warning('部分步骤未完成，可继续分步操作或重试');
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '一键开业失败');
  } finally {
    autopilotRunning.value = false;
    autopilotActiveStep.value = '';
  }
}

function openSitePreview() {
  const url = autopilotResult.value ? sitePreviewHref(autopilotResult.value) : sitePreviewUrl.value;
  if (url && url !== '#') window.open(url, '_blank', 'noopener');
}

async function finishAfterAutopilot(path: string) {
  try {
    await apiPost('/tenants/self/onboarding-wizard/complete', { skip_remaining: false });
  } catch {
    /* 非阻塞：autopilot 可能已标记完成 */
  }
  localStorage.removeItem(ONBOARDING_PENDING_KEY);
  localStorage.setItem('chuhaiji_onboarding_done', '1');
  router.replace(path);
}

async function generateSite() {
  const name = productName.value.trim();
  if (!name) {
    message.warning('请先输入主营产品名称');
    return;
  }
  generating.value = true;
  let hideLoading: (() => void) | undefined;
  hideLoading = message.loading('正在 AI 建站并保存，约需 20–40 秒…', 0);
  try {
    const result = await runHermesSiteBuilder({
      productName: name,
      autoSave: true,
      productImages: productImageUrls(productImages.value),
      runProductResearch: false,
      skipI18nAi: true,
    });
    generatedPreview.value = result.siteContent;
    generateSource.value = result.source;
    siteBuilt.value = result.saved;
    try {
      const preview = await refreshOnboardingPreviewUrl();
      sitePreviewProduction.value = preview.prod || '';
      sitePreviewUrl.value =
        import.meta.env.DEV && preview.dev
          ? preview.dev
          : preview.prod || preview.dev || '';
    } catch {
      /* 非阻塞 */
    }
    message.success(result.reply || (siteBuilt.value ? '网站已生成并保存！' : '网站内容已生成'));
    if (siteBuilt.value) {
      checklist.value = checklist.value.map((item) =>
        item.key === 'site' ? { ...item, status: 'done', detail: '官网已生成（设计规范已锁定）' } : item,
      );
      goStep(2);
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '生成失败';
    message.error(msg);
  } finally {
    hideLoading?.();
    generating.value = false;
  }
}

async function runFirstPublish() {
  publishing.value = true;
  try {
    const data = await apiPost<{
      already_done?: boolean;
      title?: string;
      preview?: string;
      task_id?: string;
    }>('/tenants/self/onboarding-chain/first-publish', {});
    firstPublishDone.value = true;
    firstPublishPreview.value = { title: data?.title, preview: data?.preview };
    message.success(
      data?.task_id ? '首篇已入队，可在发布队列查看' : '首篇草稿已生成',
    );
    goStep(5);
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '发布首篇失败');
  } finally {
    publishing.value = false;
  }
}

async function finishWizard(path: string) {
  try {
    await apiPost('/tenants/self/onboarding-wizard/complete', { skip_remaining: false });
  } catch {
    /* 非阻塞 */
  }
  localStorage.removeItem(ONBOARDING_PENDING_KEY);
  localStorage.setItem('chuhaiji_onboarding_done', '1');
  router.replace(path);
}

onMounted(loadOnboarding);
onUnmounted(stopAutopilotPoll);
</script>

<style scoped>
.onboarding-page {
  min-height: calc(100vh - 80px);
}
.wizard-panel :focus-visible {
  outline: 2px solid var(--uj-brand, #4a9b8c);
  outline-offset: 2px;
}

.wizard-panel {
  min-height: 320px;
}

.wizard-icon {
  font-size: 3rem;
  line-height: 1;
}

.wizard-highlights li {
  list-style: none;
}

.site-preview-card {
  animation: fadeIn 0.3s ease;
}

.preview-row {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  font-size: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.preview-row:last-child {
  border-bottom: none;
}

.preview-label {
  flex: 0 0 88px;
  color: #64748b;
}

.publish-preview-text {
  white-space: pre-wrap;
  font-size: 12px;
  margin: 8px 0 0;
  color: #475569;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
