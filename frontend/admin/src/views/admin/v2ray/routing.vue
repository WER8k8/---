<template>
  <YdPage title="路由规则" subtitle="代理路由策略 · 分流规则 · 域名/IP 黑白名单" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAdd=true">+ 添加规则</a-button>
    </template>
    <div class="space-y-6">
      <a-row :gutter="16">
        <a-col :span="12"><a-card title="全局策略" size="small"><a-radio-group v-model:value="globalPolicy"><a-radio value="proxy">全局代理</a-radio><a-radio value="direct">全局直连</a-radio><a-radio value="rule">规则分流</a-radio></a-radio-group><div class="mt-3 text-xs text-gray-400">当前: {{ globalPolicy==='rule'?'按规则分流后代理':'全部'+({proxy:'代理',direct:'直连'}[globalPolicy]||'') }}</div></a-card></a-col>
        <a-col :span="12"><a-card title="DNS 设置" size="small"><a-form-item label="DNS 服务器"><a-input v-model:value="dns" placeholder="8.8.8.8, 1.1.1.1"/></a-form-item><a-switch v-model:checked="dnsOverHttps"/> DNS over HTTPS</a-card></a-col>
      </a-row>
      <a-card title="分流规则" size="small"><a-table :columns="c" :dataSource="rules" rowKey="id" size="small">
        <template #bodyCell="{column,record}">
          <template v-if="column.key==='a'"><a-tag :color="record.a==='proxy'?'blue':record.a==='direct'?'green':'orange'">{{ {proxy:'代理',direct:'直连',block:'阻止'}[record.a as string] }}</a-tag></template>
          <template v-if="column.key==='ac'"><a-space><a-switch v-model:checked="record.enabled" size="small" @change="toggleRule(record)"/><a-button size="small" danger @click="delRule(record)">删除</a-button></a-space></template>
        </template>
      </a-table></a-card>
      <a-modal v-model:open="showAdd" title="添加规则" @ok="addRule">
        <a-form layout="vertical">
          <a-form-item label="规则类型"><a-select v-model:value="f.type"><a-select-option value="domain">域名</a-select-option><a-select-option value="ip">IP</a-select-option><a-select-option value="geosite">GeoSite</a-select-option><a-select-option value="geoip">GeoIP</a-select-option></a-select></a-form-item>
          <a-form-item label="匹配值"><a-input v-model:value="f.value" placeholder="example.com 或 10.0.0.0/8 或 geosite:google"/></a-form-item>
          <a-form-item label="动作"><a-select v-model:value="f.action"><a-select-option value="proxy">代理</a-select-option><a-select-option value="direct">直连</a-select-option><a-select-option value="block">阻止</a-select-option></a-select></a-form-item>
        </a-form>
      </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'

const globalPolicy=ref('rule'); const dns=ref('8.8.8.8, 223.5.5.5'); const dnsOverHttps=ref(true); const showAdd=ref(false)
const f=reactive({type:'domain',value:'',action:'proxy'})
const c=[{title:'类型',dataIndex:'t'},{title:'匹配值',dataIndex:'v'},{title:'动作',dataIndex:'a',key:'a'},{title:'启用',key:'ac'}]
const rules = ref<any[]>([])

function addRule(){ rules.value.unshift({id:Date.now(),t:f.type,v:f.value||'new-rule',a:f.action,enabled:true}); showAdd.value=false; message.success('规则已添加') }
function toggleRule(r:any){ message.success(`${r.v} ${r.enabled?'已启用':'已禁用'}`) }
function delRule(r:any){ rules.value=rules.value.filter(x=>x.id!==r.id) }

onMounted(async () => {
  try { await apiGet('/super-admin/v2ray/routing') } catch { /* 空状态 */ }
})
</script>
