<template>
  <YdPage title="AI 外贸团队" subtitle="B2B 专家角色 · 技能与边界说明" surface="elevated">
    <a-alert v-if="note" type="info" show-icon class="mb-4" :message="note" />
    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <div class="expert-grid">
        <article v-for="ex in experts" :key="ex.id" class="expert-card">
          <header class="expert-head">
            <span class="emoji">{{ ex.emoji || '🤖' }}</span>
            <div>
              <h2 class="name">{{ ex.name }}</h2>
              <p class="name-en">{{ ex.name_en }}</p>
            </div>
          </header>
          <p class="tagline">{{ ex.tagline }}</p>
          <div class="skills">
            <a-tag v-for="s in ex.skills || []" :key="s" color="blue">{{ skillLabel(s) }}</a-tag>
          </div>
          <p v-if="ex.must_show?.length" class="meta">
            须展示：{{ (ex.must_show as string[]).join(' · ') }}
          </p>
          <p v-if="ex.out_of_scope?.length" class="meta warn">
            不做：{{ (ex.out_of_scope as string[]).join(' · ') }}
          </p>
          <a-space wrap class="mt-2">
            <a-button size="small" type="primary" @click="askExpert(ex)">在副驾试用</a-button>
            <a-button v-if="ex.id === 'expert_diligence'" size="small" @click="goQueue">询盘背调</a-button>
          </a-space>
        </article>
      </div>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { fetchB2bExperts, type B2bExpert } from '@/api/foreign-trade'
import { skillLabel } from '@/constants/sales-assistant-brand'

const router = useRouter()
const loading = ref(true)
const note = ref('')
const experts = ref<B2bExpert[]>([])

onMounted(async () => {
  try {
    const data = await fetchB2bExperts()
    note.value = String(data.platform_note || '')
    experts.value = data.experts || []
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载专家库失败')
  } finally {
    loading.value = false
  }
})

const PROMPTS: Record<string, string> = {
  expert_eva: '找 8 家中东建材采购商',
  expert_letter: '为刚找到的采购商写 3 封开发信草稿',
  expert_negotiate: '客户压价 10% 怎么回应',
  expert_site: '分析官网 ICP',
  expert_matrix: '矩阵发布计划',
  expert_ads: 'Google 广告创意草稿',
  expert_research: '保温建材出口越南可行性',
  expert_crm: '给最新询盘打分',
  expert_diligence: '背调 buyer@example.com',
}

function askExpert(ex: B2bExpert) {
  const q = PROMPTS[ex.id] || `使用${ex.name}能力帮我`
  router.push({ path: '/client/copilot', query: { q } })
}

function goQueue() {
  router.push('/client/queues/inquiries')
}
</script>

<style scoped>
.expert-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.expert-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
}
.expert-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.emoji {
  font-size: 28px;
  line-height: 1;
}
.name {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #0f172a;
}
.name-en {
  font-size: 12px;
  color: #64748b;
  margin: 2px 0 0;
}
.tagline {
  font-size: 13px;
  color: #334155;
  margin: 12px 0 8px;
  line-height: 1.5;
}
.skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.meta {
  font-size: 12px;
  color: #64748b;
  margin-top: 10px;
  line-height: 1.45;
}
.meta.warn {
  color: #b45309;
}
</style>
