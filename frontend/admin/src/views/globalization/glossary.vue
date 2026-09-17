/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="术语库" :subtitle="`行业术语多语言标准化 · ${terms.length} 条已收录`" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="exportCSV">导出CSV</a-button>
        <a-button type="primary" @click="openAdd()">+ 添加术语</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
    <a-card size="small">
      <a-row :gutter="16" class="mb-4"><a-col :span="8"><a-input-search v-model:value="kw" placeholder="搜索术语(中/英/日/韩/德/法/西/阿等32种语言)..." @search="doSearch"/></a-col><a-col :span="4"><a-select v-model:value="catFilter" placeholder="行业分类" allowClear @change="doSearch"><a-select-option value="">全部</a-select-option><a-select-option value="建材">建材</a-select-option><a-select-option value="化工">化工</a-select-option></a-select></a-col></a-row>
      <a-table :columns="cols" :dataSource="filtered" rowKey="id" size="small" :pagination="{pageSize:10}">
        <template #bodyCell="{column,record}">
          <template v-if="column.key==='st'"><a-tag :color="record.st==='confirmed'?'green':record.st==='pending'?'orange':'default'">{{ {confirmed:'已确认',pending:'待审核',draft:'草稿'}[record.st as string] }}</a-tag></template>
          <template v-if="column.key==='act'"><a-space><a-button size="small" @click="openEdit(record)">编辑</a-button><a-popconfirm title="删除?" @confirm="del(record.id)"><a-button size="small" danger>删除</a-button></a-popconfirm></a-space></template>
        </template>
      </a-table>
    </a-card>
    <a-modal v-model:open="showEdit" :title="editing?'编辑术语':'添加术语'" @ok="save" width="900px">
      <a-form layout="vertical">
        <a-row :gutter="16"><a-col :span="12"><a-form-item label="中文术语" required><a-input v-model:value="f.zh"/></a-form-item></a-col><a-col :span="12"><a-form-item label="English" required><a-input v-model:value="f.en"/></a-form-item></a-col></a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">东亚</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="日本語"><a-input v-model:value="f.ja" placeholder="日本"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="한국어"><a-input v-model:value="f.ko" placeholder="韩国"/></a-form-item></a-col>
          <a-col :span="8"></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">欧美</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="Deutsch"><a-input v-model:value="f.de" placeholder="德国"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Français"><a-input v-model:value="f.fr" placeholder="法国"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Español"><a-input v-model:value="f.es" placeholder="西班牙"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="Português"><a-input v-model:value="f.pt" placeholder="葡萄牙/巴西"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Italiano"><a-input v-model:value="f.it" placeholder="意大利"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Nederlands"><a-input v-model:value="f.nl" placeholder="荷兰"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="Svenska"><a-input v-model:value="f.sv" placeholder="瑞典"/></a-form-item></a-col>
          <a-col :span="8"></a-col>
          <a-col :span="8"></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">南亚</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="हिन्दी"><a-input v-model:value="f.hi" placeholder="印度"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Bahasa Indonesia"><a-input v-model:value="f.idLang" placeholder="印尼"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Filipino"><a-input v-model:value="f.tl" placeholder="菲律宾"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="বাংলা"><a-input v-model:value="f.bn" placeholder="孟加拉"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="မြန်မာ"><a-input v-model:value="f.my" placeholder="缅甸"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="ភាសាខ្មែរ"><a-input v-model:value="f.km" placeholder="柬埔寨"/></a-form-item></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">中东欧</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="Polski"><a-input v-model:value="f.pl" placeholder="波兰"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Čeština"><a-input v-model:value="f.cs" placeholder="捷克"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Українська"><a-input v-model:value="f.uk" placeholder="乌克兰"/></a-form-item></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">中东</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="العربية"><a-input v-model:value="f.ar" placeholder="中东"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Türkçe"><a-input v-model:value="f.tr" placeholder="土耳其"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="فارسی"><a-input v-model:value="f.fa" placeholder="波斯语"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="עברית"><a-input v-model:value="f.he" placeholder="希伯来语"/></a-form-item></a-col>
          <a-col :span="8"></a-col>
          <a-col :span="8"></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">非洲</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="Kiswahili"><a-input v-model:value="f.sw" placeholder="肯尼亚/东非"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Hausa"><a-input v-model:value="f.ha" placeholder="尼日利亚/西非"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="isiZulu"><a-input v-model:value="f.zu" placeholder="南非"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="አማርኛ"><a-input v-model:value="f.am" placeholder="埃塞俄比亚"/></a-form-item></a-col>
          <a-col :span="8"></a-col>
          <a-col :span="8"></a-col>
        </a-row>
        <div class="text-xs text-gray-400 mb-2 font-medium">东南亚</div>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="ไทย"><a-input v-model:value="f.th" placeholder="泰国"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Tiếng Việt"><a-input v-model:value="f.vi" placeholder="越南"/></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="Bahasa Melayu"><a-input v-model:value="f.ms" placeholder="马来语"/></a-form-item></a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="行业分类"><a-select v-model:value="f.cat"><a-select-option value="建材">建材</a-select-option><a-select-option value="化工">化工</a-select-option><a-select-option value="机械">机械</a-select-option></a-select></a-form-item></a-col>
        </a-row>
      </a-form>
    </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'
