<template>
  <div class="message-input">
    <div class="input-toolbar">
      <a-tooltip title="技能包">
        <a-button 
          type="text" 
          :icon="h(RobotOutlined)" 
          @click="showSkillBar = !showSkillBar"
          :class="{ active: showSkillBar }"
        />
      </a-tooltip>
      <a-tooltip title="上传文件">
        <a-upload
          :before-upload="handleUpload"
          :show-upload-list="false"
          accept="image/*,.pdf,.doc,.docx,.txt"
        >
          <a-button type="text" :icon="h(PaperClipOutlined)" />
        </a-upload>
      </a-tooltip>
      <a-tooltip title="表情">
        <a-button type="text" :icon="h(SmileOutlined)" @click="showEmojiPicker = !showEmojiPicker" />
      </a-tooltip>
    </div>
    
    <div v-if="showSkillBar" class="skill-quick-bar">
      <SkillQuickBar @select="handleSkillSelect" />
    </div>
    
    <div class="input-container">
      <a-textarea
        v-model:value="inputValue"
        :placeholder="placeholder"
        :auto-size="{ minRows: 1, maxRows: 6 }"
        :disabled="disabled"
        @keydown="handleKeydown"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      
      <a-button
        type="primary"
        :icon="h(SendOutlined)"
        :loading="sending"
        :disabled="!canSend"
        @click="handleSend"
        class="send-btn"
      />
    </div>
    
    <div class="input-footer">
      <span class="char-count" :class="{ warning: charCount > 2000 }">
        {{ charCount }}/2000
      </span>
      <span class="hint">按 Enter 发送，Shift + Enter 换行</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, watch } from 'vue';
import SkillQuickBar from './SkillQuickBar.vue';
import {
  RobotOutlined,
  PaperClipOutlined,
  SmileOutlined,
  SendOutlined,
} from '@ant-design/icons-vue';

const props = defineProps<{
  placeholder?: string;
  disabled?: boolean;
  sending?: boolean;
}>();

const emit = defineEmits<{
  (e: 'send', content: string): void;
  (e: 'skill-select', skillId: string): void;
  (e: 'upload', file: File): void;
  (e: 'focus'): void;
  (e: 'blur'): void;
}>();

const inputValue = ref('');
const showSkillBar = ref(false);
const showEmojiPicker = ref(false);

const charCount = computed(() => inputValue.value.length);
const canSend = computed(() => {
  return inputValue.value.trim().length > 0 && 
         charCount.value <= 2000 && 
         !props.disabled && 
         !props.sending;
});

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    handleSend();
  }
}

function handleSend() {
  if (!canSend.value) return;
  
  const content = inputValue.value.trim();
  emit('send', content);
  inputValue.value = '';
}

function handleSkillSelect(skillId: string) {
  emit('skill-select', skillId);
  showSkillBar.value = false;
}

function handleUpload(file: File) {
  emit('upload', file);
  return false; // 阻止默认上传行为
}

function handleFocus() {
  emit('focus');
}

function handleBlur() {
  emit('blur');
}

// 监听输入值变化，提供给父组件访问
watch(inputValue, (value) => {
  // 可以在这里添加防抖逻辑
});

// 暴露方法给父组件
defineExpose({
  focus: () => {
    // 聚焦输入框
  },
  clear: () => {
    inputValue.value = '';
  },
  setValue: (value: string) => {
    inputValue.value = value;
  },
});
</script>

<style scoped>
.message-input {
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 12px 16px;
}

.input-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.input-toolbar .active {
  color: #1890ff;
  background: #e6f7ff;
}

.skill-quick-bar {
  margin-bottom: 12px;
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container :deep(.ant-input) {
  border-radius: 20px;
  padding: 12px 16px;
  resize: none;
  border-color: #d9d9d9;
  transition: all 0.3s;
}

.input-container :deep(.ant-input):hover {
  border-color: #40a9ff;
}

.input-container :deep(.ant-input):focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.send-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 8px;
}

.char-count {
  font-size: 12px;
  color: #8c8c8c;
}

.char-count.warning {
  color: #faad14;
}

.hint {
  font-size: 12px;
  color: #bfbfbf;
}

@media (max-width: 768px) {
  .message-input {
    padding: 8px 12px;
  }
  
  .input-toolbar {
    margin-bottom: 6px;
  }
  
  .input-footer {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
  }
}
</style>