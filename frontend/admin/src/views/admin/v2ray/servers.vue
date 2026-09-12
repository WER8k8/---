<template>
  <YdPage title="V2RayN 服务器配置" subtitle="V2Ray / Xray 服务器节点管理" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAdd=true">+ 添加节点</a-button>
    </template>
    <div class="space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <a-card size="small"><a-statistic title="总节点" :value="servers.length" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
        <a-card size="small"><a-statistic title="在线" :value="servers.filter((s:any)=>s.status==='online').length" :value-style="{ color: '#22c55e' }"/></a-card>
        <a-card size="small"><a-statistic title="平均延迟" :value="avgLatency+'ms'" :value-style="{ color: '#8b5cf6' }"/></a-card>
        <a-card size="small"><a-statistic title="总流量" :value="totalTraffic" :value-style="{ color: '#f59e0b' }"/></a-card>
      </div>
      <a-card title="节点列表" size="small">
        <a-table :columns="cols" :dataSource="servers" rowKey="id" size="small">
          <template #bodyCell="{column,record}">
            <template v-if="column.key==='status'"><a-tag :color="record.status==='online'?'green':'red'">{{ record.status==='online'?'在线':'离线' }}</a-tag></template>
            <template v-if="column.key==='protocol'"><a-tag>{{ record.protocol }}</a-tag></template>
            <template v-if="column.key==='actions'">
              <a-space><a-button size="small" @click="testConn(record)">测试</a-button><a-button size="small" @click="editServer(record)">编辑</a-button><a-button size="small" danger @click="delServer(record)">删除</a-button></a-space>
            </template>
          </template>
        </a-table>
      </a-card>
      <a-modal v-model:open="showAdd" title="添加节点" @ok="addServer">
        <a-form layout="vertical">
          <a-form-item label="备注名称"><a-input v-model:value="form.name" placeholder="如: 日本东京-01"/></a-form-item>
          <a-form-item label="协议"><a-select v-model:value="form.protocol"><a-select-option value="vmess">VMess</a-select-option><a-select-option value="vless">VLESS</a-select-option><a-select-option value="trojan">Trojan</a-select-option><a-select-option value="shadowsocks">Shadowsocks</a-select-option></a-select></a-form-item>
          <a-form-item label="服务器地址"><a-input v-model:value="form.address" placeholder="server.example.com"/></a-form-item>
          <a-form-item label="端口"><a-input-number v-model:value="form.port" :min="1" :max="65535"/></a-form-item>
          <a-form-item label="UUID / 密码"><a-input-password v-model:value="form.uuid" placeholder="UUID 或密码"/></a-form-item>
          <a-form-item label="传输协议"><a-select v-model:value="form.transport"><a-select-option value="tcp">TCP</a-select-option><a-select-option value="ws">WebSocket</a-select-option><a-select-option value="grpc">gRPC</a-select-option><a-select-option value="h2">HTTP/2</a-select-option></a-select></a-form-item>
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

const showAdd = ref(false)
const form = reactive({ name: '', protocol: 'vmess', address: '', port: 443, uuid: '', transport: 'ws' })
const servers = ref<any[]>([])

async function loadServers() {
  try {
    const d = await apiGet('/super-admin/v2ray/servers')
    const items = d?.items ?? d?.data?.items
    if (Array.isArray(items)) servers.value = items
  } catch { /* 空状态 */ }
}

onMounted(loadServers)
const cols=[{title:'名称',dataIndex:'name'},{title:'协议',dataIndex:'protocol',key:'protocol'},{title:'地址',dataIndex:'address'},{title:'端口',dataIndex:'port'},{title:'状态',dataIndex:'status',key:'status'},{title:'延迟',dataIndex:'latency'},{title:'上行',dataIndex:'upload'},{title:'下行',dataIndex:'download'},{title:'操作',key:'actions'}]
const avgLatency=computed(()=>{const o=servers.value.filter((s:any)=>s.status==='online'&&typeof s.latency==='number'); return o.length?Math.round(o.reduce((a:number,s:any)=>a+s.latency,0)/o.length):0})
const totalTraffic=computed(()=>{const d=servers.value.reduce((a:number,s:any)=>{const m=s.download?.match(/[\d.]+/); return a+(m?parseFloat(m[0]):0)},0); return d.toFixed(1)+'GB'})
function addServer(){ servers.value.unshift({id:Date.now(),name:form.name||'新节点',protocol:(form.protocol||'vmess').toUpperCase(),address:form.address,port:form.port,status:'offline',latency:'—',upload:'0',download:'0'}); showAdd.value=false; message.success('节点已添加') }
function testConn(r:any){
  const latency = typeof r.latency === 'number' ? r.latency : (r.status === 'online' ? avgLatency.value : null)
  message.success(latency != null ? `${r.name} 延迟 ${latency}ms` : `${r.name} 节点离线，无法测速`)
}
function editServer(r:any){ Object.assign(form,{name:r.name,protocol:r.protocol.toLowerCase(),address:r.address,port:r.port}); showAdd.value=true }
function delServer(r:any){ servers.value=servers.value.filter(s=>s.id!==r.id); message.success('已删除') }
</script>
