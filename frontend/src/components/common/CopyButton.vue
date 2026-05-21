<template>
  <button class="copy-btn" :title="title" @click="handleCopy">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  </button>
</template>

<script setup>
import { useMessage } from 'naive-ui'

const props = defineProps({
  text: { type: String, default: '' },
  title: { type: String, default: '复制内容' },
})

const message = useMessage()

function handleCopy() {
  if (!props.text) return
  const textarea = document.createElement('textarea')
  textarea.value = props.text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
    message.success('已复制')
  } catch {
    message.warning('复制失败')
  }
  document.body.removeChild(textarea)
}
</script>

<style scoped>
.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
  background: rgba(255,255,255,0.9);
  color: var(--color-text-muted);
  cursor: pointer;
  opacity: 0.4;
  transition: opacity 0.2s, color 0.2s, border-color 0.2s;
}
.copy-btn:hover {
  opacity: 1;
}
.copy-btn:hover {
  background: #fff;
  color: var(--color-accent);
  border-color: var(--color-accent);
}
</style>
