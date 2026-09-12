<template>
  <div class="skill-quick-bar">
    <div class="skill-list">
      <div
        v-for="skill in quickSkills"
        :key="skill.id"
        class="skill-item"
        @click="selectSkill(skill.id)"
      >
        <div class="skill-icon" :style="{ backgroundColor: skill.color }">
          <component :is="skill.icon" />
        </div>
        <div class="skill-info">
          <div class="skill-name">{{ skill.name }}</div>
          <div class="skill-desc">{{ skill.description }}</div>
        </div>
      </div>
    </div>
    
    <div class="skill-actions">
      <a-button type="link" size="small" @click="viewAllSkills">
        查看全部技能包
        <RightOutlined />
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, h } from 'vue';
import { useRouter } from 'vue-router';
import {
  RobotOutlined,
  SearchOutlined,
  MailOutlined,
  FileSearchOutlined,
  BarChartOutlined,
  RightOutlined,
} from '@ant-design/icons-vue';

const emit = defineEmits<{
  (e: 'select', skillId: string): void;
}>();

const router = useRouter();

interface QuickSkill {
  id: string;
  name: string;
  description: string;
  icon: any;
  color: string;
}

const quickSkills = ref<QuickSkill[]>([
  {
    id: 'auto_negotiate',
    name: '自动谈单',
    description: '智能客户沟通与转化',
    icon: RobotOutlined,
    color: '#1890ff',
  },
  {
    id: 'deep_research',
    name: '深度研究',
    description: '全面市场与竞品分析',
    icon: SearchOutlined,
    color: '#52c41a',
  },
  {
    id: 'email_draft',
    name: '邮件撰写',
    description: '专业商务邮件生成',
    icon: MailOutlined,
    color: '#faad14',
  },
  {
    id: 'customer_analysis',
    name: '客户分析',
    description: '客户画像与行为分析',
    icon: BarChartOutlined,
    color: '#722ed1',
  },
  {
    id: 'document_review',
    name: '文档审阅',
    description: '合同与文档智能审阅',
    icon: FileSearchOutlined,
    color: '#eb2f96',
  },
]);

function selectSkill(skillId: string) {
  emit('select', skillId);
}

function viewAllSkills() {
  router.push('/agent-hub/dashboard');
}
</script>

<style scoped>
.skill-quick-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px 0;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 180px;
  flex-shrink: 0;
}

.skill-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.skill-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  flex-shrink: 0;
}

.skill-info {
  flex: 1;
  min-width: 0;
}

.skill-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 2px;
}

.skill-desc {
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skill-actions {
  text-align: right;
}

@media (max-width: 768px) {
  .skill-list {
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  
  .skill-item {
    min-width: 150px;
  }
}
</style>