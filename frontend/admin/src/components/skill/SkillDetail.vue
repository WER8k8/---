/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="skill-detail">
    <div class="skill-header">
      <div class="skill-icon" :style="{ backgroundColor: skillColor }">
        <component :is="skillIcon" />
      </div>
      <div class="skill-info">
        <h2 class="skill-name">{{ skill.name }}</h2>
        <div class="skill-meta">
          <a-tag :color="categoryColor">{{ categoryText }}</a-tag>
          <a-tag v-if="skill.isCore" color="blue">核心技能</a-tag>
        </div>
      </div>
    </div>
    
    <div class="skill-description">
      <h3>技能描述</h3>
      <p>{{ skill.description }}</p>
    </div>
    
    <div class="skill-parameters" v-if="skill.parameters && skill.parameters.length > 0">
      <h3>参数配置</h3>
      <a-form
        :model="formState"
        layout="vertical"
        @finish="handleExecute"
      >
        <a-form-item
          v-for="param in skill.parameters"
          :key="param.name"
          :label="param.name"
          :name="param.name"
          :rules="[{ required: param.required, message: `请输入${param.name}` }]"
        >
          <a-input
            v-if="param.type === 'string'"
            v-model:value="formState[param.name]"
            :placeholder="param.description"
          />
          <a-input-number
            v-else-if="param.type === 'number'"
            v-model:value="formState[param.name]"
            :placeholder="param.description"
            style="width: 100%"
          />
          <a-switch
            v-else-if="param.type === 'boolean'"
            v-model:checked="formState[param.name]"
          />
          <a-upload
            v-else-if="param.type === 'file'"
            v-model:file-list="fileList[param.name]"
            :before-upload="() => false"
          >
            <a-button>
              <UploadOutlined />
              选择文件
            </a-button>
          </a-upload>
          <div class="param-description">{{ param.description }}</div>
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="executing" block>
            <CaretRightOutlined />
            执行技能包
          </a-button>
        </a-form-item>
      </a-form>
    </div>
    
    <div class="skill-actions" v-else>
      <a-button type="primary" :loading="executing" @click="handleExecute" block>
        <CaretRightOutlined />
        执行技能包
      </a-button>
    </div>
    
    <div class="skill-history">
      <h3>执行历史</h3>
      <a-list
        :data-source="executionHistory"
        :loading="loadingHistory"
      >
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <span>{{ formatDate(item.executedAt) }}</span>
                <a-tag :color="item.success ? 'success' : 'error'">
                  {{ item.success ? '成功' : '失败' }}
                </a-tag>
              </template>
              <template #description>
                <span>执行时间: {{ item.executionTime }}ms</span>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, h } from 'vue';
import { useSkill } from '@/composables/useSkill';
import { formatDate } from '@/utils/index';
import {
  RobotOutlined,
  SearchOutlined,
  MailOutlined,
  BarChartOutlined,
  FileSearchOutlined,
  CaretRightOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';
import type { Skill, SkillParameter } from '@/types/skill';

const props = defineProps<{
  skill: Skill;
}>();

const emit = defineEmits<{
  (e: 'execute', skillId: string, parameters: Record<string, any>): void;
}>();

const { executeSkill, getSkillExecutions } = useSkill();

const executing = ref(false);
const loadingHistory = ref(false);
const executionHistory = ref<any[]>([]);
const formState = reactive<Record<string, any>>({});
const fileList = ref<Record<string, any[]>>({});

const skillIcon = computed(() => {
  const iconMap: Record<string, any> = {
    'auto_negotiate': RobotOutlined,
    'deep_research': SearchOutlined,
    'email_draft': MailOutlined,
    'customer_analysis': BarChartOutlined,
    'document_review': FileSearchOutlined,
  };
  return iconMap[props.skill.id] || RobotOutlined;
});

const skillColor = computed(() => {
  const colorMap: Record<string, string> = {
    'auto_negotiate': '#1890ff',
    'deep_research': '#52c41a',
    'email_draft': '#faad14',
    'customer_analysis': '#722ed1',
    'document_review': '#eb2f96',
  };
  return colorMap[props.skill.id] || '#1890ff';
});

const categoryColor = computed(() => {
  return props.skill.category === 'accio_work' ? 'blue' : 'green';
});

const categoryText = computed(() => {
  return props.skill.category === 'accio_work' ? '卖货执行' : '市场研究'
})

async function handleExecute() {
  executing.value = true;
  
  try {
    const parameters = { ...formState };
    
    // 处理文件参数
    for (const [key, files] of Object.entries(fileList.value)) {
      if (files && files.length > 0) {
        parameters[key] = files[0].originFileObj;
      }
    }
    
    emit('execute', props.skill.id, parameters);
  } catch (error) {
    console.error('执行技能包失败:', error);
  } finally {
    executing.value = false;
  }
}

async function loadExecutionHistory() {
  loadingHistory.value = true;
  
  try {
    const response = await getSkillExecutions(props.skill.id);
    executionHistory.value = response.executions;
  } catch (error) {
    console.error('加载执行历史失败:', error);
  } finally {
    loadingHistory.value = false;
  }
}
</script>

<style scoped>
.skill-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.skill-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.skill-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  flex-shrink: 0;
}

.skill-info {
  flex: 1;
}

.skill-name {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.skill-meta {
  display: flex;
  gap: 8px;
}

.skill-description h3,
.skill-parameters h3,
.skill-history h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.skill-description p {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
  line-height: 1.6;
}

.param-description {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.skill-actions {
  margin-top: 16px;
}

.skill-history {
  border-top: 1px solid #f0f0f0;
  padding-top: 24px;
}
</style>