<template>
  <div class="worldview-editor">
    <!-- Header -->
    <div class="editor-header">
      <h2>世界观设定</h2>
      <div class="header-actions">
        <n-button size="small" quaternary @click="refreshData">
          <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></n-icon></template>
        </n-button>
        <n-button size="small" @click="prepareGenerateWorldview">
          <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="currentColor" stroke-width="2" fill="none"/></svg></n-icon></template>
          AI 生成设定
        </n-button>
        <n-button size="small" @click="showPreview = true">
          <template #icon><n-icon><svg viewBox="0 0 24 24" fill="none" width="16" height="16"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/></svg></n-icon></template>
          注入预览
        </n-button>
        <n-button size="small" type="primary" :loading="store.saving" @click="handleSave">
          保存
        </n-button>
      </div>
    </div>

    <!-- Loading spinner -->
    <div v-if="store.loading" class="loading-center">
      <n-spin size="medium" />
    </div>

    <!-- Markdown editor with preview/edit toggle -->
    <div v-else class="editor-body">
      <div class="editor-mode-bar">
        <button class="mode-btn" :class="{ active: isPreviewMode }" @click="isPreviewMode = true">预览</button>
        <button class="mode-btn" :class="{ active: !isPreviewMode }" @click="isPreviewMode = false">编辑</button>
      </div>
      <div v-if="isPreviewMode" class="markdown-preview" v-html="renderMarkdown(store.worldview)" />
      <textarea
        v-else
        v-model="store.worldview"
        class="markdown-textarea"
        placeholder="在此输入世界观设定（支持 Markdown 格式）&#10;&#10;可以使用 ## 标题、- 列表、**加粗** 等格式"
      />
    </div>

    <!-- Inject preview drawer -->
    <n-drawer v-model:show="showPreview" width="520" placement="right">
      <n-drawer-content title="设定注入预览" closable>
        <template #header-extra>
          <n-tag v-if="preview.token_estimate" type="info" size="small">
            ~{{ preview.token_estimate }} tokens
          </n-tag>
        </template>

        <div v-if="store.previewLoading" class="loading-center">
          <n-spin size="small" />
        </div>

        <n-empty v-else-if="!store.previewText" description="暂无设定内容" />

        <pre v-else class="preview-textarea">{{ store.previewText }}</pre>
      </n-drawer-content>
    </n-drawer>

    <!-- ═══ SSE Generation Output Modal ═══ -->
    <n-modal v-model:show="showGenModal" :mask-closable="false" style="width: 720px">
      <n-card title="AI 生成世界观设定" style="max-height: 80vh; overflow-y: auto; border-radius: 12px">
        <div v-if="genPhase === 'idle'">
          <PromptInjectionPanel
            title="AI 生成世界观设定"
            :injection-items="injectionItems"
            :book-id="bookId"
            :loading="genRunning"
            gen-type="worldview"
            @start="startWorldviewGen"
            @cancel="showGenModal = false"
          />
        </div>
        <div v-if="genPhase !== 'idle'" class="gen-output">
          <p v-if="genModel" class="gen-meta">模型: {{ genModel }} | 预估: {{ genTokens }} tokens</p>
          <div v-if="genPhase === 'generating'" class="gen-text">{{ genOutput }}</div>
          <div v-else class="markdown-body" v-html="renderMarkdown(genOutput)" />
          <n-spin v-if="genRunning" size="small" />
        </div>
        <template #action>
          <n-space justify="end">
            <template v-if="genPhase === 'generating'">
              <n-button @click="cancelGeneration">取消</n-button>
            </template>
            <template v-else-if="genPhase === 'done'">
              <n-button type="primary" @click="closeGenModal">关闭</n-button>
            </template>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { marked } from 'marked'
import { useWorldviewStore } from '../stores/worldview.js'
import { generateWorldview, fetchWorldviewInjections } from '../api/generate.js'
import PromptInjectionPanel from '../components/generate/PromptInjectionPanel.vue'

const route = useRoute()
const store = useWorldviewStore()
const message = useMessage()

