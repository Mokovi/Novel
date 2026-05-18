<template>
  <div class="chapter-editor">
    <!-- Generating indicator bar -->
    <div v-if="generating" class="generating-bar" />

    <!-- Top bar -->
    <div class="top-bar">
      <h2 class="editor-title">章节编辑器</h2>
      <div class="top-actions">
        <n-button
          v-if="store.currentChapter"
          :disabled="generating"
          type="primary"
          @click="handleSave"
        >
          保存
        </n-button>
        <n-button
          v-if="store.currentChapter"
          :disabled="generating"
          @click="handleDownload"
        >
          下载
        </n-button>
        <n-popconfirm
          v-if="store.currentChapter"
          @positive-click="handleDelete"
        >
          <template #trigger>
            <n-button :disabled="generating" class="btn-delete">删除章节</n-button>
          </template>
          确定删除此章节？删除后不可恢复。
        </n-popconfirm>
      </div>
    </div>

    <!-- Three-column layout -->
    <n-layout has-sider class="editor-layout" position="absolute">
      <!-- Left: Chapter list -->
      <n-layout-sider width="220" bordered class="left-sider">
        <n-scrollbar style="height: 100%">
          <n-menu
            :value="String(store.currentChapter?.id)"
            :options="chapterMenuOptions"
            @update:value="onSelectChapter"
          />
        </n-scrollbar>
      </n-layout-sider>

      <!-- Center: Editor -->
      <n-layout-content class="center-content">
        <template v-if="store.currentChapter">
          <div v-if="generating" class="stream-container">
            <StreamOutput :content="streamContent" :streaming="true" />
          </div>
          <div v-else class="editor-container">
            <editor-content :editor="editor" class="editor-content" />
          </div>
        </template>
        <n-empty v-else description="从左侧选择或创建章节" class="empty-editor" />
      </n-layout-content>

      <!-- Right: Meta panel -->
      <n-layout-sider
        v-if="store.currentChapter"
        width="280"
        bordered
        position="right"
        class="right-sider"
      >
        <n-scrollbar style="height: 100%; padding: 16px">
          <n-space vertical :size="14">
            <n-form-item label="标题">
              <n-input v-model:value="editTitle" />
            </n-form-item>
            <n-form-item label="摘要">
              <n-input v-model:value="editSummary" type="textarea" rows="4" />
            </n-form-item>
            <n-form-item label="AI 摘要">
              <n-input
                v-model:value="editAiSummary"
                type="textarea"
                rows="4"
                placeholder="AI 生成后自动填充..."
                @blur="handleSaveAiSummary"
              />
            </n-form-item>
            <n-form-item label="世界观注入">
              <n-radio-group
                v-model:value="editingWorldviewLevel"
                size="small"
                @update:value="handleWorldviewLevelChange"
              >
                <n-radio-button value="high">详细</n-radio-button>
                <n-radio-button value="medium">标准</n-radio-button>
                <n-radio-button value="low">精简</n-radio-button>
              </n-radio-group>
            </n-form-item>
            <n-form-item label="关联人物">
              <n-select
                multiple
                filterable
                placeholder="搜索人物..."
                :options="characterOptions"
                v-model:value="editingCharacterIds"
                @update:value="handleCharacterChange"
                :loading="charactersLoading"
              />
            </n-form-item>
            <div v-if="chapterCharacters.length" class="character-tags">
              <n-tag
                v-for="ch in chapterCharacters"
                :key="ch.id"
                closable
                @close="handleCharacterChange(editingCharacterIds.filter(id => id !== ch.id))"
                :type="characterTagType(ch.role_type)"
                size="small"
              >
                {{ ch.name }}
              </n-tag>
            </div>
            <n-divider />
            <n-form-item label="状态">
              <n-space>
                <n-tag :type="statusType(store.currentChapter.status)">
                  {{ statusLabel(store.currentChapter.status) }}
                </n-tag>
              </n-space>
            </n-form-item>
            <n-button
              size="large"
              block
              :type="generating ? 'warning' : 'primary'"
              :loading="generating"
              @click="handleGenerate"
              class="generate-btn"
            >
              {{ generating ? '生成中...' : store.currentChapter.content ? '重新生成' : 'AI 生成' }}
            </n-button>
            <n-button
              size="small"
              block
              secondary
              :disabled="generatingUnlimited"
              @click="handleGenerateUnlimited"
              class="unlimited-btn"
            >
              {{ generatingUnlimited ? '无限生成中...' : '无限生成 (自动分章)' }}
            </n-button>
            <n-button
              v-if="adminStore.isAdmin"
              size="small"
              block
              secondary
              @click="handlePreviewPrompt"
              class="preview-btn"
            >
              提示词预览
            </n-button>
            <n-form-item label="字数">
              <n-text>{{ editContent.length }} 字</n-text>
            </n-form-item>
            <n-divider />
            <n-text depth="3" class="meta-label">AI 生成</n-text>
          </n-space>
        </n-scrollbar>
      </n-layout-sider>
    </n-layout>

    <!-- Prompt preview modal -->
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useChaptersStore } from '../stores/chapters.js'
import { updateChapter, deleteChapter, downloadChapter, getChapterCharacters, setChapterCharacters } from '../api/chapters.js'
import { listCharacters } from '../api/characters.js'
import { generateChapter, generateUnlimited, previewPrompt } from '../api/generate.js'
import { useAdminStore } from '../stores/admin.js'
import StreamOutput from '../components/common/StreamOutput.vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const store = useChaptersStore()
const adminStore = useAdminStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

