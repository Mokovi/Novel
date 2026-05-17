<template>
  <div class="stream-output" :class="{ 'is-streaming': streaming }">
    <div ref="scrollRef" class="stream-content">
      {{ displayText }}<span v-if="streaming && displayText" class="stream-cursor" />
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-editor);
  height: 100%;
  overflow: hidden;
  border-left: 3px solid var(--color-border);
  transition: border-color var(--transition-base);
}

.stream-output.is-streaming {
  border-left-color: var(--color-accent);
}

.stream-content {
  padding: 20px 24px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--font-editor);
  font-size: 16px;
  line-height: 1.9;
  height: 100%;
  overflow-y: auto;
  color: var(--color-text-primary);
}

.stream-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--color-accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s step-end infinite;
}
</style>
