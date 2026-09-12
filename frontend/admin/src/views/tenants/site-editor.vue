<template>
  <YdPage surface="elevated">
  <div class="site-editor-space">
    <a-alert
      v-if="tenantLoadHint"
      type="info"
      show-icon
      class="mb-4"
      :message="tenantLoadHint"
      closable
      @close="tenantLoadHint = ''"
    />
    <!-- Header：产品名 + 产品图 + AI 一键生成 -->
    <div class="site-editor-header mb-4">
      <div class="site-editor-ai-block">
        <div class="site-editor-ai-row">
          <h1 class="site-editor-ai-label">AI智能建站</h1>
          <a-input
            v-model:value="aiProductName"
            class="site-editor-ai-input"
            placeholder="您卖什么？如：硅酸铝纤维、橡胶保温板"
            allow-clear
            :disabled="aiGenerating || productImagesUploading"
            @press-enter="runAiGenerate"
          />
          <a-button type="primary" :loading="aiGenerating" :disabled="productImagesUploading" @click="runAiGenerate">
            <template #icon><ThunderboltOutlined /></template>
            一键生成
          </a-button>
        </div>
        <p class="site-editor-ai-subhint">
          AI 生成后自动套用企业站版式（顶栏/认证/数据条/多栏页脚）；可在可视化模式换模板、插区块微调。
        </p>
        <div class="site-editor-product-images">
          <input
            ref="productImagesInput"
            type="file"
            accept="image/*"
            multiple
            style="display:none"
            @change="handleProductImagesPick"
          />
          <a-button size="small" :loading="productImagesUploading" @click="productImagesInput?.click()">
            <template #icon><PictureOutlined /></template>
            快速上传产品图
          </a-button>
          <a-button size="small" type="link" @click="goProductImageSpace">
            产品图片空间
          </a-button>
          <div v-if="productImages.length" class="site-editor-product-thumbs">
            <div v-for="(img, i) in productImages" :key="img.url" class="site-editor-product-thumb">
              <img :src="img.url" :alt="img.name" />
              <button type="button" class="site-editor-product-remove" @click="removeProductImage(i)">×</button>
            </div>
          </div>
        </div>
      </div>
      <div class="site-editor-header-tools">
        <a-button class="site-editor-template-btn" @click="templatePickerOpen = true">
          <template #icon><AppstoreOutlined /></template>
          {{ currentTemplateMeta?.name || '选择模板' }}
        </a-button>
        <a-radio-group v-model:value="editorMode" size="small" button-style="solid">
          <a-radio-button value="visual">可视化拖拽</a-radio-button>
          <a-radio-button value="form">表单编辑</a-radio-button>
        </a-radio-group>
        <a-button v-if="tenantPreviewUrl" type="default" @click="openTenantPreview">
          <template #icon><EyeOutlined /></template>
          预览网站
        </a-button>
        <a-button type="primary" :loading="saving" @click="saveContent">
          <template #icon><SaveOutlined /></template>
          保存
        </a-button>
      </div>
    </div>
    <p v-if="lastDesignSkills.length || lastEccExperts.length" class="site-editor-ai-hint mb-4">
      <span v-if="lastEccExperts.length">设计专家：{{ lastEccExperts.join(' · ') }}</span>
      <span v-if="lastDesignSkills.length">{{ lastEccExperts.length ? ' · ' : '' }}设计技能：{{ lastDesignSkills.join(' · ') }}</span>
    </p>

    <p v-if="currentTemplateMeta" class="site-editor-template-desc mb-3">
      {{ currentTemplateMeta.description }}
    </p>

    <SiteEditorLProPublishBanner
      :site-content="siteContentForGate"
      :template-id="selectedTemplateId"
    />

    <div v-if="editorMode === 'visual'" class="site-editor-visual-row">
      <div class="site-editor-visual-main">
        <YdGrapesSiteEditor
          ref="visualEditorRef"
          v-model:template-id="selectedTemplateId"
          :site-snapshot="siteSnapshot"
          :visual-payload="savedVisualPayload"
          @request-save="saveContent"
        />
      </div>
      <SiteEditorRightPanel
        v-model:seo-model="seoFields"
        :site-content="siteContentForGate"
        :site-url="tenantSiteUrl"
        :initial-tab="rightPanelTab"
        @gap-apply="onGapApply"
      />
    </div>

    <SiteTemplatePickerModal
      v-model:open="templatePickerOpen"
      v-model:template-id="selectedTemplateId"
      @select="onTemplatePick"
    />

    <!-- Page Tabs（表单模式） -->
    <a-card v-if="editorMode === 'form'" :body-style="{ padding: '0' }" class="mb-4">
      <div class="page-tabs">
        <button
          v-for="pg in pages"
          :key="pg.key"
          class="page-tab"
          :class="{ active: activePage === pg.key }"
          @click="switchPage(pg.key)"
        >
          {{ pg.label }}
        </button>
      </div>
    </a-card>

    <div v-if="editorMode === 'form'" class="editor-layout">
      <!-- Center: Preview -->
      <div class="preview-panel">
        <a-card title="网站预览" :body-style="{ padding: '16px' }">
          <div class="preview-frame">
            <!-- Header -->
            <div
              class="preview-header preview-editable-zone"
              :style="{ background: previewData.theme?.headerBg || '#1e293b' }"
              @click="scrollToField('siteHeader')"
            >
              <div class="preview-header-inner">
                <div class="preview-brand">
                  <div class="preview-logo">{{ previewData.brand?.name || '公司名称' }}</div>
                  <div v-if="previewData.brand?.tagline" class="preview-tagline">{{ previewData.brand.tagline }}</div>
                </div>
                <div class="preview-nav">
                  <span v-for="pg in pages" :key="pg.key"
                    class="preview-nav-item"
                    :class="{ active: activePage === pg.key }"
                    @click.stop="switchPage(pg.key)"
                  >
                    {{ pg.label }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Hero -->
            <div class="preview-hero" :style="{ background: previewData.theme?.heroBg || '#f1f5f9' }">
              <div class="preview-hero-content">
                <h2 class="preview-hero-title">{{ pageContent.title || '大标题' }}</h2>
                <p class="preview-hero-desc">{{ pageContent.description || '副标题说明' }}</p>
                <button class="preview-edit-btn" @click="scrollToField('heroTitle')">编辑</button>
              </div>
              <div class="preview-hero-image">
                <div v-if="pageContent.heroImage" class="preview-img-box" @click="scrollToField('heroImage')">
                  <img :src="pageContent.heroImage" alt="首屏大图" />
                  <div class="preview-img-overlay">更换图片</div>
                </div>
                <div v-else class="preview-img-placeholder" @click="scrollToField('heroImage')">
                  <PictureOutlined class="text-3xl text-gray-300" />
                  <span class="text-xs text-gray-400 mt-1">点击上传图片</span>
                </div>
              </div>
            </div>

            <!-- Content -->
            <div class="preview-body">
              <div v-if="activePage === 'home'" class="preview-section">
                <div v-if="pageContent.establishedYear" class="preview-eyebrow">Since {{ pageContent.establishedYear }}</div>
                <div v-if="(pageContent.trustBadges || []).length" class="preview-trust-row">
                  <span v-for="(b, i) in pageContent.trustBadges" :key="'b'+i" class="preview-trust-pill">{{ b }}</span>
                </div>
                <div v-if="(pageContent.stats || []).length" class="preview-stats-bar">
                  <div v-for="(s, i) in pageContent.stats" :key="'s'+i" class="preview-stat">
                    <div class="preview-stat-value">{{ s.value }}</div>
                    <div class="preview-stat-label">{{ s.label }}</div>
                  </div>
                </div>
                <div v-if="(pageContent.solutions || []).length" class="preview-section-title">Industry Solutions</div>
                <div v-if="(pageContent.solutions || []).length" class="preview-solution-grid">
                  <div v-for="(sol, i) in pageContent.solutions" :key="'sol'+i" class="preview-solution-card">
                    <div class="preview-solution-seg">{{ sol.segment }}</div>
                    <div class="preview-solution-title">{{ sol.title }}</div>
                  </div>
                </div>
                <div class="preview-section-title">Product Classification</div>
                <div class="preview-cat-grid">
                  <div v-for="(c, i) in pageContent.categories || []" :key="'c'+i" class="preview-cat-card">
                    <div class="preview-cat-name">{{ c.name || c }}</div>
                    <div v-if="c.description" class="preview-cat-desc">{{ c.description }}</div>
                  </div>
                </div>
                <div class="preview-section-title mt-4">{{ pageContent.sectionTitle || '为什么选择我们' }}</div>
                <div class="preview-adv-grid">
                  <div v-for="(a, i) in pageContent.advantages || []" :key="'a'+i" class="preview-adv-card">
                    <div class="preview-adv-title">{{ a.title || a }}</div>
                    <div v-if="a.description" class="preview-adv-desc">{{ a.description }}</div>
                  </div>
                </div>
              </div>
              <div v-if="activePage === 'products'" class="preview-section">
                <div class="preview-product-grid">
                  <div v-for="(item, i) in productPreviewItems" :key="i" class="preview-product-card">
                    <div class="preview-product-img">
                      <img v-if="item.image" :src="item.image" alt="" />
                    </div>
                    <div class="preview-product-name">{{ item.name }}</div>
                    <div v-if="item.summary" class="preview-product-summary">{{ item.summary }}</div>
                  </div>
                </div>
              </div>
              <div v-if="activePage === 'about'" class="preview-section">
                <p class="preview-about-text">{{ pageContent.aboutText || '关于我们，介绍公司背景、使命和价值观。' }}</p>
                <div v-if="pageContent.mission || pageContent.vision" class="preview-mv-grid">
                  <div v-if="pageContent.mission" class="preview-mv-card">
                    <div class="preview-mv-label">Mission</div>
                    <p>{{ pageContent.mission }}</p>
                  </div>
                  <div v-if="pageContent.vision" class="preview-mv-card">
                    <div class="preview-mv-label">Vision</div>
                    <p>{{ pageContent.vision }}</p>
                  </div>
                </div>
                <p v-if="pageContent.capacitySummary" class="preview-capacity">{{ pageContent.capacitySummary }}</p>
                <div v-if="(pageContent.milestones || []).length" class="preview-timeline">
                  <div v-for="(m, i) in pageContent.milestones" :key="i" class="preview-timeline-item">
                    <span class="preview-timeline-year">{{ m.year }}</span>
                    <strong>{{ m.title }}</strong>
                    <span v-if="m.description"> — {{ m.description }}</span>
                  </div>
                </div>
              </div>
              <div v-if="activePage === 'contact'" class="preview-section">
                <div class="preview-contact-info">
                  <div class="preview-contact-item" @click="scrollToField('phone')">
                    <PhoneOutlined /><span>{{ pageContent.phone || '联系电话' }}</span>
                  </div>
                  <div class="preview-contact-item" @click="scrollToField('email')">
                    <MailOutlined /><span>{{ pageContent.email || '联系邮箱' }}</span>
                  </div>
                  <div class="preview-contact-item" @click="scrollToField('address')">
                    <EnvironmentOutlined /><span>{{ pageContent.address || '公司地址' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div
              class="preview-footer preview-editable-zone"
              :style="{ background: previewData.theme?.footerBg || '#1e293b' }"
              @click="scrollToField('siteFooter')"
            >
              <div class="preview-footer-text">{{ footerDisplayText }}</div>
            </div>
          </div>
        </a-card>
      </div>

      <!-- Right: Editor -->
      <div class="editor-panel">
        <a-card title="页面编辑" :body-style="{ padding: '16px' }">
          <!-- 页眉页脚（全站） -->
          <div id="editor-field-siteHeader" class="editor-section">
            <div class="editor-section-title">页眉页脚</div>
            <p class="editor-section-hint">顶部导航栏和底部版权信息，全站各页面共用</p>
            <a-form layout="vertical" size="small">
              <a-form-item label="顶部公司名称">
                <a-input
                  v-model:value="previewData.brand.name"
                  placeholder="显示在网站顶部的公司或品牌名"
                />
              </a-form-item>
              <a-form-item label="顶部标语（选填）">
                <a-input
                  v-model:value="previewData.brand.tagline"
                  placeholder="如：专业建材出口 · 服务全球"
                />
              </a-form-item>
            </a-form>
          </div>
          <div id="editor-field-siteFooter" class="editor-section mt-2">
            <a-form layout="vertical" size="small">
              <a-form-item label="页脚版权文字">
                <a-textarea
                  v-model:value="previewData.footer.text"
                  :rows="2"
                  placeholder="留空则自动生成：© 年份 + 公司名称 + 保留所有权利"
                />
              </a-form-item>
            </a-form>
          </div>

          <a-divider class="my-3" />
          <!-- 搜索展示 -->
          <div class="editor-section">
            <div class="editor-section-title">搜索展示</div>
            <p class="editor-section-hint">客户在百度、Google 搜索时看到的内容</p>
            <a-form layout="vertical" size="small">
              <a-form-item label="网页标题" ref="pageTitle">
                <a-input v-model:value="pageContent.title" placeholder="如：某某建材 · 专业出口供应商" />
              </a-form-item>
              <a-form-item label="搜索简介" ref="seoDescription">
                <a-textarea v-model:value="pageContent.seoDescription" :rows="2" placeholder="一句话介绍公司或产品，会显示在搜索结果下方" />
              </a-form-item>
              <a-form-item label="搜索关键词">
                <a-input v-model:value="pageContent.seoKeywords" placeholder="客户可能搜的词，用逗号分隔，如：建材,出口,瓷砖" />
              </a-form-item>
            </a-form>
          </div>

          <!-- 首屏内容 -->
          <a-divider class="my-3" />
          <div id="editor-field-heroTitle" class="editor-section">
            <div class="editor-section-title">首屏内容</div>
            <p class="editor-section-hint">访客打开网站第一眼看到的大标题、说明和图片</p>
            <a-form layout="vertical" size="small">
              <a-form-item label="大标题" ref="heroTitle">
                <a-input v-model:value="pageContent.title" placeholder="如：专注建材外贸 20 年" />
              </a-form-item>
              <a-form-item label="副标题说明">
                <a-textarea v-model:value="pageContent.description" :rows="2" placeholder="补充一句口号或核心卖点" />
              </a-form-item>
              <a-form-item label="首屏展示图">
                <p class="editor-field-hint">通常由第一张产品图自动填充；也可手动更换</p>
                <div class="upload-trigger">
                  <div v-if="pageContent.heroImage" class="upload-preview" @click="triggerUpload">
                    <img :src="pageContent.heroImage" alt="preview" />
                    <div class="upload-preview-overlay"><SearchOutlined /> 点击更换</div>
                  </div>
                  <div v-else class="upload-placeholder" @click="triggerUpload">
                    <PlusOutlined />
                    <span>上传图片</span>
                  </div>
                </div>
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  style="display:none"
                  @change="handleImageUpload"
                />
              </a-form-item>
            </a-form>
          </div>

          <!-- Contact Fields (all pages) -->
          <a-divider class="my-3" />
          <div class="editor-section">
            <div class="editor-section-title">联系方式</div>
            <a-form layout="vertical" size="small">
              <a-form-item label="电话" ref="phone">
                <a-input v-model:value="pageContent.phone" placeholder="输入电话" />
              </a-form-item>
              <a-form-item label="邮箱" ref="email">
                <a-input v-model:value="pageContent.email" placeholder="输入邮箱" />
              </a-form-item>
              <template v-if="activePage === 'contact'">
                <a-form-item label="WhatsApp">
                  <a-input v-model:value="pageContent.whatsapp" placeholder="国际客户常用，如 0086-138xxxx" />
                </a-form-item>
                <a-form-item label="WeChat ID">
                  <a-input v-model:value="pageContent.wechat" placeholder="微信号，挂件一键复制" />
                </a-form-item>
                <a-form-item label="工厂地址">
                  <a-input v-model:value="pageContent.factoryAddress" placeholder="Factory address" />
                </a-form-item>
              </template>
              <a-form-item label="地址" ref="address">
                <a-input v-model:value="pageContent.address" placeholder="输入地址" />
              </a-form-item>
            </a-form>
          </div>

          <!-- Extra per-page -->
          <template v-if="activePage === 'home'">
            <a-divider class="my-3" />
            <div class="editor-section">
              <div class="editor-section-title">首页特殊内容</div>
              <a-form layout="vertical" size="small">
                <a-form-item label="特色区块标题">
                  <a-input v-model:value="pageContent.sectionTitle" placeholder="如：核心优势" />
                </a-form-item>
                <a-form-item label="特色列表">
                  <div v-for="(f, i) in pageContent.features" :key="i" class="feature-row">
                    <a-input v-model:value="pageContent.features[i]" placeholder="优势描述" />
                    <a-button type="text" size="small" danger @click="pageContent.features.splice(i, 1)">
                      <DeleteOutlined />
                    </a-button>
                  </div>
                  <a-button type="dashed" block size="small" @click="pageContent.features.push('')">
                    <PlusOutlined /> 添加优势
                  </a-button>
                </a-form-item>
              </a-form>
            </div>
          </template>

          <template v-if="activePage === 'about'">
            <a-divider class="my-3" />
            <div class="editor-section">
              <div class="editor-section-title">关于我们</div>
              <a-form layout="vertical" size="small">
                <a-form-item label="公司介绍">
                  <a-textarea v-model:value="pageContent.aboutText" :rows="5" placeholder="公司介绍文字" />
                </a-form-item>
              </a-form>
            </div>
          </template>

          <template v-if="activePage === 'products'">
            <a-divider class="my-3" />
            <div class="editor-section">
              <div class="editor-section-title">产品列表</div>
              <p class="editor-section-hint">名称与说明由 AI 生成；图片来自您上传的产品白底图</p>
              <a-form layout="vertical" size="small">
                <div v-for="(item, i) in productItemsEditable" :key="i" class="product-item-row">
                  <div v-if="item.image" class="product-item-thumb">
                    <img :src="item.image" alt="" />
                  </div>
                  <div class="product-item-fields">
                    <a-input v-model:value="item.name" placeholder="产品名称" />
                    <a-input v-model:value="item.summary" placeholder="一句规格说明" class="mt-1" />
                  </div>
                </div>
              </a-form>
            </div>
          </template>
        </a-card>
      </div>

      <SiteEditorRightPanel
        class="editor-side-panel"
        v-model:seo-model="seoFields"
        :site-content="siteContentForGate"
        :site-url="tenantSiteUrl"
        :initial-tab="rightPanelTab"
        @gap-apply="onGapApply"
      />
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Modal, message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import YdGrapesSiteEditor from '@/components/site-builder/YdGrapesSiteEditor.vue'
import SiteEditorRightPanel from '@/components/site-builder/SiteEditorRightPanel.vue'
import SiteEditorLProPublishBanner from '@/components/site-builder/SiteEditorLProPublishBanner.vue'
import SiteTemplatePickerModal from '@/components/site-builder/SiteTemplatePickerModal.vue'
import {
  DEFAULT_TEMPLATE_ID,
  getTemplateMeta,
  snapshotToSeo,
  applySeoToSnapshot,
  parseVisualHtmlToSnapshot,
  mergeParsedIntoSnapshot,
  buildVisualSiteBundle,
  syncHeroFromAssets,
  type SiteBuilderTemplateId,
  type SiteSeoFields,
  type VisualEditorPayload,
} from '@/templates/site-builder'
import {
  SaveOutlined, PictureOutlined, PlusOutlined, DeleteOutlined,
  SearchOutlined, CheckCircleOutlined, PhoneOutlined, MailOutlined,
  EnvironmentOutlined, ThunderboltOutlined, AppstoreOutlined, EyeOutlined,
} from '@ant-design/icons-vue'
import { buildTenantPreviewUrl } from '../../../../utils/tenant-preview-domain'
import { getAuthToken } from '@/utils/api'
import { runHermesSiteBuilder } from '@/utils/hermesSiteBuilder'
import {
  uploadSiteProductImages,
  productImageUrls,
  type UploadedProductImage,
} from '@/utils/siteProductImages'
import { productImageSpacePath } from '@/constants/productImageSpace'

const route = useRoute()
const router = useRouter()

const rightPanelTab = computed<'seo' | 'gap'>(() =>
  route.query.side === 'gap' ? 'gap' : 'seo',
)

function onGapApply(merged: Record<string, unknown>) {
  applySiteContent(merged)
  if (editorMode.value === 'visual') {
    visualEditorRef.value?.syncFromStructured()
  }
}

function goProductImageSpace() {
  router.push(productImageSpacePath(route.path.startsWith('/client')))
}
const loading = ref(true)
const tenantLoadHint = ref('')
const templatePickerOpen = ref(false)
const editorMode = ref<'visual' | 'form'>('visual')
const selectedTemplateId = ref<SiteBuilderTemplateId>(DEFAULT_TEMPLATE_ID)
const savedVisualPayload = ref<VisualEditorPayload | null>(null)
const visualEditorRef = ref<InstanceType<typeof YdGrapesSiteEditor> | null>(null)
const tenantSiteUrl = ref('')
const saving = ref(false)
const tenantPreviewUrl = computed(() => buildTenantPreviewUrl(tenantSiteUrl.value))
const seoFields = ref<SiteSeoFields>({
  pageTitle: '',
  seoDescription: '',
  seoKeywords: '',
  domesticPageTitle: '',
  domesticSeoDescription: '',
  domesticSeoKeywords: '',
  russianPageTitle: '',
  russianSeoDescription: '',
  russianSeoKeywords: '',
  allowIndex: true,
  seoPrimaryMarket: 'export',
})
const aiProductName = ref('')
const aiGenerating = ref(false)
const productImagesUploading = ref(false)
const productImages = ref<UploadedProductImage[]>([])
const productImagesInput = ref<HTMLInputElement>()
const lastDesignSkills = ref<string[]>([])
const lastEccExperts = ref<string[]>([])
const fileInput = ref<HTMLInputElement>()
const headers = { Authorization: `Bearer ${getAuthToken()}` }

// Pages
const pages = [
  { key: 'home', label: '首页' },
  { key: 'products', label: '产品' },
  { key: 'about', label: '关于' },
  { key: 'contact', label: '联系' },
]
const activePage = ref('home')

// Full preview data (brand + theme + all pages)
const previewData = reactive<Record<string, any>>({
  brand: { name: '公司名称', tagline: '' },
  footer: { text: '' },
  theme: { headerBg: '#1e293b', heroBg: '#f1f5f9', footerBg: '#1e293b' },
})

const footerDisplayText = computed(() => {
  const custom = String(previewData.footer?.text || '').trim()
  if (custom) return custom
  const name = previewData.brand?.name || '公司名称'
  return `© ${new Date().getFullYear()} ${name} 保留所有权利`
})

// Per-page content
const pageContents = reactive<Record<string, any>>({
  home: createDefaultPage('home'),
  products: createDefaultPage('products'),
  about: createDefaultPage('about'),
  contact: createDefaultPage('contact'),
})

function createDefaultPage(key: string) {
  const base = {
    title: '',
    description: '',
    seoDescription: '',
    seoKeywords: '',
    heroImage: '',
    phone: '',
    email: '',
    address: '',
  }
  if (key === 'home') return {
    ...base,
    sectionTitle: '为什么选择我们',
    features: ['品质可控', '定制生产', '安装便捷', '全球出口'],
    categories: [
      { name: '标准系列', description: '适用于常规工程项目' },
      { name: '加强系列', description: '更高性能指标' },
      { name: 'OEM/ODM', description: '按样品定制生产' },
    ],
    applications: [
      { title: 'Roof Insulation', description: '屋面保温系统' },
      { title: 'HVAC Insulation', description: '暖通风管设备' },
    ],
    applicationsTitle: 'What Are You Insulating?',
    solutions: [
      { segment: 'Building', title: '建筑工程', description: '墙体屋面外保温' },
      { segment: 'Industrial', title: '工业保温', description: '设备管道保温' },
      { segment: 'HVAC', title: '暖通系统', description: '风管与设备保温' },
      { segment: 'Marine', title: '船舶海工', description: '船用防火保温' },
    ],
    advantages: [
      { title: '品质可控', description: '源头工厂批次可追溯' },
      { title: '定制生产', description: '支持 OEM/ODM' },
      { title: '安装便捷', description: '标准规格缩短工期' },
      { title: '全球出口', description: '熟悉外贸单证' },
    ],
    establishedYear: '2005',
    trustBadges: ['15+ Years Experience', 'OEM/ODM', 'Factory Direct', 'Global Export'],
    stats: [
      { value: '50,000+', label: 'Tons Annual Capacity' },
      { value: '40+', label: 'Countries Served' },
      { value: '1,000+', label: 'Customers Worldwide' },
    ],
  }
  if (key === 'products') return {
    ...base,
    products: ['标准款', '加强款', '定制款'],
    productItems: [
      { name: '标准款', summary: '常规规格，适合批发' },
      { name: '加强款', summary: '更高性能，适合出口项目' },
      { name: '定制款', summary: 'OEM/ODM 贴牌' },
    ],
  }
  if (key === 'about') return {
    ...base,
    aboutText: '',
    mission: '',
    vision: '',
    capacitySummary: '',
    milestones: [],
  }
  if (key === 'contact') return {
    ...base,
    whatsapp: '',
    wechat: '',
    factoryAddress: '',
  }
  return base
}

// Derived current page content
const pageContent = computed({
  get: () => pageContents[activePage.value],
  set: (val) => { pageContents[activePage.value] = val },
})

const productPreviewItems = computed(() => {
  const items = pageContents.products?.productItems
  if (Array.isArray(items) && items.length) return items
  const names = pageContents.products?.products || []
  return names.map((n: string) => ({ name: n, summary: '', image: '' }))
})

const productItemsEditable = computed(() => {
  if (!Array.isArray(pageContents.products.productItems)) {
    pageContents.products.productItems = []
  }
  return pageContents.products.productItems
})

const siteSnapshot = computed(() =>
  syncHeroFromAssets({
    brand: { ...previewData.brand },
    footer: { ...previewData.footer },
    theme: { ...previewData.theme },
    assets: {
      productImages: productImages.value.map((i) => ({ url: i.url, name: i.name })),
    },
    pages: {
      home: { ...pageContents.home },
      products: { ...pageContents.products },
      about: { ...pageContents.about },
      contact: { ...pageContents.contact },
    },
  }),
)

/** L-Pro 发布门禁评估用（含模板 ID） */
const siteContentForGate = computed(() => ({
  ...siteSnapshot.value,
  templateId: selectedTemplateId.value,
  templateTier: selectedTemplateId.value === 'premium-b2b-v1' ? 'L-Pro' : undefined,
  visualEditor: {
    templateId: selectedTemplateId.value,
    html: savedVisualPayload.value?.html || '',
  },
}))

const currentTemplateMeta = computed(() => getTemplateMeta(selectedTemplateId.value))

function syncSeoFromPages() {
  seoFields.value = snapshotToSeo(siteSnapshot.value)
}

function applySeoFieldsToPages() {
  const updated = applySeoToSnapshot(siteSnapshot.value, seoFields.value)
  Object.assign(pageContents.home, updated.pages.home)
}

watch(seoFields, () => {
  applySeoFieldsToPages()
}, { deep: true })

function onTemplatePick(newId: SiteBuilderTemplateId) {
  if (newId === selectedTemplateId.value) return
  Modal.confirm({
    title: '切换建站模板',
    content: '将用新模板重建可视化页面（未保存的拖拽改动会丢失）。是否继续？',
    okText: '切换',
    cancelText: '取消',
    onOk: () => {
      selectedTemplateId.value = newId
      visualEditorRef.value?.applyTemplate(newId)
    },
  })
}

function openTenantPreview() {
  const url = tenantPreviewUrl.value
  if (!url) {
    message.warning('请先保存并绑定独立域名后再预览')
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

function applyStructuredFromVisual(html: string) {
  const parsed = parseVisualHtmlToSnapshot(html)
  const merged = mergeParsedIntoSnapshot(siteSnapshot.value, parsed)
  if (merged.brand) Object.assign(previewData.brand, merged.brand)
  if (merged.footer) Object.assign(previewData.footer, merged.footer)
  if (merged.pages?.home) Object.assign(pageContents.home, merged.pages.home)
  if (merged.pages?.contact) Object.assign(pageContents.contact, merged.pages.contact)
  syncSeoFromPages()
}

async function handleProductImagesPick(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  input.value = ''
  if (!files.length) return
  productImagesUploading.value = true
  try {
    const uploaded = await uploadSiteProductImages(files)
    productImages.value.push(...uploaded)
    syncHeroFromProductImages()
    message.success(`已上传 ${uploaded.length} 张产品图`)
  } catch (err: any) {
    message.error(err.message || '产品图上传失败')
  } finally {
    productImagesUploading.value = false
  }
}

function removeProductImage(index: number) {
  productImages.value.splice(index, 1)
  syncHeroFromProductImages()
}

function syncHeroFromProductImages() {
  const first = productImages.value[0]?.url
  if (first && !String(pageContents.home.heroImage || '').trim()) {
    pageContents.home.heroImage = first
  }
  if (!Array.isArray(pageContents.products.productItems)) {
    pageContents.products.productItems = []
  }
  productImages.value.forEach((img, i) => {
    const items = pageContents.products.productItems as Array<Record<string, unknown>>
    if (!items[i]) {
      items.push({ name: img.name || `Product ${i + 1}`, summary: '', image: img.url })
    } else if (!items[i].image) {
      items[i].image = img.url
    }
  })
}

function restoreProductImagesFromSite(siteContent: Record<string, any>) {
  const assets = siteContent.assets?.productImages
  if (Array.isArray(assets) && assets.length) {
    productImages.value = assets.map((a: any) => ({
      url: String(a.url || a),
      name: String(a.name || 'product'),
    }))
    return
  }
  const items = siteContent.pages?.products?.productItems
  if (Array.isArray(items)) {
    const fromItems = items
      .filter((it: any) => it?.image)
      .map((it: any, i: number) => ({ url: it.image, name: it.name || `product-${i}` }))
    if (fromItems.length) productImages.value = fromItems
  }
  syncHeroFromProductImages()
}

function switchPage(key: string) {
  activePage.value = key
}

// Scroll editor field into view
function scrollToField(fieldId: string) {
  const el = document.getElementById(`editor-field-${fieldId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('editor-field-flash')
    window.setTimeout(() => el.classList.remove('editor-field-flash'), 1200)
    return
  }
  document.querySelector('.editor-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Image upload (mock: convert to base64 / use placeholder)
function triggerUpload() {
  fileInput.value?.click()
}
function handleImageUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    pageContents[activePage.value].heroImage = reader.result as string
    message.success('图片已上传（仅本地预览）')
  }
  reader.readAsDataURL(file)
  input.value = '' // reset
}

// Load from API
async function loadSiteContent() {
  loading.value = true
  tenantLoadHint.value = ''
  try {
    const res = await fetch('/api/v1/tenants/current', { headers })
    const body = await res.json()
    if (!res.ok || (typeof body.code === 'number' && body.code !== 0)) {
      const msg = typeof body.message === 'string' ? body.message : '无法加载租户站点内容'
      tenantLoadHint.value =
        res.status === 403 || body.code === 403
          ? '当前为平台超管账号：请从「租户管理」进入具体租户，或使用租户账号在「租户工作台 → 可视化建站」编辑。'
          : msg
      return
    }
    const data = body.data || body
    const tenant = data.tenant || data
    const settings = tenant.settings || {}
    const siteContent = settings.brand?.site_content || {}

    // Restore brand/theme
    if (siteContent.brand) Object.assign(previewData.brand, siteContent.brand)
    if (siteContent.footer) Object.assign(previewData.footer, siteContent.footer)
    if (siteContent.theme) Object.assign(previewData.theme, siteContent.theme)

    // Restore page contents
    if (siteContent.pages) {
      for (const key of Object.keys(siteContent.pages)) {
        if (pageContents[key]) {
          Object.assign(pageContents[key], siteContent.pages[key])
        }
      }
    }
    restoreProductImagesFromSite(siteContent)
    syncHeroFromProductImages()
    syncSeoFromPages()
    if (tenant?.domain) tenantSiteUrl.value = tenant.domain
    else if (data.site_url) tenantSiteUrl.value = String(data.site_url).replace(/^https?:\/\//, '')
    const visual = siteContent.visualEditor as VisualEditorPayload | undefined
    if (siteContent.templateId) {
      selectedTemplateId.value = siteContent.templateId as SiteBuilderTemplateId
    } else if (visual?.templateId) {
      selectedTemplateId.value = visual.templateId
    }
    if (visual?.html || visual?.projectData) {
      savedVisualPayload.value = visual
    }
  } catch (e: any) {
    if (import.meta.env.DEV) console.warn('Failed to load site content, using defaults:', e.message)
  } finally {
    loading.value = false
  }
}

function applySiteContent(siteContent: Record<string, any>) {
  if (siteContent.brand) Object.assign(previewData.brand, siteContent.brand)
  if (siteContent.footer) Object.assign(previewData.footer, siteContent.footer)
  if (siteContent.theme) Object.assign(previewData.theme, siteContent.theme)
  if (siteContent.pages) {
    for (const key of Object.keys(siteContent.pages)) {
      if (pageContents[key]) {
        Object.assign(pageContents[key], siteContent.pages[key])
      }
    }
  }
  restoreProductImagesFromSite(siteContent)
  syncHeroFromProductImages()
  syncSeoFromPages()
}

async function runAiGenerate() {
  const name = aiProductName.value.trim()
  if (!name) {
    message.warning('请先输入您的主营产品名称')
    return
  }
  aiGenerating.value = true
  try {
    const result = await runHermesSiteBuilder({
      productName: name,
      autoSave: false,
      productImages: productImageUrls(productImages.value),
    })
    applySiteContent(result.siteContent)
    if (
      result.siteContent.templateId === 'premium-b2b-v1'
      || result.siteContent.templateTier === 'L-Pro'
    ) {
      selectedTemplateId.value = 'premium-b2b-v1'
    }
    lastDesignSkills.value = result.designSkillsApplied
    lastEccExperts.value = result.eccExpertsApplied || []
    activePage.value = 'home'
    editorMode.value = 'visual'
    visualEditorRef.value?.syncFromStructured()
    const gate = result.lProPublishGate
    if (gate?.publish_ready) {
      message.success('L-Pro 发布就绪：已满足对外上线门禁')
    } else if (gate?.p0) {
      message.info(`还差 ${gate.p0} 项才能对外发布，请补全产品图、规格与联系渠道`)
    } else {
      message.success(result.reply || '网站内容已生成，可在可视化模式微调后保存')
    }
  } catch (e: any) {
    message.error(e.message || '智能建站失败')
  } finally {
    aiGenerating.value = false
  }
}

// Save to API
async function saveContent() {
  saving.value = true
  try {
    const visualEditor =
      editorMode.value === 'visual' && visualEditorRef.value
        ? visualEditorRef.value.exportVisual()
        : savedVisualPayload.value

    if (visualEditor?.html) {
      applyStructuredFromVisual(visualEditor.html)
    }
    applySeoFieldsToPages()

    const payload: Record<string, unknown> = {
      brand: { ...previewData.brand },
      footer: { ...previewData.footer },
      theme: { ...previewData.theme },
      assets: {
        productImages: productImages.value.map((i) => ({ url: i.url, name: i.name })),
      },
      pages: {
        home: { ...pageContents.home },
        products: { ...pageContents.products },
        about: { ...pageContents.about },
        contact: { ...pageContents.contact },
      },
    }
    if (selectedTemplateId.value === 'premium-b2b-v1') {
      payload.templateId = 'premium-b2b-v1'
      payload.templateTier = 'L-Pro'
    }
    if (visualEditor?.html) {
      const bundle = buildVisualSiteBundle(selectedTemplateId.value, siteSnapshot.value)
      payload.visualEditor = {
        ...visualEditor,
        css: visualEditor.css || bundle.css,
        templateId: selectedTemplateId.value,
        multiPage: true,
        subPages: bundle.subPages,
      }
      savedVisualPayload.value = payload.visualEditor as VisualEditorPayload
    }
    const res = await fetch('/api/v1/tenants/self', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({
        settings: JSON.stringify({
          brand: {
            site_content: payload,
          },
        }),
      }),
    })
    if (res.ok) {
      message.success('网站内容已保存')
    } else {
      const d = await res.json()
      message.error(d.message || '保存失败')
    }
  } catch (e: any) {
    message.error('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => loadSiteContent())
</script>

<style scoped>
.site-editor-space {
  width: 100%;
  max-width: none;
  margin: 0;
}

.site-editor-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.site-editor-header-tools {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.site-editor-template-btn {
  max-width: 220px;
}

.site-editor-template-desc {
  margin: 0;
  font-size: 12px;
  color: #64748b;
}

.site-editor-visual-row {
  display: grid;
  grid-template-columns: 1fr minmax(300px, 360px);
  gap: 14px;
  align-items: start;
}

.site-editor-visual-main {
  min-width: 0;
}

@media (max-width: 1100px) {
  .site-editor-visual-row {
    grid-template-columns: 1fr;
  }
}

.site-editor-ai-block {
  flex: 1 1 auto;
  min-width: 0;
}

.site-editor-ai-subhint {
  margin: 6px 0 0;
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.5;
}

.site-editor-product-images {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.site-editor-product-thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.site-editor-product-thumb {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #fff;
}

.site-editor-product-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.site-editor-product-remove {
  position: absolute;
  top: 0;
  right: 0;
  width: 18px;
  height: 18px;
  border: none;
  background: rgb(15 23 42 / 0.65);
  color: #fff;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.editor-field-hint,
.editor-section-hint {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: -4px 0 8px;
}

.product-item-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.product-item-thumb {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  background: #f8fafc;
}

.product-item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.product-item-fields {
  flex: 1;
  min-width: 0;
}

.preview-product-img img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.site-editor-ai-row {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.site-editor-ai-label {
  flex: 0 0 auto;
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 32px;
  color: #0f172a;
  white-space: nowrap;
}

.site-editor-ai-input {
  flex: 1 1 240px;
  min-width: 160px;
}

.site-editor-ai-hint {
  margin: -8px 0 0;
  font-size: 0.75rem;
  color: #64748b;
}

@media (max-width: 960px) {
  .site-editor-header {
    flex-wrap: wrap;
  }
  .site-editor-ai-row {
    flex: 1 1 100%;
    flex-wrap: wrap;
  }
  .site-editor-ai-label {
    flex: 1 1 100%;
    line-height: 1.4;
  }
}

/* Page Tabs */
.page-tabs {
  display: flex;
  gap: 0;
  overflow-x: auto;
}
.page-tab {
  padding: 10px 24px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  font-family: inherit;
}
.page-tab:hover {
  color: var(--uj-brand, #4a9b8c);
  background: #f8fafc;
}
.page-tab.active {
  color: var(--uj-brand, #4a9b8c);
  font-weight: 600;
}
.page-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 2px;
  background: var(--uj-brand, #4a9b8c);
  border-radius: 2px 2px 0 0;
}

/* Layout */
.editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 380px) minmax(280px, 340px);
  gap: 20px;
  align-items: start;
  min-height: calc(100vh - 220px);
}
@media (min-width: 1280px) {
  .editor-layout {
    grid-template-columns: minmax(640px, 1fr) 380px 340px;
  }
}
@media (max-width: 1200px) {
  .editor-layout {
    grid-template-columns: minmax(0, 1fr) minmax(300px, 380px);
  }
  .editor-side-panel {
    grid-column: 1 / -1;
  }
}
@media (max-width: 1024px) {
  .editor-layout { grid-template-columns: 1fr; min-height: auto; }
}

/* Preview Panel */
.preview-panel {
  min-width: 0;
}
.preview-panel :deep(.ant-card) {
  height: 100%;
}
.preview-panel :deep(.ant-card-body) {
  padding: 12px !important;
}
.preview-frame {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  font-size: 15px;
  min-height: 620px;
  width: 100%;
}

/* Preview Header */
.preview-header {
  padding: 16px 28px;
  cursor: pointer;
}
.preview-editable-zone:hover {
  outline: 2px solid rgba(59, 130, 246, 0.35);
  outline-offset: -2px;
}
.preview-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.preview-brand {
  min-width: 0;
}
.preview-tagline {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.72);
  margin-top: 4px;
}
.preview-logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
}
.preview-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
.preview-nav-item {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  transition: color 0.2s;
}
.preview-nav-item:hover,
.preview-nav-item.active {
  color: white;
}

/* Preview Hero */
.preview-hero {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 40px 32px;
  min-height: 220px;
}
.preview-hero-content {
  flex: 1;
  min-width: 0;
}
.preview-hero-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 12px;
  line-height: 1.25;
}
.preview-hero-desc {
  font-size: 1rem;
  color: #64748b;
  margin: 0 0 16px;
  line-height: 1.5;
}
.preview-edit-btn {
  padding: 4px 12px;
  font-size: 0.75rem;
  border: 1px solid var(--uj-brand, #4a9b8c);
  background: white;
  color: var(--uj-brand, #4a9b8c);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.preview-edit-btn:hover {
  background: var(--uj-brand, #4a9b8c);
  color: white;
}
.preview-hero-image {
  flex-shrink: 0;
  width: min(360px, 42%);
  height: 220px;
}
.preview-img-box {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
}
.preview-img-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-img-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s;
}
.preview-img-box:hover .preview-img-overlay {
  opacity: 1;
}
.preview-img-placeholder {
  width: 100%;
  height: 100%;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  cursor: pointer;
  transition: border-color 0.2s;
}
.preview-img-placeholder:hover {
  border-color: var(--uj-brand, #4a9b8c);
}

/* Preview Body */
.preview-body {
  padding: 32px;
  min-height: 180px;
}
.preview-section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}
.preview-features {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.preview-feature {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.preview-feature:hover {
  background: #eef2ff;
}
.preview-feature-icon {
  color: #22c55e;
  font-size: 1rem;
}
.preview-feature-text {
  font-size: 0.8rem;
  color: #334155;
}

/* Products grid in preview */
.preview-product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.preview-product-card {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  text-align: center;
}
.preview-product-img {
  width: 100%;
  height: 80px;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 8px;
}
.preview-product-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #334155;
}
.preview-product-summary {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 4px;
  line-height: 1.4;
}

/* B2B classification & advantages */
.preview-cat-grid,
.preview-adv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}
.preview-cat-card,
.preview-adv-card {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.preview-cat-name,
.preview-adv-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}
.preview-cat-desc,
.preview-adv-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.4;
}
.mt-4 { margin-top: 16px; }

.preview-eyebrow {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #1e3a5f;
  margin-bottom: 8px;
}

.preview-solution-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}
.preview-solution-card {
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-top: 2px solid #1e3a5f;
  border-radius: 6px;
  background: #fff;
}
.preview-solution-seg {
  font-size: 0.55rem;
  font-weight: 700;
  color: #1e3a5f;
  text-transform: uppercase;
}
.preview-solution-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: #334155;
}
.preview-trust-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.preview-trust-pill {
  font-size: 0.65rem;
  padding: 3px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
}
.preview-stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 12px;
  background: #1e3a5f;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #fff;
  text-align: center;
}
.preview-stat-value {
  font-size: 0.9rem;
  font-weight: 800;
}
.preview-stat-label {
  font-size: 0.55rem;
  opacity: 0.85;
  margin-top: 2px;
}
.preview-mv-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 12px 0;
}
.preview-mv-card {
  padding: 10px;
  background: #f8fafc;
  border-left: 3px solid #1e3a5f;
  font-size: 0.75rem;
  color: #475569;
  line-height: 1.5;
}
.preview-mv-label {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #1e3a5f;
  margin-bottom: 4px;
}
.preview-capacity {
  font-size: 0.75rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 12px;
}
.preview-timeline {
  font-size: 0.75rem;
  color: #475569;
  border-left: 2px solid #e2e8f0;
  padding-left: 10px;
}
.preview-timeline-item {
  margin-bottom: 8px;
}
.preview-timeline-year {
  font-weight: 800;
  color: #1e3a5f;
  margin-right: 6px;
}

/* About */
.preview-about-text {
  font-size: 0.85rem;
  line-height: 1.6;
  color: #475569;
}

/* Contact */
.preview-contact-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.preview-contact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #475569;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.preview-contact-item:hover {
  background: #f1f5f9;
}

/* Footer */
.preview-footer {
  padding: 20px 28px;
  text-align: center;
  cursor: pointer;
}
.preview-footer-text {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.75);
  line-height: 1.5;
}

/* Editor Panel */
.editor-panel {
  min-width: 0;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}
.editor-panel :deep(.ant-card) {
  position: sticky;
  top: 72px;
}
.editor-field-flash {
  animation: editor-flash 1.2s ease;
}
@keyframes editor-flash {
  0%, 100% { background: transparent; }
  30% { background: #eff6ff; border-radius: 8px; }
}
.editor-section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}
.editor-section-hint {
  font-size: 0.72rem;
  color: #94a3b8;
  margin: 0 0 10px;
  line-height: 1.4;
}
.editor-section {
  margin-bottom: 4px;
}
.editor-section :deep(.ant-form-item) {
  margin-bottom: 10px;
}

/* Upload triggers */
.upload-trigger {
  width: 100%;
}
.upload-preview {
  position: relative;
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
}
.upload-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.upload-preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  font-size: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s;
}
.upload-preview:hover .upload-preview-overlay {
  opacity: 1;
}
.upload-placeholder {
  width: 100%;
  height: 90px;
  border: 2px dashed #d1d5db;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}
.upload-placeholder:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: var(--uj-brand, #4a9b8c);
}

/* Feature row */
.feature-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
}
.feature-row :deep(.ant-input) {
  flex: 1;
}
</style>
