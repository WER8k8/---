<template>
  <div class="skill-card" @click="handleClick">
    <div class="skill-icon" :style="{ backgroundColor: skillColor }">
      <component :is="skillIcon" />
    </div>
    
    <div class="skill-content">
      <div class="skill-header">
        <h4 class="skill-name">{{ skillName }}</h4>
        <a-tag v-if="isCore" color="blue">核心</a-tag>
      </div>
      
      <p class="skill-description">{{ skillDescription }}</p>
      
      <div class="skill-footer">
        <div class="skill-category">
          <a-tag :color="categoryColor">{{ categoryText }}</a-tag>
        </div>
        
        <div class="skill-actions">
          <a-tooltip title="收藏">
            <a-button 
              type="text" 
              size="small" 
              :icon="h(isFavorited ? StarFilled : StarOutlined)"
              :class="{ favorited: isFavorited }"
              @click.stop="toggleFavorite"
            />
          </a-tooltip>
          <a-tooltip title="执行">
            <a-button 
              type="primary" 
              size="small" 
              :icon="h(CaretRightOutlined)"
              :loading="isExecuting"
              @click.stop="executeSkill"
            />
          </a-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue';
import { useSkillStore } from '@/stores/skill';
import {
  StarOutlined,
  StarFilled,
  CaretRightOutlined,
  RobotOutlined,
  SearchOutlined,
  MailOutlined,
  BarChartOutlined,
  FileSearchOutlined,
} from '@ant-design/icons-vue';
import type { Skill } from '@/types/skill';

const props = defineProps<{
  skill: Skill | null;
}>();

const emit = defineEmits<{
  (e: 'click', skillId: string): void;
  (e: 'execute', skillId: string): void;
  (e: 'favorite', skillId: string): void;
}>();

const skillStore = useSkillStore();

const isFavorited = ref(false);
const isExecuting = ref(false);

const skillData = computed(() => {
  if (props.skill) return props.skill;
  return null;
});

const skillName = computed(() => skillData.value?.name || '未知技能');
const skillDescription = computed(() => skillData.value?.description || '暂无描述');
const isCore = computed(() => skillData.value?.isCore || false);
const category = computed(() => skillData.value?.category || 'accio_work');

const skillIcon = computed(() => {
  const iconMap: Record<string, any> = {
    'auto_negotiate': RobotOutlined,
    'deep_research': SearchOutlined,
    'email_draft': MailOutlined,
    'customer_analysis': BarChartOutlined,
    'document_review': FileSearchOutlined,
  };
  return iconMap[skillData.value?.id || ''] || RobotOutlined;
});

const skillColor = computed(() => {
  const colorMap: Record<string, string> = {
    'auto_negotiate': '#1890ff',
    'deep_research': '#52c41a',
    'email_draft': '#faad14',
    'customer_analysis': '#722ed1',
    'document_review': '#eb2f96',
  };
  return colorMap[skillData.value?.id || ''] || '#1890ff';
});

const categoryColor = computed(() => {
  return category.value === 'accio_work' ? 'blue' : 'green';
});

const categoryText = computed(() => {
  return category.value === 'accio_work' ? '卖货执行' : '市场研究'
})

function handleClick() {
  if (skillData.value) {
    emit('click', skillData.value.id);
  }
}

function executeSkill() {
  if (skillData.value) {
    isExecuting.value = true;
    emit('execute', skillData.value.id);
    setTimeout(() => {
      isExecuting.value = false;
    }, 2000);
  }
}

function toggleFavorite() {
  isFavorited.value = !isFavorited.value;
  if (skillData.value) {
    emit('favorite', skillData.value.id);
  }
}
</script>

<style scoped>
.skill-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s;
}

.skill-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
}

.skill-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  flex-shrink: 0;
}

.skill-content {
  flex: 1;
  min-width: 0;
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.skill-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.skill-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.skill-category {
  flex: 1;
}

.skill-actions {
  display: flex;
  gap: 8px;
}

.favorited {
  color: #faad14;
}

@media (max-width: 768px) {
  .skill-card {
    padding: 12px;
    gap: 12px;
  }
  
  .skill-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .skill-name {
    font-size: 14px;
  }
  
  .skill-description {
    font-size: 12px;
  }
}
</style>