// Tiptap editor
const editor = useEditor({
  content: '',
  extensions: [
    StarterKit,
    Placeholder.configure({ placeholder: '在此编辑章节正文...' }),
  ],
  onUpdate: ({ editor }) => {
    editContent.value = editor.getText()
  },
})

// Generation state
const generating = ref(false)
const generatingUnlimited = ref(false)
const streamContent = ref('')
let abortController = null

// Preview state
const showPreviewModal = ref(false)
const previewData = ref(null)
const previewLoading = ref(false)

// Edit buffers
const editTitle = ref('')
const editSummary = ref('')
const editAiSummary = ref('')
const editContent = ref('')

// Character association
const allCharacters = ref([])
const chapterCharacters = ref([])
const editingCharacterIds = ref([])
const charactersLoading = ref(false)

// Worldview level
const editingWorldviewLevel = ref('medium')

const characterOptions = computed(() =>
  allCharacters.value.map((c) => ({
    label: `${c.name}${c.role_type ? ` (${c.role_type})` : ''}`,
    value: c.id,
  }))
)

const characterTagType = (role) =>
  ({ protagonist: 'success', antagonist: 'error', supporting: 'info', minor: 'default' }[role] || 'default')

// Chapter menu (grouped by volume)
const chapterMenuOptions = computed(() => {
  const options = []
  for (const vol of store.volumes) {
    const children = store.chapters
      .filter((c) => c.volume_id === vol.id)
      .map((c) => ({
        label: c.title,
        key: String(c.id),
      }))
    if (children.length) {
      options.push({
        label: vol.title,
        key: `vol-${vol.id}`,
        children,
      })
    }
  }
  return options
})

const statusType = (s) =>
  ({ pending: 'default', generating: 'warning', completed: 'success' }[s] || 'default')
const statusLabel = (s) =>
  ({ pending: '待生成', generating: '生成中', completed: '已完成' }[s] || s)

// Chapter selection
async function onSelectChapter(key) {
  const id = parseInt(key, 10)
  router.push(`/editor/${id}`)
}

// Watch route param
watch(
  () => route.params.id,
  async (id) => {
    if (id) {
      await store.selectChapter(parseInt(id, 10))
      syncEditBuffers()
      if (route.query.generate === '1') {
        router.replace({ path: route.path, params: route.params })
        handleGenerate()
      }
    }
  },
  { immediate: true },
)

