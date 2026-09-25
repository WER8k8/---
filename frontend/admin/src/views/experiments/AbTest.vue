/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
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
  try{
    const token=getAuthToken()||''
    const res=await fetch(`/api/v1/ab-test/${id}/start`,{method:'POST',headers:{Authorization:`Bearer ${token}`}})
    if(!res.ok){ message.error(`启动失败（HTTP ${res.status}）`); return }
    rows.value=rows.value.map(r=>r.id===id?{...r,status:'running'}:r)
    message.success('已启动')
  }catch(e){
    message.error(e instanceof Error ? e.message : '启动请求失败')
  }
}
async function stop(id:string){
  try{
    const token=getAuthToken()||''
    // 2026-09-25 修正：后端真实端点是 /pause，原写作 /stop → 404。
    // 且 fetch 对 404 **不会 reject**，原实现因此无条件弹「已停止」并改状态 = 假成功。
    const res=await fetch(`/api/v1/ab-test/${id}/pause`,{method:'POST',headers:{Authorization:`Bearer ${token}`}})
    if(!res.ok){ message.error(`停止失败（HTTP ${res.status}）`); return }
    rows.value=rows.value.map(r=>r.id===id?{...r,status:'stopped'}:r)
    message.success('已停止')
  }catch(e){
    message.error(e instanceof Error ? e.message : '停止请求失败')
  }
}
async function remove(id:string){
  try{
    const token=getAuthToken()||''
    // 2026-09-25 修正：原实现**先删行再发请求**且 catch 为空 → 删除失败时行也消失（假成功）。
    const res=await fetch(`/api/v1/ab-test/${id}`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`}})
    if(!res.ok){ message.error(`删除失败（HTTP ${res.status}）`); return }
    rows.value=rows.value.filter(r=>r.id!==id)
    message.success('已删除')
  }catch(e){
    message.error(e instanceof Error ? e.message : '删除请求失败')
  }
}
async function create(){
  try{
    const token=getAuthToken()||''
    const res=await fetch('/api/v1/ab-test',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({name:form.name,page:form.page})})
    // 2026-09-25 修正：原 catch 会插入本地假行 `exp-${Date.now()}` 并提示「已创建(本地)」= 假成功。
    if(!res.ok){ message.error(`创建失败（HTTP ${res.status}）`); return }
    showCreate.value=false
    message.success('已创建')
    await load()
  }catch(e){
    message.error(e instanceof Error ? e.message : '创建请求失败')
  }
}
onMounted(load)
</script>
