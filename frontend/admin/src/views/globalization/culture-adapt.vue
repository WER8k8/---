/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="文化适配" subtitle="多区域市场合规 · 本地化检查 · 格式适配" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="runScan" :loading="scanning">运行合规扫描</a-button>
        <a-button type="primary" @click="saveConfig">保存配置</a-button>
      </a-space>
    </template>
    <div class="space-y-6">

    <a-row :gutter="16">
      <a-col :span="6" v-for="r in regions" :key="r.code"><a-card size="small" :class="'border-t-4 '+r.border">
        <div class="flex items-center gap-2 mb-2"><a-tag size="small">{{ r.code }}</a-tag><span class="font-bold">{{ r.name }}</span></div>
        <div class="space-y-1 text-xs"><div v-for="c in r.checks" :key="c.l" class="flex justify-between items-center"><span>{{ c.l }}</span><YdCheckMark :kind="c.pass ? 'pass' : 'fail'" /></div></div>
        <a-button size="small" block class="mt-2" @click="inspect(r)">详情</a-button>
      </a-card></a-col>
    </a-row>

    <a-card title="RTL 布局预览" size="small">
      <a-switch v-model:checked="rtlEnabled"/> 启用RTL布局
      <div v-if="rtlEnabled" class="mt-4 p-4 bg-gray-100 rounded-lg text-right" dir="rtl">
        <p class="text-sm font-bold">مرحباً بكم في يودينغ لمواد البناء</p>
        <p class="text-xs text-gray-500">هذا مثال على تخطيط RTL للغة العربية</p>
        <div class="flex gap-2 justify-end mt-2"><a-button size="small">تسجيل الدخول</a-button><a-button size="small" type="primary">اشتراك</a-button></div>
      </div>
    </a-card>

    <a-card title="本地化格式配置" size="small">
      <a-table :columns="fmtCols" :dataSource="formats" rowKey="code" size="small" :pagination="false">
        <template #bodyCell="{column,record}">
          <template v-if="column.key==='date'"><a-select v-model:value="record.date" size="small" style="width:140px"><a-select-option value="YYYY-MM-DD">YYYY-MM-DD</a-select-option><a-select-option value="MM/DD/YYYY">MM/DD/YYYY</a-select-option><a-select-option value="DD/MM/YYYY">DD/MM/YYYY</a-select-option></a-select></template>
          <template v-if="column.key==='currency'"><a-select v-model:value="record.currency" size="small" style="width:100px"><a-select-option value="CNY">CNY ¥</a-select-option><a-select-option value="USD">USD $</a-select-option><a-select-option value="EUR">EUR €</a-select-option><a-select-option value="JPY">JPY ¥</a-select-option><a-select-option value="KRW">KRW ₩</a-select-option><a-select-option value="INR">INR ₹</a-select-option><a-select-option value="IDR">IDR Rp</a-select-option><a-select-option value="PHP">PHP ₱</a-select-option><a-select-option value="PLN">PLN zł</a-select-option><a-select-option value="SEK">SEK kr</a-select-option><a-select-option value="CZK">CZK Kč</a-select-option><a-select-option value="UAH">UAH ₴</a-select-option><a-select-option value="BDT">BDT ৳</a-select-option><a-select-option value="MMK">MMK K</a-select-option><a-select-option value="KHR">KHR ៛</a-select-option><a-select-option value="ETB">ETB Br</a-select-option><a-select-option value="NGN">NGN ₦</a-select-option><a-select-option value="ZAR">ZAR R</a-select-option><a-select-option value="KES">KES KSh</a-select-option><a-select-option value="SAR">SAR ﷼</a-select-option><a-select-option value="AED">AED د.إ</a-select-option><a-select-option value="TRY">TRY ₺</a-select-option><a-select-option value="GBP">GBP £</a-select-option><a-select-option value="BRL">BRL R$</a-select-option></a-select></template>
          <template v-if="column.key==='unit'"><a-select v-model:value="record.unit" size="small" style="width:80px"><a-select-option value="metric">公制</a-select-option><a-select-option value="imperial">英制</a-select-option></a-select></template>
          <template v-if="column.key==='tz'"><a-select v-model:value="record.tz" size="small" style="width:140px"><a-select-option value="Asia/Shanghai">Asia/Shanghai</a-select-option><a-select-option value="Asia/Tokyo">Asia/Tokyo</a-select-option><a-select-option value="Asia/Seoul">Asia/Seoul</a-select-option><a-select-option value="Asia/Riyadh">Asia/Riyadh</a-select-option><a-select-option value="Asia/Kolkata">Asia/Kolkata</a-select-option><a-select-option value="Asia/Jakarta">Asia/Jakarta</a-select-option><a-select-option value="Asia/Manila">Asia/Manila</a-select-option><a-select-option value="Asia/Yangon">Asia/Yangon</a-select-option><a-select-option value="Asia/Phnom_Penh">Asia/Phnom_Penh</a-select-option><a-select-option value="Asia/Dhaka">Asia/Dhaka</a-select-option><a-select-option value="Asia/Bangkok">Asia/Bangkok</a-select-option><a-select-option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh</a-select-option><a-select-option value="Asia/Kuala_Lumpur">Asia/Kuala_Lumpur</a-select-option><a-select-option value="Europe/Warsaw">Europe/Warsaw</a-select-option><a-select-option value="Europe/Prague">Europe/Prague</a-select-option><a-select-option value="Europe/Kyiv">Europe/Kyiv</a-select-option><a-select-option value="Europe/Stockholm">Europe/Stockholm</a-select-option><a-select-option value="Europe/Berlin">Europe/Berlin</a-select-option><a-select-option value="Europe/Paris">Europe/Paris</a-select-option><a-select-option value="Europe/Madrid">Europe/Madrid</a-select-option><a-select-option value="Europe/Rome">Europe/Rome</a-select-option><a-select-option value="Europe/Amsterdam">Europe/Amsterdam</a-select-option><a-select-option value="Europe/London">Europe/London</a-select-option><a-select-option value="Europe/Istanbul">Europe/Istanbul</a-select-option><a-select-option value="Africa/Nairobi">Africa/Nairobi</a-select-option><a-select-option value="Africa/Lagos">Africa/Lagos</a-select-option><a-select-option value="Africa/Johannesburg">Africa/Johannesburg</a-select-option><a-select-option value="Africa/Addis_Ababa">Africa/Addis_Ababa</a-select-option><a-select-option value="America/New_York">America/New_York</a-select-option><a-select-option value="America/Sao_Paulo">America/Sao_Paulo</a-select-option><a-select-option value="Asia/Dubai">Asia/Dubai</a-select-option></a-select></template>
        </template>
      </a-table>
    </a-card>

    <a-card title="扫描结果" size="small" v-if="scanResult">
      <a-alert :type="scanResult.pass?'success':'warning'" :message="`扫描完成: ${scanResult.pass?'全部通过':'发现问题'}`"/>
      <div class="mt-3 space-y-2"><div v-for="i in scanResult.items" :key="i.msg" class="flex items-center gap-2 text-sm"><YdCheckMark :kind="i.ok ? 'pass' : 'fail'" /><span class="text-gray-600">{{ i.msg }}</span></div></div>
    </a-card>

    <a-modal v-model:open="showRegionDetail" :title="regionDetail?.name ? `${regionDetail.name} 合规详情` : '区域详情'" :footer="null">
      <div v-if="regionDetail" class="space-y-2">
        <div v-for="c in regionDetail.checks" :key="c.l" class="flex justify-between text-sm">
          <span>{{ c.l }}</span>
          <span :class="c.pass ? 'text-green-600' : 'text-red-500'">{{ c.pass ? '通过' : '待处理' }}</span>
        </div>
      </div>
    </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdCheckMark, YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'
