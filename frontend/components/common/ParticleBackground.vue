<template>
  <canvas
    ref="canvas"
    class="particles-canvas"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  particleCount?: number
  particleColor?: string
  particleSize?: number
  speed?: number
  opacity?: number
}>(), {
  particleCount: 50,
  particleColor: '#667eea',
  particleSize: 3,
  speed: 0.5,
  opacity: 0.5
})

const canvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animationId: number | null = null
let particles: Array<{
  x: number
  y: number
  vx: number
  vy: number
  size: number
}> = []

const resizeCanvas = () => {
  if (!canvas.value) return
  canvas.value.width = window.innerWidth
  canvas.value.height = window.innerHeight
}

const initParticles = () => {
  particles = []
  for (let i = 0; i < props.particleCount; i++) {
    particles.push({
      x: Math.random() * (canvas.value?.width || window.innerWidth),
      y: Math.random() * (canvas.value?.height || window.innerHeight),
      vx: (Math.random() - 0.5) * props.speed,
      vy: (Math.random() - 0.5) * props.speed,
      size: Math.random() * props.particleSize + 1
    })
  }
}

const drawParticles = () => {
  if (!ctx || !canvas.value) return
  
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  
  particles.forEach((p, i) => {
    p.x += p.vx
    p.y += p.vy
    
    if (p.x < 0 || p.x > canvas.value!.width) p.vx *= -1
    if (p.y < 0 || p.y > canvas.value!.height) p.vy *= -1
    
    ctx!.beginPath()
    ctx!.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx!.fillStyle = props.particleColor
    ctx!.globalAlpha = props.opacity
    ctx!.fill()
    
    particles.forEach((p2, j) => {
      if (i === j) return
      const dx = p.x - p2.x
      const dy = p.y - p2.y
      const distance = Math.sqrt(dx * dx + dy * dy)
      
      if (distance < 100) {
        ctx!.beginPath()
        ctx!.moveTo(p.x, p.y)
        ctx!.lineTo(p2.x, p2.y)
        ctx!.strokeStyle = props.particleColor
        ctx!.globalAlpha = props.opacity * (1 - distance / 100)
        ctx!.stroke()
      }
    })
  })
  
  ctx.globalAlpha = 1
  animationId = requestAnimationFrame(drawParticles)
}

onMounted(() => {
  if (!canvas.value) return
  ctx = canvas.value.getContext('2d')
  resizeCanvas()
  initParticles()
  drawParticles()
  
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<style scoped>
.particles-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}
</style>
