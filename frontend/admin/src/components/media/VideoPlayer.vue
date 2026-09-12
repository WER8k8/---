<template>
  <a-modal
    v-model:open="modalOpen"
    :title="title || '视频播放'"
    width="800px"
    :footer="null"
    :destroy-on-close="true"
    :centered="true"
    class="video-player-modal"
  >
    <div class="video-player-wrapper" ref="wrapperRef">
      <video
        ref="videoRef"
        :src="src"
        class="video-player-element"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMeta"
        @ended="onEnded"
        @play="onPlay"
        @pause="onPause"
        @click="togglePlay"
      >
        您的浏览器不支持 HTML5 视频播放
      </video>

      <!-- Custom Controls -->
      <div class="video-controls" v-show="controlsVisible" @mouseenter="showControls" @mouseleave="startHideTimer">
        <div class="progress-bar" @mousedown="onProgressDown">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            <div class="progress-thumb" :style="{ left: progressPercent + '%' }"></div>
          </div>
        </div>

        <div class="controls-bottom">
          <div class="controls-left">
            <a-button type="text" class="control-btn" @click="togglePlay">
              <CaretRightOutlined v-if="!isPlaying" class="control-icon" />
              <PauseOutlined v-else class="control-icon" />
            </a-button>
            <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          </div>

          <div class="controls-right">
            <div class="volume-control">
              <a-button type="text" class="control-btn" @click="toggleMute">
                <AudioMutedOutlined v-if="isMuted || volume === 0" class="control-icon" />
                <SoundOutlined v-else class="control-icon" />
              </a-button>
              <div class="volume-slider" @mousedown="onVolumeDown">
                <div class="volume-track">
                  <div class="volume-fill" :style="{ width: (isMuted ? 0 : volume * 100) + '%' }"></div>
                </div>
              </div>
            </div>

            <a-button type="text" class="control-btn" @click="toggleFullscreen">
              <FullscreenOutlined class="control-icon" />
            </a-button>
          </div>
        </div>
      </div>

      <!-- Big play button overlay -->
      <div v-if="!isPlaying && !hasEnded" class="big-play-overlay" @click="togglePlay">
        <CaretRightOutlined class="big-play-icon" />
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import {
  AudioMutedOutlined,
  CaretRightOutlined,
  FullscreenOutlined,
  PauseOutlined,
  SoundOutlined,
} from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    /** @deprecated 使用 open */
    visible?: boolean
    open?: boolean
    src: string
    title?: string
  }>(),
  { open: undefined, visible: undefined },
)

const emit = defineEmits<{
  'update:open': [value: boolean]
  /** @deprecated 使用 update:open */
  'update:visible': [value: boolean]
}>()

const modalOpen = computed({
  get: () => props.open ?? props.visible ?? false,
  set: (val: boolean) => {
    emit('update:open', val)
    emit('update:visible', val)
  },
})

const videoRef = ref<HTMLVideoElement | null>(null)
const wrapperRef = ref<HTMLElement | null>(null)

const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)
const hasEnded = ref(false)
const controlsVisible = ref(true)
const isDraggingProgress = ref(false)
const isDraggingVolume = ref(false)
let hideTimer: ReturnType<typeof setTimeout> | null = null

const progressPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

