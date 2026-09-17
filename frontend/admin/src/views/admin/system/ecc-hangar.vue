/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="ECC 专家机库" subtitle="Hermes 技术雷达 · 只读专家评审 · 不自动装依赖" surface="elevated">
    <template #actions>
      <a-space>
        <a-button :loading="loading" @click="load">刷新</a-button>
        <a-button type="primary" :loading="runningRadar" @click="runTechRadar">重跑技术雷达</a-button>
      </a-space>
    </template>

    <div v-if="meta" class="hangar-grid">
      <a-card size="small" title="门控状态">
        <a-descriptions :column="1" size="small">
          <a-descriptions-item label="专家数">{{ meta.roster_count }}</a-descriptions-item>
          <a-descriptions-item label="ECC 评审">
            <a-tag :color="meta.ecc_review_enabled ? 'green' : 'default'">
              {{ meta.ecc_review_enabled ? '开' : '关' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="LLM 深评">
            <a-tag :color="meta.llm_review_enabled ? 'green' : 'default'">
              {{ meta.llm_review_enabled ? '开' : '关' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
        <div v-if="meta.tech_radar_saved_at" class="hint">雷达快照：{{ meta.tech_radar_saved_at }}</div>
      </a-card>

      <a-card v-if="radarReports.length" size="small" title="雷达 Markdown 日报" class="wide">
        <a-list :data-source="radarReports" bordered size="small">
          <template #renderItem="{ item }">
            <a-list-item>
              <code>{{ item.path }}</code>
              <span class="hint ml-2">{{ item.bytes }} bytes</span>
            </a-list-item>
          </template>
        </a-list>
      </a-card>

      <a-card size="small" title="专家编制" class="wide">
        <a-list :data-source="meta.experts || []" bordered size="small">
          <template #renderItem="{ item }">
            <a-list-item>
              <strong>{{ item.display_name }}</strong>
              <span class="hint ml-2">{{ item.agent_id }} · {{ item.ecc_gate }}</span>
              <div class="hint">{{ (item.categories || []).join(', ') }}</div>
            </a-list-item>
          </template>
        </a-list>
      </a-card>

      <a-card size="small" title="最近 ECC 评审" class="wide">
        <a-list v-if="reviews.length" :data-source="reviews" bordered size="small">
          <template #renderItem="{ item }">
            <a-list-item>
              <div class="review-row">
                <div>
                  <a-tag v-if="item.impact === 'high'" color="red">高影响</a-tag>
                  <a-tag>{{ item.expert_verdict || '—' }}</a-tag>
                  <strong>{{ item.title }}</strong>
                </div>
                <div v-for="(r, i) in item.reviews || []" :key="i" class="hint">
                  {{ r.display_name }} · {{ r.verdict }} — {{ (r.recommendation || '').slice(0, 80) }}
                </div>
              </div>
            </a-list-item>
          </template>
        </a-list>
        <a-empty v-else description="尚无评审记录，请运行 Hermes 运维循环或技术雷达" />
      </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost } from '@/utils/api'

type Expert = { agent_id: string; display_name: string; ecc_gate: string; categories: string[] }
type ReviewItem = {
  title?: string
  impact?: string
  expert_verdict?: string
  reviews?: Array<{ display_name?: string; verdict?: string; recommendation?: string }>
}

const loading = ref(false)
const runningRadar = ref(false)
const snap = ref<Record<string, any> | null>(null)
const radarReports = ref<Array<{ path: string; bytes: number }>>([])

const meta = computed(() => snap.value?.ecc_hangar || snap.value)
const reviews = computed<ReviewItem[]>(() => meta.value?.recent_reviews || [])

async function load() {
  loading.value = true
  try {
    snap.value = await apiGet('/hermes/ops/command-center')
    const rep = await apiGet<{ data?: { reports?: Array<{ path: string; bytes: number }> } }>(
      '/hermes/ops/tech-radar/reports?limit=7',
    )
    radarReports.value = (rep as { data?: { reports?: Array<{ path: string; bytes: number }> } }).data?.reports || []
  } catch (e: unknown) {
    message.error((e as Error)?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function runTechRadar() {
  runningRadar.value = true
  try {
    await apiPost('/hermes/ops/instruct', { command: 'rerun_tech_radar' })
    message.success('技术雷达已触发')
    await load()
  } catch (e: unknown) {
    message.error((e as Error)?.message || '触发失败')
  } finally {
    runningRadar.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.hangar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.wide {
  grid-column: 1 / -1;
}
.hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 6px;
}
.review-row {
  width: 100%;
}
</style>
