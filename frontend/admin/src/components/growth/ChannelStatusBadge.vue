/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-tooltip :title="tooltipText" placement="top">
    <span
      class="channel-status-badge"
      :class="[`is-${meta.state}`, `channel-status-badge--${variant}`]"
      :style="badgeStyle"
      role="status"
      :aria-label="ariaLabel"
    >
      <component :is="iconComp" class="channel-status-badge__icon" aria-hidden="true" />
      <span v-if="showLabel" class="channel-status-badge__label">{{ meta.label }}</span>
    </span>
  </a-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  CheckCircleOutlined,
  ExperimentOutlined,
  ExclamationCircleOutlined,
  StopOutlined,
} from '@ant-design/icons-vue'
import { normalizeChannelState, getChannelStateMeta } from '@/utils/channelStatus'

/**
 * 渠道四态徽标：live / mock / degraded / blocked。
 *
 * 后端当前下发 real / mock / coming_soon，由 `normalizeChannelState`
 * 归一化；四态均带图标 + 文案 + 颜色，不依赖颜色单通道区分。
 */
interface Props {
  /** 渠道原始状态（后端取值，可传 real/mock/coming_soon 或 live/degraded/blocked） */
  status?: string | null
  /** 渠道名称，用于 tooltip 与 aria-label */
  name?: string
  /** 后端 human-readable 原因，透传到 tooltip */
  reason?: string
  /** 是否展示文案，false 时仅圆点 + 图标（紧凑场景） */
  showLabel?: boolean
  /** 视觉形态：tag 带底色边框 / plain 仅图标文字 */
  variant?: 'tag' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  status: '',
  name: '',
  reason: '',
  showLabel: true,
  variant: 'tag',
})

const state = computed(() => normalizeChannelState(props.status))
const meta = computed(() => getChannelStateMeta(props.status))

const ICON_MAP = {
  live: CheckCircleOutlined,
  mock: ExperimentOutlined,
  degraded: ExclamationCircleOutlined,
  blocked: StopOutlined,
} as const

const iconComp = computed(() => ICON_MAP[state.value])

const badgeStyle = computed(() =>
  props.variant === 'plain'
    ? { color: meta.value.color }
    : {
        color: meta.value.color,
        borderColor: meta.value.color,
        backgroundColor: meta.value.background,
      },
)

const tooltipText = computed(() => {
  const parts: string[] = []
  if (props.name) parts.push(`${props.name}：${meta.value.label}`)
  else parts.push(meta.value.label)
  parts.push(meta.value.description)
  if (props.reason) parts.push(props.reason)
  return parts.join('　')
})

const ariaLabel = computed(() =>
  `${props.name || '渠道'}状态：${meta.value.label}。${meta.value.description}${props.reason ? ' ' + props.reason : ''}`,
)
</script>

<style scoped lang="scss">
.channel-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  cursor: default;

  &__icon {
    font-size: 13px;
    flex-shrink: 0;
  }

  &__label {
    font-weight: 500;
  }

  // 语义（颜色/底色由内联 style 按 token 注入，这里只控制形态）
  &--tag {
    padding: 2px 8px;
    border: 1px solid currentColor;
    border-radius: 10px;
  }

  &--plain {
    padding: 0;
    border: none;
  }
}
</style>
