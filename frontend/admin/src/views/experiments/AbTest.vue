<template>
  <YdPage title="A/B 测试" subtitle="/api/v1/ab-test 实验列表与启停" surface="elevated">
    <template #actions>
      <a-space>
        <a-button type="primary" @click="showCreate=true">+ 新建实验</a-button>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>
    <a-card>
      <a-table :columns="columns" :data-source="rows" :loading="loading" :pagination="false" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='status'"><a-tag :color="record.status==='running'?'blue':record.status==='stopped'?'default':'green'">{{ {running:'运行中',stopped:'已停止',completed:'已完成'}[record.status as string]||record.status }}</a-tag></template>
          <template v-if="column.key==='actions'">
            <a-space>
              <a-button size="small" v-if="record.status!=='running'" @click="start(record.id)">启动</a-button>
              <a-button size="small" v-if="record.status==='running'" @click="stop(record.id)">停止</a-button>
              <a-button size="small" danger @click="remove(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    <a-modal v-model:open="showCreate" title="新建实验" @ok="create">
      <a-form layout="vertical"><a-form-item label="名称"><a-input v-model:value="form.name"/></a-form-item><a-form-item label="页面路径"><a-input v-model:value="form.page"/></a-form-item><a-form-item label="变体A"><a-textarea v-model:value="form.varA" :rows="2"/></a-form-item><a-form-item label="变体B"><a-textarea v-model:value="form.varB" :rows="2"/></a-form-item></a-form>
    </a-modal>
  </YdPage>
</template>
<script setup lang="ts">
import { getAuthToken } from '@/utils/api'
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'

const loading=ref(false); const showCreate=ref(false)
const form=reactive({name:'',page:'',varA:'',varB:''})
const rows=ref<any[]>([])
const columns=[{title:'ID',dataIndex:'id',width:200,ellipsis:true},{title:'名称',dataIndex:'name'},{title:'状态',dataIndex:'status',key:'status'},{title:'操作',key:'actions',width:200}]
async function load(){
  loading.value=true
  try{
    const token=getAuthToken()||''
    const res=await fetch('/api/v1/ab-test',{headers:{Authorization:`Bearer ${token}`}})
    if(!res.ok) throw new Error(`HTTP ${res.status}`)
    const body=await res.json()
    if(body.code===0&&body.data){
      const items = Array.isArray(body.data) ? body.data : (body.data.items || [])
      rows.value = items.map((x: any, idx: number) => ({
        id: x.id ?? `exp-${idx + 1}`,
        name: x.name || '未命名实验',
        status: x.status || 'stopped',
      }))
    }else if(Array.isArray(body)){
      rows.value=body.map((x:any, idx:number)=>({id:x.id ?? `exp-${idx+1}`,name:x.name,status:x.status}))
    }
  }catch{
    rows.value=[]
    message.error('数据加载失败，请稍后重试')
  }
  loading.value=false
}
async function start(id:string){
  try{const token=getAuthToken()||'';await fetch(`/api/v1/ab-test/${id}/start`,{method:'POST',headers:{Authorization:`Bearer ${token}`}});rows.value=rows.value.map(r=>r.id===id?{...r,status:'running'}:r);message.success('已启动')}catch{rows.value=rows.value.map(r=>r.id===id?{...r,status:'running'}:r);message.success('已启动(本地)')}
}
async function stop(id:string){
  try{const token=getAuthToken()||'';await fetch(`/api/v1/ab-test/${id}/stop`,{method:'POST',headers:{Authorization:`Bearer ${token}`}});rows.value=rows.value.map(r=>r.id===id?{...r,status:'stopped'}:r);message.success('已停止')}catch{rows.value=rows.value.map(r=>r.id===id?{...r,status:'stopped'}:r)}
}
async function remove(id:string){
  rows.value=rows.value.filter(r=>r.id!==id);message.success('已删除')
  try{const token=getAuthToken()||'';await fetch(`/api/v1/ab-test/${id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`}})}catch{}
}
async function create(){
  try{const token=getAuthToken()||'';await fetch('/api/v1/ab-test',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({name:form.name,page:form.page})});showCreate.value=false;load()}catch{rows.value.unshift({id:'exp-'+Date.now(),name:form.name||'新实验',status:'stopped'});showCreate.value=false;message.success('已创建(本地)')}
}
onMounted(load)
</script>
