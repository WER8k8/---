/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="app-tabs">
    <div class="tabs-container">
      <!-- 左侧滚动按钮 -->
      <div class="scroll-btn scroll-left" v-if="showScrollBtn" @click="scrollLeft">
        <LeftOutlined />
      </div>

      <!-- 标签页列表 -->
      <div class="tabs-wrapper" ref="tabsWrapperRef">
        <div class="tabs-list" ref="tabsListRef">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeKey === tab.key, closable: !tab.affix }"
            @click="switchTab(tab)"
            @contextmenu.prevent="showContextMenu($event, tab)"
          >
            <component :is="tab.icon" v-if="tab.icon" class="tab-icon" />
            <span class="tab-title">{{ tab.title }}</span>
            <CloseOutlined
              v-if="!tab.affix"
              class="tab-close"
              @click.stop="closeTab(tab)"
            />
          </div>
        </div>
      </div>

      <!-- 右侧滚动按钮 -->
      <div class="scroll-btn scroll-right" v-if="showScrollBtn" @click="scrollRight">
        <RightOutlined />
      </div>

      <!-- 更多操作 -->
      <div class="tabs-actions">
        <a-dropdown :trigger="['click']">
          <div class="action-btn">
            <EllipsisOutlined />
          </div>
          <template #overlay>
            <a-menu @click="handleAction as any">
              <a-menu-item key="closeOther">
                <CloseOutlined /> 关闭其他
              </a-menu-item>
              <a-menu-item key="closeLeft">
                <VerticalRightOutlined /> 关闭左侧
              </a-menu-item>
              <a-menu-item key="closeRight">
                <VerticalLeftOutlined /> 关闭右侧
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="closeAll">
                <StopOutlined /> 关闭全部
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 右键菜单 -->
    <a-menu
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{
        position: 'fixed',
        zIndex: 1000,
        left: contextMenu.x + 'px',
        top: contextMenu.y + 'px'
      }"
      @click="handleContextAction as any"
    >
      <a-menu-item key="refresh">
        <ReloadOutlined /> 刷新
      </a-menu-item>
      <a-menu-item key="close" :disabled="contextMenu.tab?.affix">
        <CloseOutlined /> 关闭
      </a-menu-item>
      <a-menu-item key="closeOther">
        <CloseOutlined /> 关闭其他
      </a-menu-item>
      <a-menu-item key="closeLeft">
        <VerticalRightOutlined /> 关闭左侧
      </a-menu-item>
      <a-menu-item key="closeRight">
        <VerticalLeftOutlined /> 关闭右侧
      </a-menu-item>
    </a-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  CloseOutlined,
  LeftOutlined,
  RightOutlined,
  EllipsisOutlined,
  ReloadOutlined,
  VerticalRightOutlined,
  VerticalLeftOutlined,
  StopOutlined
} from '@ant-design/icons-vue'

// 标签页定义
export interface AppTab {
  key: string
  title: string
  path: string
  icon?: any
  affix?: boolean
  query?: Record<string, any>
}

// Props
interface Props {
  tabs: AppTab[]
  activeKey: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'change', key: string): void
  (e: 'close', key: string): void
  (e: 'close-other', key: string): void
  (e: 'close-left', key: string): void
  (e: 'close-right', key: string): void
  (e: 'close-all'): void
  (e: 'refresh', key: string): void
}>()

const router = useRouter()

// Refs
const tabsWrapperRef = ref<HTMLElement | null>(null)
const tabsListRef = ref<HTMLElement | null>(null)

// 状态
const showScrollBtn = ref(false)
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  tab: null as AppTab | null
})

// 监听标签变化检查是否需要滚动
watch(() => props.tabs, () => {
  nextTick(() => {
    checkScroll()
  })
}, { deep: true })

onMounted(() => {
  checkScroll()
  window.addEventListener('resize', checkScroll)
  document.addEventListener('click', closeContextMenu)
})

// 检查是否需要滚动按钮
function checkScroll() {
  if (tabsWrapperRef.value && tabsListRef.value) {
    showScrollBtn.value = tabsListRef.value.scrollWidth > tabsWrapperRef.value.clientWidth
  }
}

// 向左滚动
function scrollLeft() {
  if (tabsListRef.value) {
    tabsListRef.value.scrollBy({ left: -200, behavior: 'smooth' })
  }
}

// 向右滚动
function scrollRight() {
  if (tabsListRef.value) {
    tabsListRef.value.scrollBy({ left: 200, behavior: 'smooth' })
  }
}

// 切换标签
function switchTab(tab: AppTab) {
  emit('change', tab.key)
}

// 关闭标签
function closeTab(tab: AppTab) {
  if (tab.affix) return
  emit('close', tab.key)
}

// 显示右键菜单
function showContextMenu(event: MouseEvent, tab: AppTab) {
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.tab = tab
}

// 关闭右键菜单
function closeContextMenu() {
  contextMenu.visible = false
}

// 处理右键菜单操作
function handleContextAction({ key }: { key: string }) {
  const tab = contextMenu.tab
  if (!tab) return

  switch (key) {
    case 'refresh':
      emit('refresh', tab.key)
      break
    case 'close':
      if (!tab.affix) emit('close', tab.key)
      break
    case 'closeOther':
      emit('close-other', tab.key)
      break
    case 'closeLeft':
      emit('close-left', tab.key)
      break
    case 'closeRight':
      emit('close-right', tab.key)
      break
  }

  closeContextMenu()
}

// 处理更多操作
function handleAction({ key }: { key: string }) {
  switch (key) {
    case 'closeOther':
      emit('close-other', props.activeKey)
      break
    case 'closeLeft':
      emit('close-left', props.activeKey)
      break
    case 'closeRight':
      emit('close-right', props.activeKey)
      break
    case 'closeAll':
      emit('close-all')
      break
  }
}
</script>

<style scoped lang="scss">
.app-tabs {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

  .tabs-container {
    display: flex;
    align-items: center;
    height: 40px;
    position: relative;
  }

  .scroll-btn {
    width: 28px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #666;
    background: #fff;
    border: none;

    &:hover {
      color: #1890ff;
      background: #f5f5f5;
    }

    &.scroll-left {
      border-right: 1px solid #f0f0f0;
    }

    &.scroll-right {
      border-left: 1px solid #f0f0f0;
    }
  }

  .tabs-wrapper {
    flex: 1;
    overflow: hidden;
  }

  .tabs-list {
    display: flex;
    height: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;

    &::-webkit-scrollbar {
      display: none;
    }
  }

  .tab-item {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 100%;
    padding: 0 16px;
    white-space: nowrap;
    cursor: pointer;
    border-right: 1px solid #f0f0f0;
    color: #666;
    transition: all 0.2s;
    position: relative;

    &:hover {
      color: #1890ff;
      background: #f5f5f5;
    }

    &.active {
      color: #1890ff;
      background: #fff;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: #1890ff;
      }
    }

    .tab-icon {
      font-size: 14px;
    }

    .tab-title {
      font-size: 13px;
    }

    .tab-close {
      font-size: 12px;
      margin-left: 4px;
      color: #999;
      cursor: pointer;

      &:hover {
        color: #ff4d4f;
      }
    }
  }

  .tabs-actions {
    width: 40px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-left: 1px solid #f0f0f0;

    .action-btn {
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #666;
      border-radius: 4px;

      &:hover {
        color: #1890ff;
        background: #f5f5f5;
      }
    }
  }
}

.context-menu {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>
