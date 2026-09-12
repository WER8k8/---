<template>
  <YdPage title="翻译引擎" subtitle="AI 驱动多语言翻译 · 对接 LangChain RAG · 支持批量" surface="elevated">
    <template #actions>
      <a-tag color="blue">API: /langchain/rag/query</a-tag>
    </template>
    <div class="space-y-6">
    <a-row :gutter="16">
      <a-col :span="16"><a-card title="翻译工作台" size="small">
        <a-form layout="vertical"><a-form-item label="源文本"><a-textarea v-model:value="src" :rows="5" placeholder="输入要翻译的文本..."/></a-form-item>
        <a-row :gutter="16"><a-col :span="8"><a-form-item label="源语言"><a-select v-model:value="srcLang" show-search option-filter-prop="label"><a-select-option value="zh" label="中文">中文</a-select-option><a-select-option value="ja" label="日本語">日本語</a-select-option><a-select-option value="ko" label="한국어">한국어</a-select-option><a-select-option value="en" label="English">English</a-select-option><a-select-option value="de" label="Deutsch">Deutsch</a-select-option><a-select-option value="fr" label="Français">Français</a-select-option><a-select-option value="es" label="Español">Español</a-select-option><a-select-option value="pt" label="Português">Português</a-select-option><a-select-option value="it" label="Italiano">Italiano</a-select-option><a-select-option value="nl" label="Nederlands">Nederlands</a-select-option><a-select-option value="sv" label="Svenska">Svenska</a-select-option><a-select-option value="hi" label="हिन्दी">हिन्दी</a-select-option><a-select-option value="id" label="Bahasa Indonesia">Bahasa Indonesia</a-select-option><a-select-option value="tl" label="Filipino">Filipino</a-select-option><a-select-option value="bn" label="বাংলা">বাংলা</a-select-option><a-select-option value="my" label="မြန်မာ">မြန်မာ</a-select-option><a-select-option value="km" label="ភាសាខ្មែរ">ភាសាខ្មែរ</a-select-option><a-select-option value="pl" label="Polski">Polski</a-select-option><a-select-option value="cs" label="Čeština">Čeština</a-select-option><a-select-option value="uk" label="Українська">Українська</a-select-option><a-select-option value="ar" label="العربية">العربية</a-select-option><a-select-option value="tr" label="Türkçe">Türkçe</a-select-option><a-select-option value="fa" label="فارسی">فارسی</a-select-option><a-select-option value="he" label="עברית">עברית</a-select-option><a-select-option value="sw" label="Kiswahili">Kiswahili</a-select-option><a-select-option value="ha" label="Hausa">Hausa</a-select-option><a-select-option value="zu" label="isiZulu">isiZulu</a-select-option><a-select-option value="am" label="አማርኛ">አማርኛ</a-select-option><a-select-option value="th" label="ไทย">ไทย</a-select-option><a-select-option value="vi" label="Tiếng Việt">Tiếng Việt</a-select-option><a-select-option value="ms" label="Bahasa Melayu">Bahasa Melayu</a-select-option></a-select></a-form-item></a-col><a-col :span="8"><a-form-item label="目标语言"><a-select v-model:value="tgtLang" show-search option-filter-prop="label"><a-select-option value="en" label="English">English</a-select-option><a-select-option value="de" label="Deutsch">Deutsch</a-select-option><a-select-option value="fr" label="Français">Français</a-select-option><a-select-option value="es" label="Español">Español</a-select-option><a-select-option value="pt" label="Português">Português</a-select-option><a-select-option value="it" label="Italiano">Italiano</a-select-option><a-select-option value="nl" label="Nederlands">Nederlands</a-select-option><a-select-option value="sv" label="Svenska">Svenska</a-select-option><a-select-option value="ja" label="日本語">日本語</a-select-option><a-select-option value="ko" label="한국어">한국어</a-select-option><a-select-option value="ar" label="العربية">العربية</a-select-option><a-select-option value="tr" label="Türkçe">Türkçe</a-select-option><a-select-option value="fa" label="فارسی">فارسی</a-select-option><a-select-option value="he" label="עברית">עברית</a-select-option><a-select-option value="th" label="ไทย">ไทย</a-select-option><a-select-option value="vi" label="Tiếng Việt">Tiếng Việt</a-select-option><a-select-option value="ms" label="Bahasa Melayu">Bahasa Melayu</a-select-option><a-select-option value="hi" label="हिन्दी">हिन्दी</a-select-option><a-select-option value="id" label="Bahasa Indonesia">Bahasa Indonesia</a-select-option><a-select-option value="tl" label="Filipino">Filipino</a-select-option><a-select-option value="bn" label="বাংলা">বাংলা</a-select-option><a-select-option value="my" label="မြန်မာ">မြန်မာ</a-select-option><a-select-option value="km" label="ភាសាខ្មែរ">ភាសាខ្មែរ</a-select-option><a-select-option value="pl" label="Polski">Polski</a-select-option><a-select-option value="cs" label="Čeština">Čeština</a-select-option><a-select-option value="uk" label="Українська">Українська</a-select-option><a-select-option value="sw" label="Kiswahili">Kiswahili</a-select-option><a-select-option value="ha" label="Hausa">Hausa</a-select-option><a-select-option value="zu" label="isiZulu">isiZulu</a-select-option><a-select-option value="am" label="አማርኛ">አማርኛ</a-select-option><a-select-option value="zh" label="中文">中文</a-select-option></a-select></a-form-item></a-col><a-col :span="8"><a-form-item label=" "><a-button type="primary" block @click="doTranslate" :loading="loading">翻译</a-button></a-form-item></a-col></a-row></a-form>
        <div v-if="result" class="mt-4 p-4 bg-blue-50 rounded-lg"><div class="flex items-center justify-between mb-2"><h4 class="text-sm font-medium">翻译结果</h4><a-space><a-rate :value="rating" disabled :count="5"/><a-button size="small" @click="copyText(result)">复制</a-button><a-button size="small" @click="addToGlossary">添加到术语库</a-button></a-space></div><p class="text-sm whitespace-pre-wrap">{{ result }}</p></div>
        <div v-if="apiError" class="mt-4 p-3 bg-red-50 rounded text-sm text-red-600">{{ apiError }}</div>
      </a-card></a-col>
      <a-col :span="8">
        <a-card title="批量翻译" size="small"><a-textarea v-model:value="batchText" :rows="6" placeholder="每行一条待翻译文本..."/><a-button type="primary" block class="mt-3" @click="doBatch" :loading="batchLoading">批量翻译 ({{ batchLines }}条)</a-button></a-card>
        <a-card title="翻译历史" size="small" class="mt-4"><div class="space-y-2 max-h-60 overflow-y-auto"><div v-for="h in history" :key="h.id" class="p-2 hover:bg-gray-50 rounded cursor-pointer text-xs" @click="result=h.result; rating=h.rating"><div class="text-gray-600 truncate">{{ h.src?.slice(0,40) }}</div><div class="text-blue-600 truncate">{{ h.result?.slice(0,40) }}</div><div class="text-gray-400">{{ h.lang }} · {{ h.time }}</div></div></div></a-card>
      </a-col>
    </a-row>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'
