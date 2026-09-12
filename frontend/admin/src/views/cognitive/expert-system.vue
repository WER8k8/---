<template>
  <YdPage title="专家系统" subtitle="建材行业规则引擎 · 推理系统 · 对接RAG知识库" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAdd=true">+ 添加规则</a-button>
    </template>
    <div class="space-y-6">
    <a-card title="规则库" size="small"><a-table :columns="cols" :dataSource="rules" rowKey="id" size="small" :pagination="false">
      <template #bodyCell="{column,record}"><template v-if="column.key==='active'"><a-switch v-model:checked="record.active" size="small"/></template><template v-if="column.key==='pri'"><a-tag :color="record.pri==='high'?'red':'blue'">{{ record.pri==='high'?'高':'普通' }}</a-tag></template><template v-if="column.key==='act'"><a-button size="small" danger @click="delRule(record.id)">删除</a-button></template></template>
    </a-table></a-card>

    <a-card title="推理引擎 (对接RAG)" size="small">
      <a-form layout="vertical"><a-form-item label="问题类型"><a-select v-model:value="inferType"><a-select-option value="product">产品选型</a-select-option><a-select-option value="construction">施工方案</a-select-option><a-select-option value="quality">质量检测</a-select-option></a-select></a-form-item>
      <div v-if="inferType==='product'"><a-row :gutter="16"><a-col :span="8"><a-form-item label="密度等级"><a-select v-model:value="p.density"><a-select-option value="LC20">LC20</a-select-option><a-select-option value="LC30">LC30</a-select-option><a-select-option value="LC40">LC40</a-select-option></a-select></a-form-item></a-col><a-col :span="8"><a-form-item label="应用场景"><a-select v-model:value="p.scene"><a-select-option value="wall">外墙保温</a-select-option><a-select-option value="floor">楼地面</a-select-option><a-select-option value="roof">屋面</a-select-option></a-select></a-form-item></a-col><a-col :span="8"><a-form-item label="强度要求"><a-select v-model:value="p.strength"><a-select-option value="high">高强</a-select-option><a-select-option value="normal">常规</a-select-option></a-select></a-form-item></a-col></a-row></div>
      <div v-if="inferType==='construction'"><a-row :gutter="16"><a-col :span="12"><a-form-item label="施工季节"><a-select v-model:value="p.season"><a-select-option value="summer">夏季</a-select-option><a-select-option value="winter">冬季</a-select-option></a-select></a-form-item></a-col><a-col :span="12"><a-form-item label="施工面积(m²)"><a-input-number v-model:value="p.area" :min="1"/></a-form-item></a-col></a-row></div>
      <div v-if="inferType==='quality'"><a-row :gutter="16"><a-col :span="12"><a-form-item label="检测项目"><a-select v-model:value="p.testItem"><a-select-option value="compressive">抗压强度</a-select-option><a-select-option value="thermal">导热系数</a-select-option><a-select-option value="density">密度检测</a-select-option></a-select></a-form-item></a-col><a-col :span="12"><a-form-item label="标准等级"><a-select v-model:value="p.standard"><a-select-option value="GB">国标 GB</a-select-option><a-select-option value="JGJ">行标 JGJ</a-select-option></a-select></a-form-item></a-col></a-row></div>
      <a-button type="primary" @click="doInfer" :loading="inferring">开始推理</a-button></a-form>
      <div v-if="inferResult" class="mt-4 p-4 bg-green-50 rounded-lg"><h4 class="font-semibold mb-2">推理结果</h4><div class="text-sm whitespace-pre-wrap">{{ inferResult }}</div></div>
    </a-card>
    <a-modal v-model:open="showAdd" title="添加规则" @ok="addRule"><a-form layout="vertical"><a-form-item label="规则名称"><a-input v-model:value="f.name"/></a-form-item><a-form-item label="条件"><a-input v-model:value="f.condition" placeholder="如: density==LC20 AND scene==wall"/></a-form-item><a-form-item label="结论"><a-textarea v-model:value="f.conclusion" :rows="2"/></a-form-item></a-form></a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'; import { message } from 'ant-design-vue'; import { YdPage } from '@/components/youding'; import { getAuthToken } from '@/utils/api'
const showAdd=ref(false); const inferType=ref('product'); const inferring=ref(false); const inferResult=ref('')
const p=reactive({density:'LC20',scene:'wall',strength:'normal',season:'summer',area:100,testItem:'compressive',standard:'GB'})
const f=reactive({name:'',condition:'',conclusion:''})
const cols=[{title:'规则名称',dataIndex:'n'},{title:'条件',dataIndex:'c'},{title:'结论',dataIndex:'o'},{title:'优先级',dataIndex:'pri',key:'pri'},{title:'启用',dataIndex:'active',key:'active'},{title:'操作',key:'act'}]
const rules=ref([{id:1,n:'密度-场景匹配',c:'density==LC20 AND scene==wall',o:'推荐LC20轻集料混凝土,干密度≤1200kg/m³',pri:'high',active:true},{id:2,n:'冬季施工方案',c:'season==winter',o:'建议添加防冻剂,施工温度≥5°C,养护期延长3天',pri:'high',active:true},{id:3,n:'抗压检测标准',c:'testItem==compressive',o:'GB/T 50081标准,试块尺寸150mm³,28天龄期',pri:'normal',active:true},{id:4,n:'屋面应用',c:'scene==roof',o:'选用LC30以上,增加防水层,坡度≥2%',pri:'normal',active:true}])
function addRule(){ rules.value.unshift({id:Date.now(),n:f.name||'新规则',c:f.condition,o:f.conclusion,pri:'normal',active:true}); showAdd.value=false; message.success('规则已添加') }
function delRule(id:number){ rules.value=rules.value.filter(r=>r.id!==id); message.success('已删除') }
async function doInfer(){
  inferring.value=true; inferResult.value=''
  const params:string[]=[];
  if(inferType.value==='product') params.push(`密度等级=${p.density}`,`场景=${p.scene}`,`强度=${p.strength}`)
  else if(inferType.value==='construction') params.push(`季节=${p.season}`,`面积=${p.area}m²`)
  else params.push(`检测=${p.testItem}`,`标准=${p.standard}`)
  // 先匹配本地规则
  const matched=rules.value.filter(r=>r.active&&(r.c.includes(String(Object.values(p).find(v=>typeof v==='string'&&String(v).length>1)||''))||r.c.includes(inferType.value)))
  if(matched.length){ inferResult.value=matched.map(r=>`[规则] ${r.n}: ${r.o}`).join('\n'); inferring.value=false; return }
  // 调用RAG API
  try{
    const h:any={Authorization:`Bearer ${getAuthToken()}`,'Content-Type':'application/json'};
    const r=await fetch('/api/v1/super-admin/langchain/rag/query',{method:'POST',headers:h,body:JSON.stringify({query:`建材专家系统：${inferType.value==='product'?'产品选型':inferType.value==='construction'?'施工方案':'质量检测'}，参数：${params.join(',')}`})});
    const d=await r.json(); inferResult.value=d.data?.answer||'推理完成，无匹配结果'
  }catch{
    inferResult.value='RAG API不可用。本地规则已匹配完成。'
  }
  inferring.value=false
}
</script>