const bookId = computed(() => Number(route.params.bookId))

const showPreview = ref(false)
const isPreviewMode = ref(true)

const preview = computed(() => ({
  text: store.previewText,
  token_estimate: store.previewTokenEstimate,
}))

// ── Generation modal state ──
const showGenModal = ref(false)
const genOutput = ref('')
const genModel = ref('')
const genTokens = ref(0)
const genRunning = ref(false)
const genAbort = ref(null)
const genPhase = ref('idle') // 'idle' | 'generating' | 'done'

const injectionItems = ref([])

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}

async function handleSave() {
  await store.saveAll(bookId.value)
  message.success('世界观设定已保存')
}

async function refreshData() {
  await store.fetch(bookId.value)
  message.success('已刷新')
}

watch(showPreview, async (val) => {
  if (val) {
    await store.fetchPreview(bookId.value)
  }
})

onMounted(() => {
  store.fetch(bookId.value)
})

// ── Generation handlers ──

async function prepareGenerateWorldview() {
  genOutput.value = ''
  genModel.value = ''
  genTokens.value = 0
  genRunning.value = false
  genPhase.value = 'idle'
  injectionItems.value = []
  showGenModal.value = true
  try {
    const data = await fetchWorldviewInjections(bookId.value)
    injectionItems.value = data.items || []
  } catch (e) {
    console.error('Failed to fetch injection items:', e)
  }
}

function startWorldviewGen(overrides, userPrompt) {
  genPhase.value = 'generating'
  genRunning.value = true

  const body = { user_prompt: userPrompt || '' }
  if (overrides && (overrides.exclude_variables?.length || overrides.extra_variables || overrides.added_character_ids?.length)) {
    body.injection_overrides = overrides
  }

  genAbort.value = generateWorldview(bookId.value, {
    onStart: (evt) => {
      genModel.value = evt.model || ''
      genTokens.value = evt.token_estimate || 0
    },
    onToken: (token) => {
      genOutput.value += token
    },
    onDone: () => {
      genRunning.value = false
      genPhase.value = 'done'
      message.success('世界观设定生成完成')
    },
    onError: (err) => {
      genRunning.value = false
      genPhase.value = 'done'
      message.error(err)
    },
  }, body)
}

function cancelGeneration() {
  genAbort.value?.abort()
  genRunning.value = false
  genPhase.value = 'idle'
  message.info('已取消生成')
}

function closeGenModal() {
  showGenModal.value = false
  store.fetch(bookId.value)
}
</script>

<style scoped>
.worldview-editor {
  max-width: 960px;
  margin: 0 auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.editor-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.editor-body {
  min-height: 500px;
}

.markdown-textarea {
  width: 100%;
  min-height: 500px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text);
  background: var(--color-bg-editor);
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.markdown-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(201, 169, 78, 0.12);
}

.markdown-textarea::placeholder {
  color: var(--color-text-muted);
  opacity: 0.5;
}

.loading-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.preview-textarea {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text);
  background: #f8f8f8;
  border-radius: 6px;
  padding: 16px;
  margin: 0;
}

.gen-prompt-section {
  margin-bottom: 8px;
}

.gen-output {
  margin-bottom: 8px;
}

.gen-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 0 8px;
}

.gen-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text);
}

.preview-textarea :deep(textarea) {
  font-family: var(--font-mono, 'SF Mono', 'Fira Code', monospace);
  font-size: 13px;
  line-height: 1.7;
}

/* ── Preview/Edit mode toggle ── */
.editor-mode-bar {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  align-self: flex-start;
}

.mode-btn {
  padding: 6px 20px;
  font-size: 13px;
  font-family: var(--font-ui);
  border: none;
  cursor: pointer;
  background: transparent;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: var(--color-accent);
  color: #fff;
}

.mode-btn:not(.active):hover {
  background: var(--color-bg-hover, #f0f0f0);
}

.markdown-preview {
  min-height: 500px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: #fafaf8;
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text);
  overflow-y: auto;
}
</style>