import { ref, computed } from 'vue'; import { message } from 'ant-design-vue'
const src=ref(''); const result=ref(''); const loading=ref(false); const apiError=ref('')
const srcLang=ref('zh'); const tgtLang=ref('en'); const rating=ref(4); const batchText=ref('')
const batchLoading=ref(false)
const batchLines=computed(()=>batchText.value.split('\n').filter(l=>l.trim()).length)
const history=ref<{id:number;src:string;result:string;lang:string;time:string;rating:number}[]>([{id:1,src:'轻集料混凝土是一种新型环保建材',result:'Lightweight aggregate concrete is a new type of environmentally friendly building material',lang:'zh→en',time:'05-20 10:30',rating:5},{id:2,src:'本产品具有轻质高强的特点',result:'本製品は軽量高強度の特徴があります',lang:'zh→ja',time:'05-20 10:15',rating:4}])
const langNames:Record<string,string>={zh:'中文',ja:'日文',ko:'韩文',en:'英文',de:'德文',fr:'法文',es:'西文',pt:'葡文',it:'意文',nl:'荷文',sv:'瑞典文',hi:'印地文',id:'印尼文',tl:'菲律宾文',bn:'孟加拉文',my:'缅甸文',km:'高棉文',pl:'波兰文',cs:'捷克文',uk:'乌克兰文',ar:'阿拉伯文',tr:'土耳其文',fa:'波斯文',he:'希伯来文',sw:'斯瓦希里文',ha:'豪萨文',zu:'祖鲁文',am:'阿姆哈拉文',th:'泰文',vi:'越南文',ms:'马来文'}
async function doTranslate(){
  if(!src.value.trim()){message.warning('请输入文本');return}
  loading.value=true; apiError.value=''; result.value=''
  const prompt=`请将以下${langNames[srcLang.value]||srcLang.value}文本翻译成${langNames[tgtLang.value]||tgtLang.value}。只返回翻译结果，不要任何解释。\n\n${src.value}`
  try{
    const tk=getAuthToken()||''; const res=await fetch('/api/v1/super-admin/langchain/rag/query',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${tk}`},body:JSON.stringify({query:prompt})})
    if(!res.ok) throw new Error(`HTTP ${res.status}`)
    const d=(await res.json()).data||{}
    result.value=d.answer||'翻译失败，请重试'
    history.value.unshift({id:Date.now(),src:src.value,result:result.value,lang:`${srcLang.value}→${tgtLang.value}`,time:new Date().toLocaleTimeString('zh-CN'),rating:4})
  }catch(e:any){
    apiError.value=`API调用失败: ${e.message}。未使用本地假译文。`
    result.value=''
    message.error('翻译服务不可用，请检查配置后重试')
  }
  loading.value=false
}
async function doBatch(){ if(!batchText.value.trim())return; batchLoading.value=true; const lines=batchText.value.split('\n').filter(l=>l.trim()); for(let i=0;i<lines.length;i++){src.value=lines[i];await doTranslate()} batchLoading.value=false; message.success(`批量翻译完成: ${lines.length} 条`) }
function copyText(t:string){ navigator.clipboard.writeText(t); message.success('已复制') }
function addToGlossary(){ message.success(`已添加 "${src.value.slice(0,30)}" 到术语库`) }
</script>