const kw=ref(''); const catFilter=ref(''); const showEdit=ref(false); const editing=ref<any>(null)
const f=reactive({zh:'',en:'',ja:'',ko:'',de:'',fr:'',es:'',pt:'',it:'',nl:'',sv:'',hi:'',idLang:'',tl:'',bn:'',my:'',km:'',pl:'',cs:'',uk:'',ar:'',tr:'',fa:'',he:'',sw:'',ha:'',zu:'',am:'',th:'',vi:'',ms:'',cat:'建材'})
const cols=[{title:'中文',dataIndex:'zh',width:120},{title:'English',dataIndex:'en',width:140},{title:'Deutsch',dataIndex:'de',width:100},{title:'Français',dataIndex:'fr',width:100},{title:'Español',dataIndex:'es',width:100},{title:'العربية',dataIndex:'ar',width:100},{title:'分类',dataIndex:'cat',width:60},{title:'状态',dataIndex:'st',key:'st',width:70},{title:'操作',key:'act',width:120}]
const terms=ref([
  {id:1,zh:'轻集料混凝土',en:'Lightweight Aggregate Concrete',de:'Leichtzuschlagbeton',fr:'Béton léger',es:'Hormigón ligero',pt:'Concreto leve',it:'Calcestruzzo leggero',nl:'Lichtgewicht beton',sv:'Lättballastbetong',ja:'軽量骨材コンクリート',ko:'경량 골재 콘크리트',ar:'خرسانة الركام خفيفة الوزن',tr:'Hafif agrega betonu',fa:'بتن سبک با سنگدانه',he:'בטון קל משקל',hi:'हल्का समुच्चय कंक्रीट',idLang:'Beton Agregat Ringan',tl:'Lightweight Aggregate Concrete',bn:'হালকা অ্যাগ্রিগেট কংক্রিট',my:'ပေါ့ပါးသော အစုအဝေး ကွန်ကရစ်',km:'បេតុងទម្ងន់ស្រាល',pl:'Lekki beton kruszywowy',cs:'Lehčený beton',uk:'Легкий заповнювач бетон',sw:'Saruji nyepesi',ha:'Kankare mai sauƙi',zu:'Ukhonkolo we-Agregate Ebulula',am:'ቀላል አግሪጌት ኮንክሪት',th:'คอนกรีตมวลเบา',vi:'Bê tông nhẹ',ms:'Konkrit Agregat Ringan',cat:'建材',st:'confirmed'},
  {id:2,zh:'陶粒',en:'Ceramsite',de:'Blähton',fr:'Céramsite',es:'Ceramsita',pt:'Ceramsita',it:'Ceramsite',nl:'Ceramsiet',sv:'Ceramsit',ja:'セラムサイト',ko:'세람사이트',ar:'سيرامسيت',tr:'Seramzit',fa:'سرامسایت',he:'סראמסיט',hi:'सेरामसाइट',idLang:'Seramsit',tl:'Ceramsite',bn:'সেরামসাইট',my:'ဆီရမ်ဆိုက်',km:'សេរ៉ាមស៊ីត',pl:'Ceramsyt',cs:'Ceramsit',uk:'Керамзит',sw:'Ceramsite',ha:'Ceramsite',zu:'I-Ceramsite',am:'ሴራምሳይት',th:'เซรามไซต์',vi:'Ceramsite',ms:'Seramsit',cat:'建材',st:'confirmed'},
  {id:3,zh:'保温砂浆',en:'Thermal Insulation Mortar',de:'Wärmedämmputz',fr:'Mortier isolant',es:'Mortero aislante',pt:'Argamassa isolante',it:'Malta isolante',nl:'Isolatiemortel',sv:'Värmisoleringsbruk',ja:'断熱モルタル',ko:'단열 모르타르',ar:'ملاط العزل الحراري',tr:'Isı yalıtım harcı',fa:'ملات عایق حرارتی',he:'טיח בידוד תרמי',hi:'थर्मल इन्सुलेशन मोर्टार',idLang:'Mortar Isolasi Termal',tl:'Thermal Insulation Mortar',bn:'তাপ নিরোধক মর্টার',my:'အပူကာကွယ်ရေး မော်တာ',km:'បាយអកំដៅ',pl:'Zaprawa termoizolacyjna',cs:'Tepelně izolační malta',uk:'Теплоізоляційний розчин',sw:'Chokaa cha insulation ya joto',ha:'Turmi mai rufe zafi',zu:'Udaka lokugquma ukushisa',am:'የሙቀት መከላከያ ሞርታር',th:'ปูนฉนวนกันความร้อน',vi:'Vữa cách nhiệt',ms:'Mortar Penebat Haba',cat:'建材',st:'pending'},
  {id:4,zh:'抗压强度',en:'Compressive Strength',de:'Druckfestigkeit',fr:'Résistance à la compression',es:'Resistencia a la compresión',pt:'Resistência à compressão',it:'Resistenza a compressione',nl:'Druksterkte',sv:'Tryckhållfasthet',ja:'圧縮強度',ko:'압축 강도',ar:'قوة الضغط',tr:'Basınç dayanımı',fa:'مقاومت فشاری',he:'חוזק לחיצה',hi:'संपीड़न शक्ति',idLang:'Kekuatan Tekan',tl:'Compressive Strength',bn:'কম্প্রেসিভ স্ট্রেংথ',my:'ဖိအားခံနိုင်အား',km:'កម្លាំងបង្ហាប់',pl:'Wytrzymałość na ściskanie',cs:'Pevnost v tlaku',uk:'Міцність на стиск',sw:'Nguvu ya kukandamiza',ha:'Ƙarfin matsi',zu:'Amandla okucindezela',am:'የመጨመቅ ጥንካሬ',th:'กำลังอัด',vi:'Cường độ nén',ms:'Kekuatan Mampatan',cat:'建材',st:'confirmed'},
  {id:5,zh:'导热系数',en:'Thermal Conductivity',de:'Wärmeleitfähigkeit',fr:'Conductivité thermique',es:'Conductividad térmica',pt:'Condutividade térmica',it:'Conducibilità termica',nl:'Warmtegeleidbaarheid',sv:'Värmeledningsförmåga',ja:'熱伝導率',ko:'열전도율',ar:'الموصلية الحرارية',tr:'Isıl iletkenlik',fa:'رسانایی حرارتی',he:'מוליכות תרמית',hi:'तापीय चालकता',idLang:'Konduktivitas Termal',tl:'Thermal Conductivity',bn:'তাপ পরিবাহিতা',my:'အပူကူးယူနိုင်မှု',km:'ចរន្តកម្ដៅ',pl:'Przewodność cieplna',cs:'Tepelná vodivost',uk:'Теплопровідність',sw:'Uendeshaji wa joto',ha:'Ƙarfin zafin wuta',zu:'Ukusebenza kokushisa',am:'የሙቀት ምልላት',th:'การนำความร้อน',vi:'Độ dẫn nhiệt',ms:'Kekonduksian Terma',cat:'建材',st:'confirmed'},
  {id:6,zh:'氟碳涂料',en:'Fluorocarbon Coating',de:'Fluorkohlenstoffbeschichtung',fr:'Revêtement fluorocarboné',es:'Revestimiento de fluorocarbono',pt:'Revestimento de fluorcarbono',it:'Rivestimento fluorocarbonico',nl:'Fluorkoolstof coating',sv:'Fluorkolbeläggning',ja:'フッ素樹脂塗料',ko:'불소 수지 도료',ar:'طلاء الفلوروكربون',tr:'Florokarbon kaplama',fa:'پوشش فلوئوروکربن',he:'ציפוי פלואורופחמן',hi:'फ्लोरोकार्बन कोटिंग',idLang:'Lapisan Fluorokarbon',tl:'Fluorocarbon Coating',bn:'ফ্লুরোকার্বন লেপ',my:'ဖလိုရိုကာဗွန် အကာအကွယ်',km:'ថ្នាំកូតហ្វ្លុយរ៉ូកាបូន',pl:'Powłoka fluorowęglowa',cs:'Fluorouhlíkový nátěr',uk:'Фторвуглецеве покриття',sw:'Mpakato wa florokaboni',ha:'Rufin fluorocarbon',zu:'I-Fluorocarbon Coating',am:'የፍሎሮካርቦን ሽፋን',th:'สารเคลือบฟลูออโรคาร์บอน',vi:'Lớp phủ fluorocarbon',ms:'Salutan Fluorokarbon',cat:'化工',st:'draft'},
  {id:7,zh:'发泡剂',en:'Foaming Agent',de:'Schaummittel',fr:'Agent moussant',es:'Agente espumante',pt:'Agente espumante',it:'Agente schiumogeno',nl:'Schuimmiddel',sv:'Skummedel',ja:'発泡剤',ko:'발포제',ar:'عامل رغوة',tr:'Köpürtücü madde',fa:'عامل کف‌زا',he:'חומר מוקצף',hi:'फोमिंग एजेंट',idLang:'Agen Berbusa',tl:'Foaming Agent',bn:'ফোমিং এজেন্ট',my:'အမြှုပ်ထွက်ပစ္စည်း',km:'ភ្នាក់ងារពពុះ',pl:'Środek spieniający',cs:'Pěnidlo',uk:'Піноутворювач',sw:'Wakala wa kutoa povu',ha:'Mai yin kumfa',zu:'I-Foaming Agent',am:'የአረፋ ወኪል',th:'สารเกิดฟอง',vi:'Chất tạo bọt',ms:'Ejen Berbuih',cat:'化工',st:'pending'},
])
const filtered=computed(()=>terms.value.filter(t=>(!kw.value||t.zh.includes(kw.value)||t.en.toLowerCase().includes(kw.value.toLowerCase())||(t.de&&t.de.toLowerCase().includes(kw.value.toLowerCase()))||(t.fr&&t.fr.toLowerCase().includes(kw.value.toLowerCase()))||(t.es&&t.es.toLowerCase().includes(kw.value.toLowerCase()))||(t.ar&&t.ar.includes(kw.value))||(t.ja&&t.ja.includes(kw.value))||(t.ko&&t.ko.includes(kw.value))||(t.hi&&t.hi.includes(kw.value))||(t.idLang&&t.idLang.toLowerCase().includes(kw.value.toLowerCase()))||(t.pl&&t.pl.toLowerCase().includes(kw.value.toLowerCase()))||(t.pt&&t.pt.toLowerCase().includes(kw.value.toLowerCase()))||(t.it&&t.it.toLowerCase().includes(kw.value.toLowerCase()))||(t.nl&&t.nl.toLowerCase().includes(kw.value.toLowerCase()))||(t.sv&&t.sv.toLowerCase().includes(kw.value.toLowerCase()))||(t.tr&&t.tr.toLowerCase().includes(kw.value.toLowerCase()))||(t.fa&&t.fa.includes(kw.value))||(t.he&&t.he.includes(kw.value))||(t.tl&&t.tl.toLowerCase().includes(kw.value.toLowerCase()))||(t.th&&t.th.includes(kw.value))||(t.vi&&t.vi.toLowerCase().includes(kw.value.toLowerCase()))||(t.ms&&t.ms.toLowerCase().includes(kw.value.toLowerCase()))||(t.bn&&t.bn.includes(kw.value))||(t.my&&t.my.includes(kw.value))||(t.km&&t.km.includes(kw.value))||(t.cs&&t.cs.toLowerCase().includes(kw.value.toLowerCase()))||(t.uk&&t.uk.toLowerCase().includes(kw.value.toLowerCase()))||(t.sw&&t.sw.toLowerCase().includes(kw.value.toLowerCase()))||(t.ha&&t.ha.toLowerCase().includes(kw.value.toLowerCase()))||(t.zu&&t.zu.toLowerCase().includes(kw.value.toLowerCase()))||(t.am&&t.am.includes(kw.value)))&&(!catFilter.value||t.cat===catFilter.value)))
function openAdd(){ editing.value=null; Object.assign(f,{zh:'',en:'',ja:'',ko:'',de:'',fr:'',es:'',pt:'',it:'',nl:'',sv:'',hi:'',idLang:'',tl:'',bn:'',my:'',km:'',pl:'',cs:'',uk:'',ar:'',tr:'',fa:'',he:'',sw:'',ha:'',zu:'',am:'',th:'',vi:'',ms:'',cat:'建材'}); showEdit.value=true }
function openEdit(r:any){ editing.value=r; Object.assign(f,{zh:r.zh,en:r.en,ja:r.ja||'',ko:r.ko||'',de:r.de||'',fr:r.fr||'',es:r.es||'',pt:r.pt||'',it:r.it||'',nl:r.nl||'',sv:r.sv||'',hi:r.hi||'',idLang:r.idLang||'',tl:r.tl||'',bn:r.bn||'',my:r.my||'',km:r.km||'',pl:r.pl||'',cs:r.cs||'',uk:r.uk||'',ar:r.ar||'',tr:r.tr||'',fa:r.fa||'',he:r.he||'',sw:r.sw||'',ha:r.ha||'',zu:r.zu||'',am:r.am||'',th:r.th||'',vi:r.vi||'',ms:r.ms||'',cat:r.cat}); showEdit.value=true }
function save(){ if(!f.zh||!f.en){message.warning('中英文必填');return}; if(editing.value){Object.assign(editing.value,{zh:f.zh,en:f.en,ja:f.ja,ko:f.ko,de:f.de,fr:f.fr,es:f.es,pt:f.pt,it:f.it,nl:f.nl,sv:f.sv,hi:f.hi,idLang:f.idLang,tl:f.tl,bn:f.bn,my:f.my,km:f.km,pl:f.pl,cs:f.cs,uk:f.uk,ar:f.ar,tr:f.tr,fa:f.fa,he:f.he,sw:f.sw,ha:f.ha,zu:f.zu,am:f.am,th:f.th,vi:f.vi,ms:f.ms,cat:f.cat});editing.value.st='pending';message.success('已更新')}else{terms.value.unshift({id:Date.now(),zh:f.zh,en:f.en,ja:f.ja,ko:f.ko,de:f.de,fr:f.fr,es:f.es,pt:f.pt,it:f.it,nl:f.nl,sv:f.sv,hi:f.hi,idLang:f.idLang,tl:f.tl,bn:f.bn,my:f.my,km:f.km,pl:f.pl,cs:f.cs,uk:f.uk,ar:f.ar,tr:f.tr,fa:f.fa,he:f.he,sw:f.sw,ha:f.ha,zu:f.zu,am:f.am,th:f.th,vi:f.vi,ms:f.ms,cat:f.cat,st:'pending'});message.success('已添加')}; showEdit.value=false }
function del(id:number){ terms.value=terms.value.filter(t=>t.id!==id); message.success('已删除') }
function doSearch(){}
function exportCSV(){ const csv='\uFEFF中文,English,Deutsch,Français,Español,العربية,日本語,한국어,分类\n'+terms.value.map(t=>[t.zh,t.en,t.de||'',t.fr||'',t.es||'',t.ar||'',t.ja||'',t.ko||'',t.cat].join(',')).join('\n'); const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='glossary.csv'; a.click(); message.success('已导出') }

onMounted(async () => {
  try { await apiGet('/international') } catch { /* 空状态 */ }
})
</script>
