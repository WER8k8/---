/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="ge-app">
    <YdHonestDataBanner
      level="partial"
      title="GEO 监测 ≠ 真实搜索排名"
      description="本页测的是「大模型 API 是否提到品牌」，不是 ChatGPT 网页搜索榜。最终效果以询盘电话与独立域收录为准。"
      :banner="false"
      :closable="true"
    />
    <!-- Hero -->
    <div class="ge-hero">
      <h1>GEO引擎 · AI品牌可见性监测</h1>
      <p>
        探测品牌/关键词在各大 AI 中的<strong class="text-slate-300">提及情况</strong>（监测用）。
        GEO 优化本身靠内容与品牌布局，与填 Key 不是一回事。
      </p>
      <div class="ge-hero-bar">
        <a-input-search v-model:value="keyword" placeholder="输入品牌/关键词" enter-button="查询收录" size="large" @search="checkAll" :loading="loading" style="max-width:400px"/>
        <a-button size="large" @click="checkAll">全量检查</a-button>
        <a-button size="large" @click="runCompetitor">竞品对比</a-button>
      </div>
      <!-- Quick links -->
      <div class="ge-links">
        <span class="text-xs text-gray-400">直达搜索:</span>
        <a v-for="l in quickLinks" :key="l.name" :href="l.url" target="_blank" class="ge-link-btn">{{ l.name }}</a>
      </div>
      <a-alert
        v-if="unconfiguredCount > 0"
        type="warning"
        show-icon
        class="mt-3"
        message="部分监测通道未接通"
        :description="`共 ${unconfiguredCount} 个模型因未配置 API Key 而无法探测（只影响能不能测，不代表 GEO 没做）。接通后可在 AI配置 填写 Key；DeepSeek / NVIDIA 等有免费额度可先试。`"
      >
        <template #action>
          <a-button size="small" type="primary" @click="goAiConfig()">接通监测通道</a-button>
        </template>
      </a-alert>
    </div>

    <!-- unified-geo-v1 租户口径 -->
    <a-card size="small" title="统一 GEO 分 · unified-geo-v1" class="ge-unified-card">
      <div class="flex flex-wrap gap-3 items-end mb-3">
        <div>
          <div class="text-xs text-gray-500 mb-1">租户域名</div>
          <a-input v-model:value="tenantDomain" placeholder="dev.local" style="width:200px" />
        </div>
        <a-button type="primary" :loading="unifiedLoading" @click="() => loadUnifiedGeo()">刷新统一分</a-button>
        <a-button :loading="unifiedLoading" @click="() => loadUnifiedGeo(true)">含 AI 探针</a-button>
      </div>
      <div v-if="unifiedGeo?.ok" class="flex flex-wrap gap-4 items-center">
        <div class="text-center px-4">
          <div class="text-4xl font-bold text-indigo-600">{{ unifiedGeo.overall ?? '—' }}</div>
          <div class="text-xs text-gray-400">{{ unifiedGeo.schema_version }}</div>
        </div>
        <div class="flex flex-wrap gap-2">
          <a-tag v-for="(c, k) in unifiedGeo.components" :key="k">
            {{ k }}: {{ c.score ?? '—' }}
          </a-tag>
        </div>
      </div>
      <p v-else-if="unifiedGeo?.error_code" class="text-sm text-gray-500">{{ unifiedGeo.error_code }}</p>
      <p class="text-xs text-gray-400 mt-2 mb-0">
        口径合并 AEO / Optimizer / Engine / AI Search；未配置 Key 的探针 honest not_configured。
      </p>
    </a-card>

    <!-- GEO Score + Model Cards -->
    <a-row :gutter="16" v-if="result">
      <a-col :span="6">
        <a-card size="small" class="ge-score-card" :class="'grade-'+geoScore?.grade">
          <div class="text-center">
            <div class="text-5xl font-bold mb-1" :style="{color: scoreColor}">{{ geoScore?.total_score || '—' }}</div>
            <a-tag :color="scoreColor">{{ geoScore?.grade }}级</a-tag>
            <div class="text-xs text-gray-400 mt-2">监测综合分</div>
            <div class="text-[10px] text-gray-400 mt-1 leading-snug">{{ geoScore?.score_note || '反映各 AI 是否提及品牌，非 GEO 优化完成度' }}</div>
          </div>
          <div class="mt-3 space-y-1 text-xs">
            <div v-for="d in geoScore?.dimensions" :key="d.label"><div class="flex justify-between"><span class="text-gray-500">{{ d.label }}</span><span>{{ d.score }}/{{ d.max }}</span></div><a-progress :percent="d.score/d.max*100" size="small" :show-info="false"/></div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="18">
        <div class="ge-model-grid">
          <div v-for="m in result.models" :key="m.id" class="ge-mcard" :style="{borderTopColor: m.color}">
            <div class="flex items-center gap-2 mb-2">
              <span class="font-bold text-sm">{{ m.name }}</span>
              <a-tag
                v-if="m.status === 'not_configured'"
                color="default"
                size="small"
                class="ge-config-tag"
                @click="goAiConfig(m.id)"
              >监测未接通</a-tag>
              <a-tag v-else :color="stColor(m.status)" size="small">{{ stLabel(m.status) }}</a-tag>
            </div>
            <a-progress :percent="m.confidence*100" :stroke-color="m.color" size="small"/>
            <div class="text-xs text-gray-500 mt-1">{{ m.response?.slice(0,80) }}</div>
            <div class="flex gap-2 mt-1">
              <a v-if="m.status !== 'not_configured'" :href="linkForModel(m.id)" target="_blank" class="text-xs text-blue-500">直达搜索</a>
              <a v-else class="text-xs text-blue-500 cursor-pointer" @click.prevent="goAiConfig(m.id)">接通此通道</a>
            </div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- Trend + Competitor -->
    <a-row :gutter="16" v-if="result">
      <a-col :span="12">
        <a-card title="提及率趋势" size="small">
          <a-empty v-if="!trend.length" description="暂无历史探测记录。多次 GEO 探测后才会出现真实趋势。" />
          <template v-else>
          <div class="h-32 flex items-end gap-0.5">
            <div v-for="(d,i) in trend" :key="i" class="flex-1 bg-blue-500 rounded-t hover:bg-blue-600 relative group" :style="{height:(d.rate||2)+'%'}">
              <div class="absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] text-gray-400 opacity-0 group-hover:opacity-100 whitespace-nowrap">{{ d.rate }}%</div>
            </div>
          </div>
          </template>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="竞品对比" size="small">
          <a-input v-model:value="competitors" placeholder="竞品关键词,逗号分隔" class="mb-3" @pressEnter="runCompetitor"/>
          <div v-if="compResults.length" class="space-y-2">
            <div v-for="c in compResults" :key="c.keyword" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
              <span class="font-medium flex-1 text-sm">{{ c.keyword }}</span>
              <a-progress :percent="c.score" size="small" :style="{width:'80px'}"/>
              <span class="text-xs">{{ c.indexed }}/{{ c.total }}</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Optimization Suggestions -->
    <a-alert v-if="filteredSuggestions.length" type="info" show-icon class="ge-alert">
      <template #message>建议（监测 vs GEO 优化）</template>
      <template #description>
        <ul class="list-disc pl-4 space-y-1">
          <li v-for="s in filteredSuggestions" :key="s">{{ s }}</li>
        </ul>
      </template>
    </a-alert>

    <a-card size="small" title="GEO 优化方向（与 API Key 无关）" class="ge-strategy-card">
      <ul class="text-xs text-gray-600 space-y-1.5 list-disc pl-4 m-0">
        <li>完善官网产品页：参数、应用案例、资质证书，便于 AI 引用</li>
        <li>在行业媒体、百科、B2B 平台增加品牌与产品描述</li>
        <li>结构化数据（Schema）与多语言页面，提升可被检索与摘要的质量</li>
        <li>持续发布技术文章、工程案例，形成可被大模型学习的公开信源</li>
      </ul>
    </a-card>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { getAuthToken } from '@/utils/api'
