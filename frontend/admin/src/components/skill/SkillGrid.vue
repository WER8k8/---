<template>
  <div class="skill-grid">
    <div class="grid-header">
      <h3 class="grid-title">{{ title }}</h3>
      <div class="grid-actions">
        <a-input-search
          v-if="showSearch"
          v-model:value="searchQuery"
          placeholder="搜索技能包..."
          allow-clear
          style="width: 200px"
        />
        <a-select
          v-if="showCategoryFilter"
          v-model:value="selectedCategory"
          placeholder="分类筛选"
          style="width: 120px"
          allow-clear
        >
          <a-select-option value="accio_work">卖货执行</a-select-option>
          <a-select-option value="deer_flow">市场研究</a-select-option>
        </a-select>
      </div>
    </div>
    
    <div class="grid-content">
      <template v-if="loading">
        <SkeletonCard variant="card" />
      </template>
      <template v-else>
        <div class="skills-container">
          <SkillCard
            v-for="skill in filteredSkills"
            :key="skill.id"
            :skill="skill"
            @click="handleSkillClick"
            @execute="handleSkillExecute"
            @favorite="handleSkillFavorite"
          />
        </div>
        
        <a-empty v-if="filteredSkills.length === 0" description="暂无技能包">
          <template #image>
            <AppstoreOutlined style="font-size: 48px; color: #bfbfbf" />
          </template>
        </a-empty>
      </template>
    </div>
    
    <div v-if="showPagination && total > pageSize" class="grid-footer">
      <a-pagination
        v-model:current="currentPage"
        :total="total"
        :page-size="pageSize"
        :show-size-changer="false"
        :show-total="(total: number) => `共 ${total} 个技能包`"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useRouter } from 'vue-router';
import { useSkillStore } from '@/stores/skill';
import SkillCard from './SkillCard.vue';
import { AppstoreOutlined } from '@ant-design/icons-vue';
import type { Skill } from '@/types/skill';

const props = withDefaults(defineProps<{
  skills?: Skill[];
  title?: string;
  showSearch?: boolean;
  showCategoryFilter?: boolean;
  showPagination?: boolean;
  loading?: boolean;
  pageSize?: number;
}>(), {
  skills: () => [],
  title: '技能包',
  showSearch: true,
  showCategoryFilter: true,
  showPagination: true,
  loading: false,
  pageSize: 12,
});

const emit = defineEmits<{
  (e: 'click', skillId: string): void;
  (e: 'execute', skillId: string): void;
  (e: 'favorite', skillId: string): void;
  (e: 'page-change', page: number): void;
}>();

const router = useRouter();
const skillStore = useSkillStore();

const searchQuery = ref('');
const selectedCategory = ref<string | undefined>(undefined);
const currentPage = ref(1);

const displaySkills = computed(() => {
  return props.skills.length > 0 ? props.skills : skillStore.skills;
});

const filteredSkills = computed(() => {
  let result = displaySkills.value;
  
  // 按分类筛选
  if (selectedCategory.value) {
    result = result.filter(skill => skill.category === selectedCategory.value);
  }
  
  // 按搜索词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(skill =>
      skill.name.toLowerCase().includes(query) ||
      skill.description.toLowerCase().includes(query)
    );
  }
  
  // 分页
  if (props.showPagination) {
    const start = (currentPage.value - 1) * props.pageSize;
    const end = start + props.pageSize;
    result = result.slice(start, end);
  }
  
  return result;
});

const total = computed(() => displaySkills.value.length);

watch([searchQuery, selectedCategory], () => {
  currentPage.value = 1;
});

function handleSkillClick(skillId: string) {
  emit('click', skillId);
  router.push(`/skill/${skillId}`);
}

function handleSkillExecute(skillId: string) {
  emit('execute', skillId);
  skillStore.markSkillExecuting(skillId);
}

function handleSkillFavorite(skillId: string) {
  emit('favorite', skillId);
}

function handlePageChange(page: number) {
  currentPage.value = page;
  emit('page-change', page);
}
</script>

<style scoped>
.skill-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.grid-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.grid-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.grid-actions {
  display: flex;
  gap: 12px;
}

.grid-content {
  min-height: 200px;
}

.skills-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.grid-footer {
  display: flex;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .grid-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .grid-actions {
    flex-direction: column;
  }
  
  .skills-container {
    grid-template-columns: 1fr;
  }
}
</style>