function formatTime(t: number): string {
  if (!t || isNaN(t)) return '00:00'
  const m = Math.floor(t / 60)
  const s = Math.floor(t % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function togglePlay() {
  const video = videoRef.value
  if (!video) return
  if (hasEnded.value) {
    hasEnded.value = false
    video.currentTime = 0
    video.play()
    return
  }
  if (video.paused) {
    video.play()
  } else {
    video.pause()
  }
}

function toggleMute() {
  const video = videoRef.value
  if (!video) return
  video.muted = !video.muted
  isMuted.value = video.muted
}

function toggleFullscreen() {
  const el = wrapperRef.value
  if (!el) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    el.requestFullscreen()
  }
}

function onTimeUpdate(e: Event) {
  const video = e.target as HTMLVideoElement
  currentTime.value = video.currentTime
}

function onLoadedMeta(e: Event) {
  const video = e.target as HTMLVideoElement
  duration.value = video.duration
}

function onEnded() {
  isPlaying.value = false
  hasEnded.value = true
}

function onPlay() {
  isPlaying.value = true
  hasEnded.value = false
}

function onPause() {
  isPlaying.value = false
}

function onProgressDown(e: MouseEvent) {
  e.preventDefault()
  isDraggingProgress.value = true
  seekVideo(e)
  document.addEventListener('mousemove', onProgressMove)
  document.addEventListener('mouseup', onProgressUp)
}

function onProgressMove(e: MouseEvent) {
  if (isDraggingProgress.value) {
    seekVideo(e)
  }
}

function onProgressUp() {
  isDraggingProgress.value = false
  document.removeEventListener('mousemove', onProgressMove)
  document.removeEventListener('mouseup', onProgressUp)
}

function seekVideo(e: MouseEvent) {
  const video = videoRef.value
  if (!video) return
  const bar = document.querySelector('.progress-bar')
  if (!bar) return
  const rect = bar.getBoundingClientRect()
  const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  video.currentTime = pos * duration.value
}

function onVolumeDown(e: MouseEvent) {
  e.preventDefault()
  isDraggingVolume.value = true
  setVolume(e)
  document.addEventListener('mousemove', onVolumeMove)
  document.addEventListener('mouseup', onVolumeUp)
}

function onVolumeMove(e: MouseEvent) {
  if (isDraggingVolume.value) {
    setVolume(e)
  }
}

function onVolumeUp() {
  isDraggingVolume.value = false
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', onVolumeUp)
}

function setVolume(e: MouseEvent) {
  const video = videoRef.value
  if (!video) return
  const slider = document.querySelector('.volume-slider')
  if (!slider) return
  const rect = slider.getBoundingClientRect()
  const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  video.volume = pos
  volume.value = pos
  if (pos > 0 && video.muted) {
    video.muted = false
    isMuted.value = false
  }
}

function showControls() {
  controlsVisible.value = true
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

function startHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer)
  }
  if (isPlaying.value) {
    hideTimer = setTimeout(() => {
      controlsVisible.value = false
    }, 3000)
  }
}

// Pause video when modal is closed
watch(modalOpen, (val) => {
  if (!val && videoRef.value) {
    videoRef.value.pause()
    isPlaying.value = false
  }
  if (val) {
    controlsVisible.value = true
    hasEnded.value = false
  }
})

onBeforeUnmount(() => {
  if (hideTimer) clearTimeout(hideTimer)
  document.removeEventListener('mousemove', onProgressMove)
  document.removeEventListener('mouseup', onProgressUp)
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', onVolumeUp)
})
</script>

<style scoped>
.video-player-modal :deep(.ant-modal-content) {
  padding: 0;
  overflow: hidden;
  border-radius: 12px;
  background: #000;
}
.video-player-modal :deep(.ant-modal-header) {
  background: #111;
  border-bottom: 1px solid #222;
  padding: 12px 24px;
}
.video-player-modal :deep(.ant-modal-title) {
  color: #e5e7eb;
  font-size: 15px;
}
.video-player-modal :deep(.ant-modal-close) {
  color: #9ca3af;
  top: 8px;
}
.video-player-modal :deep(.ant-modal-body) {
  padding: 0;
}

.video-player-wrapper {
  position: relative;
  width: 100%;
  background: #000;
  line-height: 0;
}

.video-player-element {
  width: 100%;
  display: block;
  max-height: 70vh;
  object-fit: contain;
  cursor: pointer;
}

.video-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.85));
  padding: 40px 12px 8px;
  transition: opacity 0.3s ease;
  cursor: default;
}

.progress-bar {
  width: 100%;
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  margin-bottom: 4px;
}

.progress-track {
  width: 100%;
  height: 4px;
  background: rgba(255,255,255,0.25);
  border-radius: 2px;
  position: relative;
  overflow: visible;
}

.progress-fill {
  height: 100%;
  background: var(--uj-brand, #4a9b8c);
  border-radius: 2px;
  transition: width 0.1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: var(--uj-brand, #4a9b8c);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.15s;
}

.progress-bar:hover .progress-thumb {
  opacity: 1;
}
.progress-bar:hover .progress-track {
  height: 6px;
}

.controls-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.control-btn {
  color: #e5e7eb !important;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.control-btn:hover {
  color: #fff !important;
  background: rgba(255,255,255,0.1) !important;
}

.control-icon {
  font-size: 15px;
  line-height: 1;
}

.time-display {
  color: #d1d5db;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  margin-left: 4px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 0;
}

.volume-slider {
  width: 0;
  height: 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  overflow: hidden;
  transition: width 0.2s ease;
}

.volume-control:hover .volume-slider {
  width: 60px;
}

.volume-track {
  width: 60px;
  height: 4px;
  background: rgba(255,255,255,0.25);
  border-radius: 2px;
  position: relative;
}

.volume-fill {
  height: 100%;
  background: #e5e7eb;
  border-radius: 2px;
}

.big-play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.35);
  cursor: pointer;
  transition: background 0.2s;
}
.big-play-overlay:hover {
  background: rgba(0,0,0,0.25);
}

.big-play-icon {
  font-size: 56px;
  color: rgba(255,255,255,0.85);
  text-shadow: 0 2px 12px rgba(0,0,0,0.4);
}
</style>