import { YdHonestDataBanner } from '@/components/youding'
const router = useRouter()
const keyword=ref('优丁建材 轻集料混凝土'); const loading=ref(false); const competitors=ref(''); const compResults=ref<any[]>([]);
const result=ref<any>(null); const geoScore=ref<any>(null); const trend=ref<any[]>([]); const quickLinks=ref<any[]>([])
const tenantDomain=ref('dev.local'); const unifiedLoading=ref(false); const unifiedGeo=ref<any>(null)

const modelLinks:Record<string,string>={deepseek:'https://chat.deepseek.com/',openai:'https://chat.openai.com/',nvidia:'https://build.nvidia.com/explore/discover',gemini:'https://gemini.google.com/',anthropic:'https://claude.ai/'}
const aiConfigProvider:Record<string,string>={deepseek:'deepseek',openai:'openai',nvidia:'nvidia',gemini:'gemini',anthropic:'anthropic'}

function goAiConfig(modelId?: string) {
  const q: Record<string, string> = { from: 'geo-engine' }
  if (modelId && aiConfigProvider[modelId]) q.provider = aiConfigProvider[modelId]
  router.push({ path: '/ai-config', query: q })
}

const unconfiguredCount = computed(() =>
  (result.value?.models || []).filter((m: any) => m.status === 'not_configured').length
)

function stColor(s:string){return {indexed:'green',partial:'orange',not_indexed:'red',not_configured:'default',error:'red'}[s]||'default'}
function stLabel(s:string){return {indexed:'已提及',partial:'部分提及',not_indexed:'未提及',not_configured:'监测未接通',error:'探测错误'}[s]||s}
function linkForModel(id:string){return modelLinks[id]||'#'}
const scoreColor=computed(()=>{const g=geoScore.value?.grade;return {A:'#22c55e',B:'#3b82f6',C:'#f59e0b',D:'#ef4444'}[g as string]||'#94a3b8'})
const filteredSuggestions = computed(() => (geoScore.value?.suggestions || []).filter(Boolean))