function syncEditBuffers() {
  if (store.currentChapter) {
    editTitle.value = store.currentChapter.title || ''
    editSummary.value = store.currentChapter.summary || ''
    editAiSummary.value = store.currentChapter.ai_summary || ''
    editContent.value = store.currentChapter.content || ''
    editingWorldviewLevel.value = store.currentChapter.worldview_level || 'medium'
    const content = store.currentChapter.content || ''
    if (content) {
      const html = content
        .split('\n\n')
        .map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`)
        .join('')
      editor.value?.commands.setContent(html)
    } else {
      editor.value?.commands.setContent('')
    }
    loadChapterCharacters()
  }
}

async function loadChapterCharacters() {
  if (!store.currentChapter) return
  try {
    const res = await getChapterCharacters(store.currentChapter.id)
    chapterCharacters.value = res.data
    editingCharacterIds.value = res.data.map((c) => c.id)
  } catch (e) {
    console.error('Failed to load chapter characters:', e)
  }
}

async function handleCharacterChange(ids) {
  if (!store.currentChapter) return
  editingCharacterIds.value = ids
  try {
    const res = await setChapterCharacters(store.currentChapter.id, ids)
    chapterCharacters.value = res.data
  } catch (e) {
    message.error(`保存人物关联失败: ${e.response?.data?.detail || e.message}`)
  }
}

async function handleWorldviewLevelChange(val) {
  if (!store.currentChapter) return
  editingWorldviewLevel.value = val
  try {
    await updateChapter(store.currentChapter.id, { worldview_level: val })
    store.currentChapter.worldview_level = val
    message.success('世界观级别已更新')
  } catch (e) {
    message.error(`更新失败: ${e.response?.data?.detail || e.message}`)
  }
}

// Generate
async function handleGenerate() {
  if (!store.currentChapter) return
  if (store.currentChapter.content) {
    const ok = window.confirm('章节已有内容，重新生成将覆盖现有内容。确定继续？')
    if (!ok) return
  }

  generating.value = true
  streamContent.value = ''

  abortController = generateChapter(
    store.currentChapter.id,
    {
      onStart: () => {},
      onToken: (token) => {
        streamContent.value += token
      },
      onSummary: (summary) => {
        editAiSummary.value = summary
      },
      onDone: async () => {
        generating.value = false
        message.success('生成完成')
        // Reload chapter to get saved content
        await store.selectChapter(store.currentChapter.id)
        syncEditBuffers()
      },
      onError: (msg) => {
        generating.value = false
        message.error(`生成失败: ${msg}`)
      },
    },
  )
}

async function handleGenerateUnlimited() {
  if (!store.currentChapter) return
  if (store.currentChapter.content) {
    const ok = window.confirm('章节已有内容，无限生成将覆盖现有内容并创建新章节。确定继续？')
    if (!ok) return
  }

  generatingUnlimited.value = true
  streamContent.value = ''

  abortController = generateUnlimited(
    store.currentChapter.id,
    {
      onStart: () => {},
      onToken: (token) => {
        streamContent.value += token
      },
      onSplitting: (evt) => {
        message.info(`内容已分割为 ${evt.segment_count} 个章节`)
      },
      onSummary: (summary) => {
        editAiSummary.value = summary
      },
      onDone: async (evt) => {
        generatingUnlimited.value = false
        if (evt.new_chapter_ids && evt.new_chapter_ids.length) {
          message.success(`生成完成，已自动创建 ${evt.new_chapter_ids.length} 个新章节`)
        } else {
          message.success('生成完成')
        }
        await store.selectChapter(store.currentChapter.id)
        await store.fetchChapters()
        syncEditBuffers()
      },
      onError: (msg) => {
        generatingUnlimited.value = false
        message.error(`无限生成失败: ${msg}`)
      },
    },
  )
}

async function handleSaveAiSummary() {
  if (!store.currentChapter) return
  try {
    await updateChapter(store.currentChapter.id, {
      ai_summary: editAiSummary.value,
    })
  } catch (e) {
    console.error('Failed to save AI summary:', e)
  }
}

async function handlePreviewPrompt() {
  if (!store.currentChapter) return
  previewLoading.value = true
  showPreviewModal.value = true
  try {
    const res = await previewPrompt(store.currentChapter.id)
    previewData.value = res.data
  } catch (e) {
    message.error(`获取预览失败: ${e.message}`)
    showPreviewModal.value = false
  } finally {
    previewLoading.value = false
  }
}

// Save
async function handleSave() {
  if (!store.currentChapter) return
  try {
    await updateChapter(store.currentChapter.id, {
      title: editTitle.value,
      summary: editSummary.value,
      content: editContent.value,
      worldview_level: editingWorldviewLevel.value,
    })
    message.success('已保存')
    await store.selectChapter(store.currentChapter.id)
  } catch (e) {
    message.error(`保存失败: ${e.response?.data?.detail || e.message}`)
  }
}

async function handleDownload() {
  if (!store.currentChapter) return
  const res = await downloadChapter(store.currentChapter.id)
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentChapter.title || 'chapter'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleDelete() {
  if (!store.currentChapter) return
  try {
    await deleteChapter(store.currentChapter.id)
    message.success('章节已删除')
    router.push('/outline')
  } catch (e) {
    message.error(`删除失败: ${e.response?.data?.detail || e.message}`)
  }
}

// Load data on mount
onMounted(async () => {
  await store.fetchVolumes()
  await store.fetchChapters()
  try {
    charactersLoading.value = true
    const res = await listCharacters({ limit: 500 })
    allCharacters.value = res.data
  } catch (e) {
    console.error('Failed to load characters:', e)
  } finally {
    charactersLoading.value = false
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.chapter-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Generating indicator bar */
.generating-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-accent) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  z-index: 10;
}

/* Top bar */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.editor-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-delete {
  --n-color: transparent !important;
  --n-color-hover: rgba(196, 90, 90, 0.08) !important;
  --n-text-color: var(--color-error) !important;
  --n-border: 1px solid var(--color-error) !important;
}

/* Editor layout */
.editor-layout {
  height: calc(100vh - 140px) !important;
  position: relative !important;
}

.left-sider {
  background: var(--color-bg-card);
}

.center-content {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.stream-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Tiptap editor */
:deep(.tiptap-wrapper) {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--color-bg-editor);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

:deep(.tiptap-content) {
  min-height: 400px;
  outline: none;
  font-family: var(--font-editor);
  font-size: 16px;
  line-height: 1.9;
  color: var(--color-text-primary);
}

:deep(.tiptap-content p) {
  margin: 0 0 0.6em;
}

:deep(.tiptap-content .ProseMirror) {
  min-height: 400px;
  padding: 0;
  outline: none;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: var(--color-text-muted);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Right sider */
.right-sider {
  background: var(--color-bg-card);
}

.generate-btn {
  margin: 8px 0;
  font-weight: 600;
  font-size: 15px;
}

.unlimited-btn {
  margin-bottom: 8px;
}

.meta-label {
  font-size: 12px;
}

.character-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: -8px;
}

.preview-btn {
  margin-top: 4px;
}

.preview-textarea :deep(textarea) {
  font-family: monospace;
}

.empty-editor {
  margin-top: 80px;
}
</style>
