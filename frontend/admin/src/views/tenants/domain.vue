<template>
  <YdPage title="域名绑定" subtitle="主域名与自定义域名 · DNS 验证 · SSL 证书" surface="elevated">
  <div class="space-y-6">
    <!-- 主域名展示 -->
    <a-card title="主域名" size="small">
      <div class="flex items-center gap-3">
        <GlobalOutlined class="text-2xl text-blue-500" />
        <div>
          <p class="text-lg font-semibold text-gray-800">{{ primaryDomain }}</p>
          <p class="text-xs text-gray-400">当前租户的主域名（子域名），客户可通过此地址访问您的专属网站</p>
        </div>
      </div>
    </a-card>

    <!-- 添加域名 -->
    <a-card title="绑定自定义域名" size="small">
      <div class="mb-4 flex items-center gap-3">
        <a-input
          v-model:value="newDomain"
          placeholder="请输入要绑定的域名，如 www.abc-building.com"
          class="flex-1"
        />
        <a-button type="primary" :loading="addingDomain" @click="addDomain">添加</a-button>
      </div>

      <!-- DNS 配置提示 -->
      <transition name="fade">
        <div v-if="dnsConfig.visible" class="dns-hint">
          <div class="dns-hint-header">
            <InfoCircleOutlined class="text-blue-500" />
            <span>请将以下 DNS 记录添加到您的域名管理后台</span>
          </div>
          <div class="dns-config-block">
            <div class="dns-method">
              <h4>方法一：CNAME 记录（推荐）</h4>
              <table class="dns-table">
                <tr><td class="dns-label">主机记录</td><td class="dns-value"><code>www</code></td></tr>
                <tr><td class="dns-label">记录类型</td><td class="dns-value"><code>CNAME</code></td></tr>
                <tr><td class="dns-label">记录值</td><td class="dns-value"><code>saas.youding.com</code></td></tr>
              </table>
            </div>
            <div class="dns-method">
              <h4>方法二：A 记录</h4>
              <table class="dns-table">
                <tr><td class="dns-label">记录类型</td><td class="dns-value"><code>A</code></td></tr>
                <tr><td class="dns-label">记录值</td><td class="dns-value"><code>123.123.123.123</code></td></tr>
              </table>
            </div>
          </div>
          <a-button type="default" :loading="verifyingDns" @click="verifyDns">验证 DNS 配置</a-button>
        </div>
      </transition>
    </a-card>

    <!-- 域名列表 -->
    <a-card title="已绑定域名" size="small">
      <a-table
        :columns="columns"
        :dataSource="domainList"
        rowKey="id"
        size="small"
        :loading="loading"
        :pagination="{ pageSize: 10 }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 验证状态 -->
          <template v-if="column.key === 'verifyStatus'">
            <a-tag v-if="record.verifyStatus === 'verified'" color="success">
              <CheckCircleOutlined /> 已验证
            </a-tag>
            <a-tag v-else-if="record.verifyStatus === 'verifying'" color="processing">
              <LoadingOutlined /> 验证中
            </a-tag>
            <a-tag v-else color="error">
              <CloseCircleOutlined /> 未验证
            </a-tag>
          </template>

          <!-- SSL 状态 -->
          <template v-if="column.key === 'sslStatus'">
            <a-tag v-if="record.sslStatus === 'enabled'" color="success">
              <CheckCircleOutlined /> 已启用
            </a-tag>
            <a-tag v-else-if="record.sslStatus === 'pending'" color="warning">
              <ClockCircleOutlined /> 申请中
            </a-tag>
            <a-tag v-else color="error">
              <CloseCircleOutlined /> 失败
            </a-tag>
          </template>

          <!-- 操作 -->
          <template v-if="column.key === 'action'">
            <a-popconfirm
              title="确定要删除该域名绑定？"
              @confirm="deleteDomain(record)"
            >
              <a-button type="link" danger size="small">
                <DeleteOutlined /> 删除
              </a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  GlobalOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { getAuthToken } from '@/utils/api'

const headers = { Authorization: `Bearer ${getAuthToken()}` }

// 主域名
const primaryDomain = ref('')

// 添加域名
const newDomain = ref('')
const addingDomain = ref(false)
const verifyingDns = ref(false)

// DNS 配置提示
const dnsConfig = reactive({
  visible: false,
  domain: '',
})

// 域名列表
const loading = ref(false)
const domainList = ref<any[]>([])

const columns = [
  { title: '域名', dataIndex: 'domain', key: 'domain' },
  { title: '验证状态', key: 'verifyStatus', width: 120 },
  { title: 'SSL 状态', key: 'sslStatus', width: 120 },
  { title: '操作', key: 'action', width: 100 },
]

// 加载域名列表
async function loadDomains() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/tenants/domains', { headers })
    const data = await res.json()
    const items = data.data?.domains || data.domains || []
    domainList.value = Array.isArray(items) ? items : []
    if (data.data?.primaryDomain) {
      primaryDomain.value = data.data.primaryDomain
    }
  } catch (e: any) {
    if (import.meta.env.DEV) console.error('加载域名列表失败', e)
  } finally {
    loading.value = false
  }
}

// 添加域名
async function addDomain() {
  const domain = newDomain.value.trim()
  if (!domain) {
    message.warning('请输入要绑定的域名')
    return
  }
  addingDomain.value = true
  try {
    const res = await fetch('/api/v1/tenants/domains', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ domain }),
    })
    const data = await res.json()
    if (res.ok) {
      message.success('域名已添加')
      newDomain.value = ''
      dnsConfig.visible = true
      dnsConfig.domain = domain
      await loadDomains()
    } else {
      message.error(data.message || '添加失败')
    }
  } catch (e: any) {
    message.error(e.message || '添加失败')
  } finally {
    addingDomain.value = false
  }
}

// 验证 DNS
async function verifyDns() {
  verifyingDns.value = true
  try {
    const domain = dnsConfig.domain || newDomain.value.trim()
    const res = await fetch('/api/v1/tenants/domains/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify({ domain }),
    })
    const data = await res.json()
    if (res.ok) {
      message.success('DNS 验证通过')
      await loadDomains()
    } else {
      message.error(data.message || '验证失败，请检查 DNS 配置是否正确')
    }
  } catch (e: any) {
    message.error(e.message || '验证请求失败')
  } finally {
    verifyingDns.value = false
  }
}

// 删除域名
async function deleteDomain(record: any) {
  try {
    const res = await fetch(`/api/v1/tenants/domains/${encodeURIComponent(record.domain || record.id)}`, {
      method: 'DELETE',
      headers,
    })
    if (res.ok) {
      message.success('域名已删除')
      await loadDomains()
    } else {
      const data = await res.json()
      message.error(data.message || '删除失败')
    }
  } catch (e: any) {
    message.error(e.message || '删除失败')
  }
}

onMounted(() => loadDomains())
</script>

<style scoped>
.dns-hint {
  margin-top: 1rem;
  padding: 1rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}
.dns-hint-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 0.75rem;
}
.dns-config-block {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
}
.dns-method h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 0.5rem;
}
.dns-table {
  border-collapse: collapse;
  width: 100%;
  max-width: 480px;
}
.dns-table td {
  padding: 0.35rem 0.75rem;
  border: 1px solid #e0f2fe;
  font-size: 0.82rem;
}
.dns-label {
  background: #e0f2fe;
  color: #0c4a6e;
  font-weight: 500;
  width: 100px;
}
.dns-value code {
  background: #f1f5f9;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.82rem;
  color: #0c4a6e;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
