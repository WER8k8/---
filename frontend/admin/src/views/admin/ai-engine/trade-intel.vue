<template>
  <YdPage title="出海参谋" subtitle="规则矩阵 · 蓝海 + 海关试点（M0/M1/M2）" surface="elevated">
    <template #actions>
      <a-button type="primary" size="small" :disabled="loading" @click="runSeed">同步种子</a-button>
      <a-button size="small" :disabled="loading" @click="loadRules">刷新列表</a-button>
      <a-button size="small" :disabled="loading" @click="previewBlueOcean">蓝海+海关试点</a-button>
      <a-button size="small" :disabled="loading" @click="previewCommercial">M2 商业数据</a-button>
      <a-button size="small" :disabled="loading" @click="runComtradeRefresh">Comtrade 刷新</a-button>
    </template>

    <div class="trade-intel-page">
    <p v-if="matrixStats" class="text-xs text-gray-500 mb-1">
      矩阵规模：{{ matrixStats.matrix_spec }}（共 {{ matrixStats.total_rows }} 条规则种子）
    </p>
    <p v-if="refreshSnapshot?.saved_at" class="text-xs text-gray-500 mb-3">
      海关抓取：{{ refreshSnapshot.saved_at }} · 更新 {{ refreshSnapshot.rows_updated ?? 0 }} 条
      <span v-if="refreshSnapshot.years">（{{ refreshSnapshot.years.new }}/{{ refreshSnapshot.years.old }}）</span>
    </p>
    <div v-if="blueOceanPreview" class="mb-4 p-3 border rounded-xl bg-gray-50 text-sm">
      <p class="font-medium mb-1">蓝海 Top3（含 M1 海关字段）</p>
      <ul class="list-disc pl-5 space-y-1">
        <li v-for="(r, i) in blueOceanPreview.recommendations || []" :key="i">
          {{ r.country_code }} — {{ r.verdict || r.reason }}
          <span v-if="r.customs_export_index != null" class="text-gray-600">
            · 出口指数 {{ r.customs_export_index }}（{{ r.customs_source || '试点' }}）
          </span>
        </li>
      </ul>
      <p v-if="blueOceanPreview.disclaimer || blueOceanPreview.customs_m1" class="text-xs text-gray-500 mt-2">
        对外宣传须人工复核；数据为公开统计试点。
      </p>
    </div>
    <div v-if="commercialPreview" class="mb-4 p-3 border rounded-xl bg-blue-50 text-sm">
      <p class="font-medium mb-1">M2 商业海关 · {{ commercialPreview.mode }}</p>
      <p class="text-xs text-gray-600 mb-2">
        已配置外部 API：{{ commercialPreview.m2_configured ? '是' : '否（回退 M1）' }}
        <span v-if="commercialPreview.m2_error"> · {{ commercialPreview.m2_error }}</span>
      </p>
      <ul class="list-disc pl-5 space-y-1">
        <li v-for="(r, i) in (commercialPreview.rows || []).slice(0, 5)" :key="i">
          {{ typeof r === 'object' ? JSON.stringify(r) : r }}
        </li>
      </ul>
    </div>
    <p v-if="message" class="text-sm mb-2" :class="ok ? 'text-green-600' : 'text-red-600'">{{ message }}</p>
    <div class="overflow-x-auto border rounded-xl">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left">品类</th>
            <th class="px-3 py-2 text-left">国家</th>
            <th class="px-3 py-2 text-left">结论</th>
            <th class="px-3 py-2 text-left">增速</th>
            <th class="px-3 py-2 text-left">HS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id" class="border-t">
            <td class="px-3 py-2">{{ r.category_label }}</td>
            <td class="px-3 py-2">{{ r.country_code }}</td>
            <td class="px-3 py-2">{{ r.verdict }}</td>
            <td class="px-3 py-2">{{ r.growth }}</td>
            <td class="px-3 py-2">{{ r.hs_chapter }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!rules.length && !loading" class="p-4 text-gray-400 text-center">暂无数据，请先同步种子并执行迁移 023</p>
    </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const rules = ref<any[]>([])
interface BlueOceanRec {
  country_code?: string
  verdict?: string
  reason?: string
  customs_export_index?: number
  customs_source?: string
}
const blueOceanPreview = ref<{ recommendations?: BlueOceanRec[]; disclaimer?: string; customs_m1?: unknown } | null>(null)
const commercialPreview = ref<{ mode?: string; rows?: unknown[]; m2_configured?: boolean; m2_error?: string } | null>(null)
const loading = ref(false)
const message = ref('')
const ok = ref(true)
const matrixStats = ref<{ matrix_spec?: string; total_rows?: number } | null>(null)
const refreshSnapshot = ref<{ saved_at?: string; rows_updated?: number; years?: { new?: number; old?: number } } | null>(null)

function headers(): Record<string, string> {
  const tk = getAuthToken()
  return tk ? { Authorization: `Bearer ${tk}` } : {}
}

async function loadRefreshStatus() {
  try {
    const res = await fetch('/api/v1/ops/trade-intel/status', { headers: headers() })
    const body = await res.json()
    if (res.ok) refreshSnapshot.value = body.data?.latest || null
  } catch {
    refreshSnapshot.value = null
  }
}

async function runComtradeRefresh() {
  loading.value = true
  message.value = ''
  try {
    const res = await fetch('/api/v1/ops/trade-intel/refresh', {
      method: 'POST',
      headers: headers(),
    })
    const body = await res.json()
    ok.value = res.ok
    if (res.ok) {
      refreshSnapshot.value = body.data || null
      message.value = `Comtrade 已刷新：更新 ${body.data?.rows_updated ?? 0} 条`
      await loadMatrixStats()
    } else {
      message.value = body.message || '刷新失败'
    }
  } catch {
    message.value = '刷新请求失败'
    ok.value = false
  } finally {
    loading.value = false
  }
}

async function loadMatrixStats() {
  try {
    const res = await fetch('/api/v1/trade-intel/matrix-stats', { headers: headers() })
    const body = await res.json()
    if (res.ok) matrixStats.value = body.data || null
  } catch {
    matrixStats.value = null
  }
}

async function loadRules() {
  loading.value = true
  message.value = ''
  try {
    const res = await fetch('/api/v1/trade-intel/rules', { headers: headers() })
    const body = await res.json()
    rules.value = body.data || []
    ok.value = res.ok
    if (!res.ok) message.value = body.message || '加载失败'
  } catch {
    message.value = '网络错误'
    ok.value = false
  } finally {
    loading.value = false
  }
}

async function previewBlueOcean() {
  loading.value = true
  blueOceanPreview.value = null
  try {
    const res = await fetch(
      '/api/v1/trade-intel/blue-ocean?category=insulation_board&message=保温板',
      { headers: headers() },
    )
    const body = await res.json()
    if (res.ok) blueOceanPreview.value = body.data || null
    else {
      ok.value = false
      message.value = body.message || '蓝海预览失败'
    }
  } catch {
    message.value = '蓝海预览网络错误'
    ok.value = false
  } finally {
    loading.value = false
  }
}

async function previewCommercial() {
  loading.value = true
  commercialPreview.value = null
  try {
    const res = await fetch('/api/v1/trade-intel/commercial-stats?category=insulation_board', {
      headers: headers(),
    })
    const body = await res.json()
    if (res.ok) commercialPreview.value = body.data || null
    else {
      ok.value = false
      message.value = body.message || 'M2 预览失败'
    }
  } catch {
    message.value = 'M2 预览网络错误'
    ok.value = false
  } finally {
    loading.value = false
  }
}

async function runSeed() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/trade-intel/rules/seed', {
      method: 'POST',
      headers: headers(),
    })
    const body = await res.json()
    ok.value = res.ok
    message.value = res.ok
      ? `已同步：新建 ${body.data?.created ?? 0}，更新 ${body.data?.updated ?? 0}`
      : body.message || '同步失败'
    if (res.ok) await loadRules()
  } catch {
    message.value = '同步请求失败'
    ok.value = false
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMatrixStats()
  loadRefreshStatus()
  loadRules()
})
</script>
