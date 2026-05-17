<template>
  <div class="stream-output">
    <div ref="scrollRef" class="stream-content">
      {{ displayText }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  content: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
})

const displayText = ref('')
const scrollRef = ref(null)

watch(() => props.content, (val) => {
  displayText.value = val
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}, { immediate: true })
</script>

<style scoped>
.stream-output {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  height: 100%;
  overflow: hidden;
}
.stream-content {
  padding: 16px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.7;
  height: 100%;
  overflow-y: auto;
}
</style>