async function api(p:string,m='GET',b?:any){const h:any={Authorization:`Bearer ${getAuthToken()}`};if(b)h['Content-Type']='application/json';const r=await fetch(`/api/v1/super-admin${p}`,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok)throw new Error(`HTTP ${r.status}`);const d=await r.json();return d.data||d}

async function checkAll(){if(!keyword.value.trim())return;loading.value=true;try{const[kw]=await Promise.all([api(`/geo-engine/quick-check?keyword=${encodeURIComponent(keyword.value)}`),api(`/geo-engine/score?keyword=${encodeURIComponent(keyword.value)}`,'POST'),api(`/geo-engine/trend?keyword=${encodeURIComponent(keyword.value)}&days=30`)]);result.value=kw;const[s,t]=await Promise.all([api(`/geo-engine/score?keyword=${encodeURIComponent(keyword.value)}`,'POST'),api(`/geo-engine/trend?keyword=${encodeURIComponent(keyword.value)}&days=30`)]);geoScore.value=s;trend.value=t}catch(e:any){message.error(e.message)}loading.value=false}

async function runCompetitor(){const kws=competitors.value||keyword.value;const list=kws.split(/[,，]/).filter((k:string)=>k.trim());if(!list.length)return;loading.value=true;try{const q=list.map((k:string)=>`keywords=${encodeURIComponent(k.trim())}`).join('&');compResults.value=await api(`/geo-engine/competitor?${q}`,'POST')}catch(e:any){message.error(e.message)}loading.value=false}

async function loadUnifiedGeo(withProbes=false){
  const d=tenantDomain.value.trim(); if(!d)return
  unifiedLoading.value=true
  try{
    const r=await fetch(`/api/v1/public/tenants/${encodeURIComponent(d)}/geo-score?include_probes=${withProbes?'true':'false'}`,{headers:{Authorization:`Bearer ${getAuthToken()}`}})
    if(!r.ok) throw new Error(`HTTP ${r.status}`)
    const body=await r.json(); unifiedGeo.value=body.data||body
  }catch(e:any){message.error(e.message); unifiedGeo.value=null}
  unifiedLoading.value=false
}

onMounted(async()=>{try{quickLinks.value=await api('/geo-engine/quick-links');checkAll();loadUnifiedGeo()}catch{quickLinks.value=[{name:'DeepSeek',url:'https://chat.deepseek.com/'},{name:'豆包',url:'https://www.doubao.com/chat/search'},{name:'元宝',url:'https://yuanbao.tencent.com/chat/naQivTmsDa'},{name:'通义千问',url:'https://www.tongyi.com/'},{name:'文心一言',url:'https://yiyan.baidu.com/'},{name:'Kimi',url:'https://kimi.moonshot.cn/'}];loadUnifiedGeo()}})
</script>
<style scoped>
.ge-app{display:flex;flex-direction:column;gap:1rem}
.ge-hero{background:linear-gradient(135deg,#0f172a,#1e293b,#1e3a5f);border-radius:18px;padding:1.5rem 2rem;color:white}
.ge-hero h1{font-size:1.35rem;font-weight:700;margin-bottom:.25rem}
.ge-hero p{font-size:.78rem;color:#94a3b8;margin-bottom:1rem}
.ge-hero-bar{display:flex;gap:.75rem}
.ge-links{margin-top:.75rem;display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}
.ge-link-btn{font-size:.7rem;padding:.2rem .6rem;border-radius:6px;background:rgba(255,255,255,.08);color:#94a3b8;text-decoration:none;transition:all .15s}
.ge-link-btn:hover{background:rgba(255,255,255,.15);color:white}
.ge-score-card{border-radius:14px;border-width:2px}
.ge-score-card.grade-A{border-color:#22c55e}
.ge-score-card.grade-B{border-color:#3b82f6}
.ge-score-card.grade-C{border-color:#f59e0b}
.ge-score-card.grade-D{border-color:#ef4444}
.ge-model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.5rem}
.ge-mcard{background:white;border-radius:12px;padding:.75rem;border:1px solid #f1f5f9;border-top:3px solid #3b82f6;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.ge-config-tag{cursor:pointer}
.ge-config-tag:hover{opacity:.85;box-shadow:0 0 0 1px #94a3b8}
.ge-alert{border-radius:12px}
.ge-strategy-card{border-radius:12px;border:1px dashed #e2e8f0}
.ge-unified-card{border-radius:12px;border:1px solid #e0e7ff}
.ge-hero strong{font-weight:600}
@media (max-width:768px){.ge-hero-bar{flex-direction:column}.ge-model-grid{grid-template-columns:1fr}.ge-stats{grid-template-columns:repeat(2,1fr)}.ge-search{max-width:100%}}
@media (max-width:480px){.ge-hero h1{font-size:1.1rem}.ge-hero{padding:1rem 1.25rem}}
</style>
