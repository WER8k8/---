/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="API网关" subtitle="开放API管理与开发者文档" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="openDocs">文档</a-button>
        <a-button type="primary" @click="createKey"><PlusOutlined /> 创建API Key</a-button>
      </a-space>
    </template>
  <div class="space-y-6 animate-fade-in">    <div class="grid grid-cols-4 gap-4"><a-card v-for="s in st" :key="s.l" hoverable><a-statistic :title="s.l" :value="s.v" :valueStyle="{color:s.c}"/></a-card></div>
    <a-card title="API端点"><a-table :columns="ac" :data-source="apis" size="small" row-key="id">
      <template #bodyCell="{column,record}">
        <template v-if="column.key==='method'"><a-tag :color="{'GET':'green','POST':'blue','PUT':'orange','DELETE':'red'}[record.method as string]">{{ record.method }}</a-tag></template>
        <template v-if="column.key==='rate'">{{ record.rate }}/min</template>
      </template>
    </a-table></a-card>
    <a-card title="API Key管理"><a-table :columns="kc" :data-source="keys" size="small" row-key="id">
      <template #bodyCell="{column}"><template v-if="column.key==='action'"><a-popconfirm title="确定吊销？"><a-button size="small" type="link" danger>吊销</a-button></a-popconfirm></template></template>
    </a-table>    </a-card>
  </div>
  </YdPage>
</template><script setup lang="ts">import { ref,onMounted } from 'vue';import { Card,Statistic,Table,Tag,Button,Popconfirm,Space,message } from 'ant-design-vue';import { PlusOutlined } from '@ant-design/icons-vue';import { YdPage } from '@/components/youding';import { getAuthToken } from '@/utils/api'
const st=[{l:'活跃开发者',v:156,c:'#4a9b8c'},{l:'API调用量',v:'2.8M',c:'#8b5cf6'},{l:'平均延迟',v:'45ms',c:'#22c55e'},{l:'可用率',v:'99.95%',c:'#f59e0b'}]
const ac=[{title:'路径',dataIndex:'path'},{title:'方法',key:'method',width:70},{title:'描述',dataIndex:'desc'},{title:'限流',key:'rate',width:80},{title:'版本',dataIndex:'version',width:80}]
const apis = ref<any[]>([])
const kc=[{title:'名称',dataIndex:'name'},{title:'Key',dataIndex:'key'},{title:'权限',dataIndex:'scope',width:80},{title:'创建时间',dataIndex:'time',width:160},{title:'操作',key:'action',width:80}]
const keys = ref<any[]>([])
onMounted(async()=>{try{const tk=getAuthToken()||'';const r=await fetch('/api/v1/developer/',{headers:{Authorization:`Bearer ${tk}`}});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();if(d.data){const x=d.data;if(x.stats)x.stats.forEach((s:any,i:number)=>{if(st[i])st[i].v=s});if(x.apis)apis.value=x.apis;if(x.keys)keys.value=x.keys}}catch(e){message.warning('数据加载失败，请稍后重试')}})
function openDocs(){ window.open('/api/v1/docs', '_blank') }
function createKey() {
  const key = `yd_${Date.now().toString(36)}${Date.now().toString(36).slice(-8)}`;
  keys.value.unshift({
    id: Date.now(),
    name: `密钥-${keys.value.length + 1}`,
    key: `${key.slice(0, 12)}…`,
    scope: 'read',
    time: new Date().toLocaleString('zh-CN'),
  });
  message.success('API Key 已创建，请妥善保存');
}
</script>
