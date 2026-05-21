<template>
  <n-modal :show="visible" :mask-closable="false" style="width: 720px">
    <n-card :title="title" style="max-height: 80vh; overflow-y: auto; border-radius: 12px">
      <div v-if="phase === 'idle'">
        <PromptInjectionPanel
          :title="title"
          :injection-items="injectionItems"
          :book-id="bookId"
          :loading="running"
          :gen-type="genType"
          @start="(overrides, userPrompt) => $emit('start', overrides, userPrompt)"
          @cancel="$emit('close')"
        />
      </div>
      <div v-if="phase !== 'idle'" class="gen-output">
        <p v-if="model" class="gen-meta">
          模型: {{ model }} | 预估: {{ tokens }} tokens
        </p>
        <div v-if="phase === 'generating'" class="gen-text">{{ output }}</div>
        <div v-else class="preview-wrapper">
          <CopyButton :text="output" />
          <div class="markdown-body" v-html="renderMarkdown(output)" />
        </div>
        <div v-if="phase === 'done' && result" class="gen-result">
          <n-alert v-if="result.created_count > 0" type="success" closable>
            已创建 {{ result.created_count }} 个角色
            <template v-if="result.skipped_count > 0">，跳过 {{ result.skipped_count }} 个</template>
          </n-alert>
          <n-alert v-if="result.errors?.length" type="warning" closable>
            <div v-for="(err, i) in result.errors" :key="i" class="gen-error-item">{{ err }}</div>
          </n-alert>
        </div>
        <n-spin v-if="running" size="small" />
      </div>
      <template #action>
        <n-space justify="end">
          <template v-if="phase === 'generating'">
            <n-button @click="$emit('cancel')">取消</n-button>
          </template>
          <template v-else-if="phase === 'done'">
            <n-button type="primary" @click="$emit('close')">关闭</n-button>
          </template>
        </n-space>
      </template>
    </n-card>
  </n-modal>
</template>

<script setup>
import { NCard, NModal, NSpin, NSpace, NButton, NAlert } from 'naive-ui'
import { marked } from 'marked'
import PromptInjectionPanel from './PromptInjectionPanel.vue'
import CopyButton from '../common/CopyButton.vue'

defineProps({
  title: { type: String, default: 'AI 生成' },
  genType: { type: String, default: 'worldview' },
  visible: { type: Boolean, default: false },
  phase: { type: String, default: 'idle' },
  output: { type: String, default: '' },
  model: { type: String, default: '' },
  tokens: { type: Number, default: 0 },
  running: { type: Boolean, default: false },
  injectionItems: { type: Array, default: () => [] },
  bookId: { type: Number, required: true },
  result: { type: Object, default: null },
})

defineEmits(['start', 'cancel', 'close'])

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch { return text }
}
</script>

<style scoped>
.gen-output {
  min-height: 100px;
}

.gen-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 0 12px;
  padding: 6px 10px;
  background: #f8f6f2;
  border-radius: 6px;
}

.gen-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  background: var(--color-bg-editor);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.preview-wrapper {
  position: relative;
}

.gen-result {
  margin-top: 16px;
}

.gen-error-item {
  font-size: 13px;
  line-height: 1.6;
}

.markdown-body {
  min-height: 200px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fafaf8;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
  overflow-y: auto;
}
</style>
