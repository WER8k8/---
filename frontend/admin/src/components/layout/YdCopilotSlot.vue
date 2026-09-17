/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <aside
    class="yd-copilot-slot"
    :class="[
      `yd-copilot-slot--${currentDock}`,
      { open: props.open }
    ]"
    aria-label="AI 智能副驾"
  >
    <header class="yd-copilot-slot__head">
      <div class="yd-copilot-slot__title">
        <RobotOutlined />
        <span>出海 AI 智能副驾</span>
        <span class="yd-copilot-slot__badge">自适应</span>
      </div>
      <div class="yd-copilot-slot__actions">
        <button
          type="button"
          class="yd-copilot-slot__btn"
          :title="currentDock === 'left' ? '切换为右侧停靠' : '切换为左侧自适应'"
          @click="toggleDock"
        >
          <SwapOutlined />
        </button>
        <button
          type="button"
          class="yd-copilot-slot__close"
          aria-label="关闭"
          @click="emit('update:open', false)"
        >
          ×
        </button>
      </div>
    </header>

    <div class="yd-copilot-slot__body">
      <slot>
        <div class="yd-copilot-slot__banner">
          <p class="yd-copilot-slot__hint">
            <strong>外贸 AI 智能副驾</strong> · 100 种性格客情洞察、千种场景秒级响应、询盘翻译与 PI 单证自动套算
          </p>
        </div>

        <!-- 外贸专属自适应快捷卡片 -->
        <div class="yd-copilot-quick-grid">
          <button type="button" class="quick-card" @click="handleQuickAction('inquiry')">
            <span class="quick-icon">🌐</span>
            <div class="quick-text">
              <span class="quick-title">询盘多语言翻译</span>
              <span class="quick-desc">阿语/西语/俄语精准意图提取</span>
            </div>
          </button>

          <button type="button" class="quick-card" @click="handleQuickAction('quote')">
            <span class="quick-icon">📊</span>
            <div class="quick-text">
              <span class="quick-title">BOQ 22 参数核价</span>
              <span class="quick-desc">集装箱配载与定金自动折算</span>
            </div>
          </button>

          <button type="button" class="quick-card" @click="handleQuickAction('pi')">
            <span class="quick-icon">📑</span>
            <div class="quick-text">
              <span class="quick-title">PI / CI 单证生成</span>
              <span class="quick-desc">7 步履约单证一键套打</span>
            </div>
          </button>

          <button type="button" class="quick-card" @click="handleQuickAction('sentiment')">
            <span class="quick-icon">🎯</span>
            <div class="quick-text">
              <span class="quick-title">买家情绪与谈判策略</span>
              <span class="quick-desc">100 种脾气多轮应策建议</span>
            </div>
          </button>
        </div>

        <div class="yd-copilot-slot__footer">
          <a-button type="primary" block @click="goAssistant">
            打开完整外贸 AI 工作台
          </a-button>
        </div>
      </slot>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { RobotOutlined, SwapOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';
import { useAdaptiveCopilotDock, type CopilotDockPosition } from '@/composables/useAdaptiveLayout';

const props = withDefaults(
  defineProps<{
    open: boolean;
    dock?: CopilotDockPosition;
  }>(),
  {
    dock: undefined,
  },
);

const emit = defineEmits<{
  'update:open': [value: boolean];
  'update:dock': [value: CopilotDockPosition];
}>();

const router = useRouter();
const copilotDockStore = useAdaptiveCopilotDock();

// 优先使用传入的 prop，否则使用全局持久化的 dock 状态（默认 'left'）
const currentDock = ref<CopilotDockPosition>(props.dock || copilotDockStore.dock.value);

watch(
  () => props.dock,
  (newDock) => {
    if (newDock) {
      currentDock.value = newDock;
    }
  },
);

watch(
  () => copilotDockStore.dock.value,
  (newDock) => {
    if (!props.dock) {
      currentDock.value = newDock;
    }
  },
);

function toggleDock() {
  copilotDockStore.toggleDock();
  currentDock.value = copilotDockStore.dock.value;
  emit('update:dock', currentDock.value);
}

function handleQuickAction(actionKey: string) {
  const target = `/client/assistant?action=${actionKey}`;
  void router.push(target);
  emit('update:open', false);
}

function goAssistant() {
  const target = '/client/assistant';
  void router.push(target);
  emit('update:open', false);
}
</script>

<style scoped lang="scss">
.yd-copilot-slot {
  position: fixed;
  top: 0;
  width: min(calc(380px * var(--uj-adaptive-scale, 1)), 92vw);
  max-width: 92vw;
  height: 100vh;
  background: var(--uj-bg-card, #ffffff);
  z-index: 120;
  transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

/* 左出模式（左侧自适应滑出） */
.yd-copilot-slot--left {
  left: 0;
  right: auto;
  border-right: 1px solid var(--uj-border, #e2e8f0);
  box-shadow: 8px 0 32px rgba(15, 23, 42, 0.12);
  transform: translateX(-100%);
}
.yd-copilot-slot--left.open {
  transform: translateX(0);
}

/* 右出模式（右侧滑出） */
.yd-copilot-slot--right {
  right: 0;
  left: auto;
  border-left: 1px solid var(--uj-border, #e2e8f0);
  box-shadow: -8px 0 32px rgba(15, 23, 42, 0.12);
  transform: translateX(100%);
}
.yd-copilot-slot--right.open {
  transform: translateX(0);
}

/* RTL 阿拉伯语/希伯来语排版镜像适配 */
[dir="rtl"] .yd-copilot-slot--left {
  left: auto;
  right: 0;
  border-right: none;
  border-left: 1px solid var(--uj-border, #e2e8f0);
  box-shadow: -8px 0 32px rgba(15, 23, 42, 0.12);
  transform: translateX(100%);
}
[dir="rtl"] .yd-copilot-slot--left.open {
  transform: translateX(0);
}

[dir="rtl"] .yd-copilot-slot--right {
  right: auto;
  left: 0;
  border-left: none;
  border-right: 1px solid var(--uj-border, #e2e8f0);
  box-shadow: 8px 0 32px rgba(15, 23, 42, 0.12);
  transform: translateX(-100%);
}
[dir="rtl"] .yd-copilot-slot--right.open {
  transform: translateX(0);
}

.yd-copilot-slot__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--uj-border, #e2e8f0);
  background: var(--uj-bg-card, #ffffff);
}

.yd-copilot-slot__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: calc(14px * var(--uj-adaptive-scale, 1));
}

.yd-copilot-slot__badge {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 10px;
  background: #e8f5f1;
  color: #4a9b8c;
}

.yd-copilot-slot__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.yd-copilot-slot__btn {
  border: none;
  background: transparent;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s ease;
}
.yd-copilot-slot__btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #0f172a;
}

.yd-copilot-slot__close {
  border: none;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  color: #94a3b8;
  padding: 0 4px;
}
.yd-copilot-slot__close:hover {
  color: #0f172a;
}

.yd-copilot-slot__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.yd-copilot-slot__banner {
  padding: 12px 14px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.yd-copilot-slot__hint {
  font-size: calc(12px * var(--uj-adaptive-scale, 1));
  color: #475569;
  line-height: 1.5;
  margin: 0;
}

.yd-copilot-quick-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-card:hover {
  border-color: #4a9b8c;
  background: #f0fdf4;
  transform: translateY(-1px);
}

.quick-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.quick-text {
  display: flex;
  flex-direction: column;
}

.quick-title {
  font-size: calc(13px * var(--uj-adaptive-scale, 1));
  font-weight: 600;
  color: #0f172a;
}

.quick-desc {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.yd-copilot-slot__footer {
  margin-top: auto;
  padding-top: 12px;
}

/* 超小屏全屏滑出 */
@media (max-width: 480px) {
  .yd-copilot-slot {
    width: 100vw;
    max-width: 100vw;
  }
}
</style>
