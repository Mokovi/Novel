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
      </div>
    </div>

    <!-- Loading spinner -->
    <div v-if="store.loading" class="loading-center">
      <n-spin size="medium" />
    </div>

    <!-- Tabs -->
    <template v-else-if="store.sections.length > 0">
      <n-tabs type="line" animated class="section-tabs">
        <n-tab-pane
          v-for="sec in store.sections"
          :key="sec.key"
          :tab="sec.label"
          :name="sec.key"
        >
          <div class="section-content">
            <!-- Glossary (array of {term, definition}) -->
            <template v-if="sec.key === '术语表'">
              <GlossaryEditor
                :items="glossaryItems"
                @update:items="onGlossaryUpdate"
              />
            </template>

            <!-- Array of objects -->
            <template v-else-if="Array.isArray(sec.content)">
              <ArrayEditor
                :value="sec.content"
                @update:value="onSectionUpdate(sec.key, $event)"
              />
            </template>

            <!-- Object or other -->
            <template v-else>
              <ObjectEditor
                :value="sec.content"
                @update:value="onSectionUpdate(sec.key, $event)"
              />
            </template>

            <!-- Save button per section -->
            <div class="section-footer">
              <n-button
                type="primary"
                size="small"
                :loading="store.saving"
                :disabled="!isSectionDirty(sec.key)"
                @click="saveSection(sec.key)"
              >
                保存 {{ sec.label }}
              </n-button>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </template>

    <!-- Empty state -->
    <div v-else class="empty-worldview">
      <n-empty description="暂无世界观设定">
        <template #extra>
          <p class="empty-hint">世界观设定存储在作品级别，请先通过大纲视图中的「全书大纲」生成或手动添加内容。</p>
          <n-button size="small" @click="refreshData">刷新数据</n-button>
        </template>
      </n-empty>
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
        <div v-if="genPhase === 'idle'" class="gen-prompt-section">
          <n-input
            v-model:value="userPrompt"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="补充提示词（可选）：输入您对世界观生成的特定要求..."
          />
          <div v-if="adminStore.isAdmin" style="margin-top:12px">
            <n-button size="small" quaternary @click="handlePreview">提示词预览</n-button>
          </div>
        </div>
        <div v-if="genPhase !== 'idle'" class="gen-output">
          <p v-if="genModel" class="gen-meta">模型: {{ genModel }} | 预估: {{ genTokens }} tokens</p>
          <div v-if="genPhase === 'generating'" class="gen-text">{{ genOutput }}</div>
          <div v-else class="markdown-body" v-html="renderMarkdown(genOutput)" />
          <n-spin v-if="genRunning" size="small" />
        </div>
        <template #action>
          <n-space justify="end">
            <template v-if="genPhase === 'idle'">
              <n-button @click="showGenModal = false">取消</n-button>
              <n-button type="primary" @click="startWorldviewGen">开始生成</n-button>
            </template>
            <template v-else-if="genPhase === 'generating'">
              <n-button @click="cancelGeneration">取消</n-button>
            </template>
            <template v-else>
              <n-button type="primary" @click="closeGenModal">关闭</n-button>
            </template>
          </n-space>
        </template>
      </n-card>
    </n-modal>

    <!-- ═══ Prompt Preview Modal ═══ -->
    <n-modal v-model:show="showPreviewModal" preset="card" title="提示词预览" style="max-width: 800px">
      <n-space v-if="previewLoading" justify="center">
        <n-spin />
      </n-space>
      <n-space v-else-if="previewData" vertical :size="12">
        <n-space>
          <n-tag type="info" size="small">模型: {{ previewData.model }}</n-tag>
          <n-tag size="small">模板: {{ previewData.template_name }}</n-tag>
          <n-tag size="small">预估: ~{{ previewData.token_estimate }} tokens</n-tag>
        </n-space>
        <n-input
          type="textarea"
          :value="previewData.prompt"
          readonly
          rows="20"
          class="preview-textarea"
        />
      </n-space>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { marked } from 'marked'
import { useWorldviewStore } from '../stores/worldview.js'
import { useAdminStore } from '../stores/admin.js'
import { generateWorldview, previewWorldviewPrompt } from '../api/generate.js'
import GlossaryEditor from '../components/worldview/GlossaryEditor.vue'
import ObjectEditor from '../components/worldview/ObjectEditor.vue'
import ArrayEditor from '../components/worldview/ArrayEditor.vue'

const route = useRoute()
const store = useWorldviewStore()
const adminStore = useAdminStore()
const message = useMessage()

const bookId = computed(() => Number(route.params.bookId))

const showPreview = ref(false)
const dirtySections = ref(new Set())

const glossaryItems = computed({
  get: () => {
    const g = store.data['术语表']
    return Array.isArray(g) ? g : []
  },
  set: (val) => {
    store.updateSection('术语表', val)
    dirtySections.value.add('术语表')
  },
})

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
const userPrompt = ref('')

// ── Preview modal state ──
const showPreviewModal = ref(false)
const previewData = ref(null)
const previewLoading = ref(false)

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}

function isSectionDirty(key) {
  return dirtySections.value.has(key)
}

function onSectionUpdate(key, value) {
  store.updateSection(key, value)
  dirtySections.value.add(key)
}

function onGlossaryUpdate(items) {
  glossaryItems.value = items
}

async function saveSection(key) {
  await store.saveSection(key, bookId.value)
  dirtySections.value.delete(key)
  message.success(`${key} 已保存`)
}

async function refreshData() {
  await store.fetch(bookId.value)
  dirtySections.value.clear()
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

function prepareGenerateWorldview() {
  genOutput.value = ''
  genModel.value = ''
  genTokens.value = 0
  genRunning.value = false
  genPhase.value = 'idle'
  userPrompt.value = ''
  showGenModal.value = true
}

function startWorldviewGen() {
  genPhase.value = 'generating'
  genRunning.value = true

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
  }, { user_prompt: userPrompt.value })
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

async function handlePreview() {
  previewLoading.value = true
  previewData.value = null
  showPreviewModal.value = true
  try {
    const data = await previewWorldviewPrompt(bookId.value)
    previewData.value = data
  } catch (e) {
    message.error(e.message || '获取提示词预览失败')
  } finally {
    previewLoading.value = false
  }
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

.section-tabs {
  min-height: 400px;
}

.section-content {
  padding-top: 16px;
}

.section-footer {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--divider-color, #efefef);
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

.empty-worldview {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.empty-hint {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 8px 0 16px;
  text-align: center;
  max-width: 360px;
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
</style>