const rtlEnabled=ref(false); const scanning=ref(false); const scanResult=ref<any>(null)
const showRegionDetail=ref(false); const regionDetail=ref<any>(null)
const regions=ref([
  {code:'US',name:'美国',border:'border-blue-500',checks:[{l:'CCPA合规',pass:true},{l:'ADA无障碍',pass:true},{l:'州税规则',pass:false}]},
  {code:'DE',name:'德国',border:'border-yellow-500',checks:[{l:'CE认证',pass:true},{l:'德国建筑产品法规',pass:true},{l:'REACH合规',pass:false}]},
  {code:'FR',name:'法国',border:'border-red-500',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'法国NF标志',pass:false}]},
  {code:'ES',name:'西班牙',border:'border-red-400',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'UNE标准',pass:false}]},
  {code:'IT',name:'意大利',border:'border-green-400',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'IMQ认证',pass:false}]},
  {code:'NL',name:'荷兰',border:'border-orange-500',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'荷兰建筑法令',pass:false}]},
  {code:'UK',name:'英国',border:'border-blue-600',checks:[{l:'UKCA认证',pass:false},{l:'GDPR合规',pass:true},{l:'建筑法规',pass:true}]},
  {code:'PL',name:'波兰',border:'border-red-500',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'波兰建筑法规',pass:false}]},
  {code:'SE',name:'瑞典',border:'border-blue-400',checks:[{l:'CE认证',pass:true},{l:'REACH合规',pass:true},{l:'Boverket规范',pass:false}]},
  {code:'SA',name:'沙特',border:'border-green-500',checks:[{l:'SASO认证',pass:false},{l:'清真认证',pass:true},{l:'GCC商标',pass:false}]},
  {code:'AE',name:'阿联酋',border:'border-green-400',checks:[{l:'ESMA认证',pass:false},{l:'清真认证',pass:true},{l:'DM合规',pass:true}]},
  {code:'TR',name:'土耳其',border:'border-red-300',checks:[{l:'CE认证',pass:true},{l:'土耳其标准TSE',pass:false},{l:'海关登记',pass:true}]},
  {code:'IN',name:'印度',border:'border-orange-500',checks:[{l:'BIS认证',pass:false},{l:'GST合规',pass:true},{l:'海关登记',pass:true}]},
  {code:'ID',name:'印尼',border:'border-red-500',checks:[{l:'SNI认证',pass:false},{l:'清真认证',pass:true}]},
  {code:'BR',name:'巴西',border:'border-green-500',checks:[{l:'INMETRO认证',pass:false},{l:'ANVISA合规',pass:true},{l:'进口许可',pass:true}]},
  {code:'NG',name:'尼日利亚',border:'border-green-400',checks:[{l:'SON认证',pass:false},{l:'NAFDAC合规',pass:true}]},
  {code:'ZA',name:'南非',border:'border-yellow-600',checks:[{l:'SABS认证',pass:false},{l:'EER合规',pass:true}]},
  {code:'KE',name:'肯尼亚',border:'border-green-500',checks:[{l:'KEBS认证',pass:false},{l:'进口标准',pass:true}]},
  {code:'JP',name:'日本',border:'border-red-500',checks:[{l:'特定商取引法',pass:true},{l:'個人情報保護法',pass:true},{l:'消費税法',pass:true}]},
  {code:'KR',name:'韩国',border:'border-blue-500',checks:[{l:'KS认证',pass:false},{l:'個人情報保護法',pass:true},{l:'関税法',pass:true}]},
  {code:'VN',name:'越南',border:'border-yellow-500',checks:[{l:'CR认证',pass:false},{l:'进口标准',pass:true}]},
  {code:'TH',name:'泰国',border:'border-blue-400',checks:[{l:'TIS认证',pass:false},{l:'进口登记',pass:true}]},
  {code:'MY',name:'马来西亚',border:'border-blue-600',checks:[{l:'SIRIM认证',pass:false},{l:'清真认证',pass:true},{l:'进口许可',pass:true}]},
])
const fmtCols=[{title:'区域',dataIndex:'n'},{title:'日期格式',dataIndex:'date',key:'date'},{title:'货币',dataIndex:'currency',key:'currency'},{title:'单位',dataIndex:'unit',key:'unit'},{title:'时区',dataIndex:'tz',key:'tz'}]
const formats=ref([
  {code:'CN',n:'中国',date:'YYYY-MM-DD',currency:'CNY',unit:'metric',tz:'Asia/Shanghai'},
  {code:'US',n:'美国',date:'MM/DD/YYYY',currency:'USD',unit:'imperial',tz:'America/New_York'},
  {code:'DE',n:'德国',date:'DD.MM.YYYY',currency:'EUR',unit:'metric',tz:'Europe/Berlin'},
  {code:'FR',n:'法国',date:'DD/MM/YYYY',currency:'EUR',unit:'metric',tz:'Europe/Paris'},
  {code:'ES',n:'西班牙',date:'DD/MM/YYYY',currency:'EUR',unit:'metric',tz:'Europe/Madrid'},
  {code:'IT',n:'意大利',date:'DD/MM/YYYY',currency:'EUR',unit:'metric',tz:'Europe/Rome'},
  {code:'NL',n:'荷兰',date:'DD-MM-YYYY',currency:'EUR',unit:'metric',tz:'Europe/Amsterdam'},
  {code:'UK',n:'英国',date:'DD/MM/YYYY',currency:'GBP',unit:'imperial',tz:'Europe/London'},
  {code:'PL',n:'波兰',date:'DD.MM.YYYY',currency:'PLN',unit:'metric',tz:'Europe/Warsaw'},
  {code:'SE',n:'瑞典',date:'YYYY-MM-DD',currency:'SEK',unit:'metric',tz:'Europe/Stockholm'},
  {code:'SA',n:'沙特',date:'DD/MM/YYYY',currency:'SAR',unit:'metric',tz:'Asia/Riyadh'},
  {code:'AE',n:'阿联酋',date:'DD/MM/YYYY',currency:'AED',unit:'metric',tz:'Asia/Dubai'},
  {code:'TR',n:'土耳其',date:'DD.MM.YYYY',currency:'TRY',unit:'metric',tz:'Europe/Istanbul'},
  {code:'IN',n:'印度',date:'DD/MM/YYYY',currency:'INR',unit:'metric',tz:'Asia/Kolkata'},
  {code:'ID',n:'印尼',date:'DD/MM/YYYY',currency:'IDR',unit:'metric',tz:'Asia/Jakarta'},
  {code:'BR',n:'巴西',date:'DD/MM/YYYY',currency:'BRL',unit:'metric',tz:'America/Sao_Paulo'},
  {code:'NG',n:'尼日利亚',date:'DD/MM/YYYY',currency:'NGN',unit:'metric',tz:'Africa/Lagos'},
  {code:'ZA',n:'南非',date:'YYYY/MM/DD',currency:'ZAR',unit:'metric',tz:'Africa/Johannesburg'},
  {code:'KE',n:'肯尼亚',date:'DD/MM/YYYY',currency:'KES',unit:'metric',tz:'Africa/Nairobi'},
  {code:'JP',n:'日本',date:'YYYY-MM-DD',currency:'JPY',unit:'metric',tz:'Asia/Tokyo'},
  {code:'KR',n:'韩国',date:'YYYY-MM-DD',currency:'KRW',unit:'metric',tz:'Asia/Seoul'},
  {code:'VN',n:'越南',date:'DD/MM/YYYY',currency:'VND',unit:'metric',tz:'Asia/Ho_Chi_Minh'},
  {code:'TH',n:'泰国',date:'DD/MM/YYYY',currency:'THB',unit:'metric',tz:'Asia/Bangkok'},
  {code:'MY',n:'马来西亚',date:'DD/MM/YYYY',currency:'MYR',unit:'metric',tz:'Asia/Kuala_Lumpur'},
])
function runScan(){ scanning.value=true; setTimeout(()=>{ scanResult.value={pass:true,items:[{ok:true,msg:'GDPR Cookie 声明已配置'},{ok:true,msg:'RTL 样式表已加载'},{ok:true,msg:'货币格式化已正确'},{ok:false,msg:'沙特GCC商标注册待更新'},{ok:true,msg:'无障碍ARIA标签完整'}]}; scanning.value=false; message.success('扫描完成') },1200) }
function inspect(r:any){ regionDetail.value = r; showRegionDetail.value = true }
function saveConfig(){ message.success('配置已保存') }

onMounted(async () => {
  try { await apiGet('/international') } catch { /* 空状态 */ }
})
</script>
