<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['success'])

const HANDLE_W = 48
const MIN_DURATION = 250 // 拖动时长下限（毫秒），过滤机器式瞬时滑动

const trackRef = ref(null)
const dragging = ref(false)
const passed = ref(false)
const offset = ref(0)

let startX = 0
let startTime = 0
let moved = false

const maxOffset = computed(() => {
  const w = trackRef.value?.clientWidth ?? 0
  return Math.max(w - HANDLE_W - 2, 0)
})

const fillStyle = computed(() => ({ width: `${offset.value + HANDLE_W}px` }))
const handleStyle = computed(() => ({ left: `${offset.value}px` }))

function pointX(e) {
  return e.touches ? e.touches[0].clientX : e.clientX
}

function onDown(e) {
  if (passed.value) return
  dragging.value = true
  moved = false
  startX = pointX(e)
  startTime = Date.now()
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
  window.addEventListener('touchmove', onMove, { passive: false })
  window.addEventListener('touchend', onUp)
}

function onMove(e) {
  if (!dragging.value) return
  if (e.cancelable) e.preventDefault()
  const dx = pointX(e) - startX
  if (Math.abs(dx) > 2) moved = true
  offset.value = Math.min(Math.max(dx, 0), maxOffset.value)
}

function onUp() {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', onUp)
  window.removeEventListener('touchmove', onMove)
  window.removeEventListener('touchend', onUp)

  const duration = Date.now() - startTime
  const ok = moved && duration >= MIN_DURATION && offset.value >= maxOffset.value - 4
  if (ok) {
    offset.value = maxOffset.value
    passed.value = true
    emit('success')
  } else {
    offset.value = 0 // 未到底，回弹
  }
}

function reset() {
  passed.value = false
  offset.value = 0
}

defineExpose({ reset })
</script>

<template>
  <div ref="trackRef" class="sv-track" :class="{ dragging, passed }">
    <div class="sv-fill" :style="fillStyle"></div>
    <div class="sv-text">{{ passed ? '验证通过' : '按住滑块，拖动到最右侧' }}</div>
    <div
      class="sv-handle"
      :style="handleStyle"
      @mousedown="onDown"
      @touchstart="onDown"
    >{{ passed ? '✓' : '→' }}</div>
  </div>
</template>

<style scoped>
.sv-track {
  position: relative;
  width: 100%;
  height: 42px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  user-select: none;
  box-sizing: border-box;
}
.sv-track:not(.dragging) .sv-fill,
.sv-track:not(.dragging) .sv-handle {
  transition: all 0.25s ease;
}
.sv-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: #e1f3d8;
}
.sv-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #909399;
  pointer-events: none;
}
.sv-handle {
  position: absolute;
  top: 0;
  left: 0;
  width: 48px;
  height: 100%;
  background: #fff;
  border-right: 1px solid #dcdfe6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #909399;
  cursor: grab;
  touch-action: none;
}
.sv-handle:active { cursor: grabbing; }
.sv-track.passed { border-color: #67c23a; }
.sv-track.passed .sv-text { color: #67c23a; }
.sv-track.passed .sv-handle {
  background: #67c23a;
  border-color: #67c23a;
  color: #fff;
  cursor: default;
}
</style>
